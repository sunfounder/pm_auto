from pm_auto.libs.utils import log_error
from pm_auto.libs.addon import Addon
import asyncio

class PiPower5Addon(Addon):
    LOOP_INTERVAL = 1
    BUTTON_POLL_INTERVAL = 0.1

    DEFAULT_CONFIG = {
        'shutdown_percentage': 10,
        'pipower5_buzzer_volume': 50,
        'pipower5_buzz_on': [],
        'pipower5_buzz_sequence': {},
        'send_email_on': [],
    }

    BUZZ_EVENT_BIT = {
        "battery_activated":                 0x01,
        "low_battery":                       0x02,
        "power_disconnected":                0x04,
        "power_restored":                    0x08,
        "power_insufficient":                0x10,
        "battery_critical_shutdown":         0x20,
        "battery_voltage_critical_shutdown": 0x40,
    }

    @log_error
    def __init__(self, *args, config=None, log=None, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            from pipower5.pipower5 import PiPower5
            from pipower5.device import is_connected
        except ImportError as e:
            self.log.error(f'PiPower5 package not installed: {e}')
            self._is_ready = False
            return

        try:
            if not is_connected():
                self.log.error('PiPower5 not ready')
                self._is_ready = False
                return
            self.pipower5 = PiPower5()
        except Exception as e:
            self.log.error(f'PiPower5 init failed: {e}')
            self._is_ready = False
            return

        self.update_config(config, init=True)

        # Write non-I2C settings to driver on startup
        self._apply_buzz_on()

        try:
            from pipower5.email_sender import EmailSender
            self.email_sender = EmailSender(config, log=self.log)
        except Exception as e:
            self.log.warning(f'Email sender init failed: {e}')
            self.email_sender = None

        self._last_button_state = None
        self._last_shutdown_request = None
        self._was_input_plugged_in = self.pipower5.read_is_input_plugged_in()
        self._is_ready = True

        # Sync hardware→config: if CLI changed hardware values, reflect them
        self._sync_hardware_to_config()

    @log_error
    def is_ready(self):
        return self._is_ready

    @log_error
    def _sync_hardware_to_config(self):
        """Read current hardware values and publish any differences as config patches.
        This handles the case where CLI (pipower5) changed values directly in hardware."""
        try:
            hw_shutdown = self.pipower5.read_shutdown_percentage()
            cfg_shutdown = self._config.get('shutdown_percentage')
            if cfg_shutdown is not None and hw_shutdown != cfg_shutdown:
                self.log.info(f'Hardware shutdown_pct ({hw_shutdown}) differs from config ({cfg_shutdown}), syncing')
                self._config['shutdown_percentage'] = hw_shutdown
                self.event.publish('config_changed', {'shutdown_percentage': hw_shutdown})

            hw_buzzer_vol = self.pipower5.read_buzzer_volume()
            cfg_buzzer_vol = self._config.get('pipower5_buzzer_volume')
            if cfg_buzzer_vol is not None and hw_buzzer_vol != cfg_buzzer_vol:
                self._config['pipower5_buzzer_volume'] = hw_buzzer_vol
                self.event.publish('config_changed', {'pipower5_buzzer_volume': hw_buzzer_vol})
        except Exception as e:
            self.log.debug(f'Hardware→config sync skipped: {e}')

    @log_error
    def test_smtp(self):
        if not self.email_sender:
            return False, "Email sender not initialized"
        if not self.email_sender.is_ready():
            return False, "SMTP settings incomplete"
        try:
            self.email_sender.connect()
            return True, ""
        except Exception as e:
            return False, str(e)

    def _apply_buzz_on(self):
        """Write pipower5_buzz_on config (list of event names) to kernel sysfs as bitmask."""
        try:
            buzz_on = self._config.get("pipower5_buzz_on", [])
            mask = 0
            for event in buzz_on:
                mask |= self.BUZZ_EVENT_BIT.get(event, 0)
            self.pipower5._write_sysfs("buzz_on", f"0x{mask:02X}")
        except Exception as e:
            self.log.debug(f"Failed to apply buzz_on to driver: {e}")

    def play_pipower5_buzzer(self, event):
        self.pipower5.buzz_sequence(event)

    @log_error
    def power_failure_simulation(self, test_time=60):
        return self.pipower5.power_failure_simulation(test_time)

    @log_error
    def update_config(self, config, init=False):
        patch = {}
        if config is None:
            config = {}
        cfg = config

        if 'shutdown_percentage' in cfg:
            val = cfg['shutdown_percentage']
            if not init:
                self.pipower5.write_shutdown_percentage(val)
            patch['shutdown_percentage'] = val

        if 'pipower5_buzzer_volume' in cfg:
            val = cfg['pipower5_buzzer_volume']
            if not init:
                self.pipower5.set_buzzer_volume(val)
            patch['pipower5_buzzer_volume'] = val

        smtp_changed = any(k in cfg for k in (
            'smtp_server', 'smtp_port', 'smtp_email',
            'smtp_password', 'smtp_security'))

        for key in ('send_email_on', 'send_email_to', 'smtp_server',
                     'smtp_port', 'smtp_email', 'smtp_password', 'smtp_security',
                     'pipower5_buzz_on', 'pipower5_buzz_sequence'):
            if key in cfg:
                patch[key] = cfg[key]

        if init:
            self._config = {**cfg, **patch}
        else:
            self._config = {**self._config, **patch}

        if smtp_changed and not init:
            try:
                from pipower5.email_sender import EmailSender
                self.email_sender = EmailSender(self._config, log=self.log)
            except Exception as e:
                self.log.warning(f'Failed to recreate EmailSender: {e}')

        if 'pipower5_buzz_on' in cfg and not init:
            self._apply_buzz_on()

        return patch

    @log_error
    def publish_data(self):
        data = self.pipower5.read_all()
        data['device_name'] = self.device_info['name']
        self.event.publish('data_changed', data)

    def _buzz_if_enabled(self, event_name):
        buzz_on = self._config.get('pipower5_buzz_on', [])
        if event_name in buzz_on:
            self.play_pipower5_buzzer(event_name)

    def _send_email_if_enabled(self, event_name, data=None):
        """Send email notification if event_name is in send_email_on config."""
        send_email_on = self._config.get('send_email_on', [])
        if event_name not in send_email_on:
            return
        if not self.email_sender:
            self.log.warning(f'Cannot send email for {event_name}: EmailSender not initialized')
            return
        try:
            if data is None:
                data = {}
            # Ensure all template fields are present
            data.setdefault('device_name', self.device_info.get('name', 'PiPower5'))
            data.setdefault('battery_percentage', self.pipower5.read_battery_percentage())
            data.setdefault('battery_voltage', self.pipower5.read_battery_voltage())
            data.setdefault('shutdown_percentage', self._config.get('shutdown_percentage', 10))
            data.setdefault('battery_current_output', self.pipower5.read_battery_current())
            data.setdefault('estimated_time', 'N/A')
            data.setdefault('input_status', 'Unknown')
            data.setdefault('charging_status', 'Unknown')
            import time
            data.setdefault('switch_time', time.strftime('%Y-%m-%d %H:%M:%S'))

            result = self.email_sender.send_preset_email(event_name, data)
            if result is True:
                self.log.info(f'Email sent for event: {event_name}')
            else:
                self.log.error(f'Email failed for {event_name}: {result}')
        except Exception as e:
            self.log.error(f'Email exception for {event_name}: {e}')

    @log_error
    def _check_events(self):
        try:
            shutdown_req = self.pipower5.read_shutdown_request()
            button_state = self.pipower5.read_power_btn()
            is_plugged = self.pipower5.read_is_input_plugged_in()
            bat_pct = self.pipower5.read_battery_percentage()

            if shutdown_req != self._last_shutdown_request:
                self._last_shutdown_request = shutdown_req
                if shutdown_req == 1:
                    self.event.publish('pipower5_low_battery_shutdown', shutdown_req)
                    self._buzz_if_enabled('low_battery')
                    self._send_email_if_enabled('low_battery',
                        {'battery_percentage': bat_pct, 'device_name': self.device_info.get('name', 'PiPower5')})
                elif shutdown_req == 2:
                    self.event.publish('pipower5_button_shutdown', shutdown_req)
                    self._buzz_if_enabled('battery_critical_shutdown')
                elif shutdown_req == 3:
                    self.event.publish('pipower5_low_voltage_shutdown', shutdown_req)
                    self._buzz_if_enabled('battery_voltage_critical_shutdown')

            if button_state != self._last_button_state:
                self._last_button_state = button_state
                if button_state == 1:
                    self.event.publish('pipower5_button_click', button_state)
                elif button_state == 2:
                    self.event.publish('pipower5_button_double_click', button_state)
                elif button_state == 3:
                    self.event.publish('pipower5_button_long_press', button_state)
                elif button_state == 4:
                    self.event.publish('pipower5_button_long_press_released', button_state)
                # States 5 (LONG_PRESS_5S) and 6: MCU cuts power directly,
                # Python won't reliably see these. OLED is cleared by the
                # 2-second auto-clear timer in OLEDAddon._main().

            if is_plugged != self._was_input_plugged_in:
                self._was_input_plugged_in = is_plugged
                if is_plugged:
                    self.event.publish('pipower5_input_plugged_in', is_plugged)
                    self._buzz_if_enabled('power_restored')
                    self._send_email_if_enabled('power_restored',
                        {'battery_percentage': bat_pct, 'device_name': self.device_info.get('name', 'PiPower5')})
                else:
                    self.event.publish('pipower5_input_unplugged', is_plugged)
                    self._buzz_if_enabled('power_disconnected')
                    self._send_email_if_enabled('power_disconnected',
                        {'battery_percentage': bat_pct, 'device_name': self.device_info.get('name', 'PiPower5')})

        except Exception as e:
            self.log.debug(f'Event check failed: {e}')

    async def _main(self):
        self.log.info('PiPower5 addon main loop started')
        import time as _time
        last_data = 0
        while self.running:
            now = _time.monotonic()
            try:
                self._check_events()
            except Exception as e:
                pass
            if now - last_data >= self.LOOP_INTERVAL:
                try:
                    self.publish_data()
                except Exception as e:
                    self.log.error(f'PiPower5 publish error: {e}')
                last_data = now
            await asyncio.sleep(self.BUTTON_POLL_INTERVAL)

    @log_error
    async def _start(self):
        pass

    @log_error
    async def _stop(self):
        pass
