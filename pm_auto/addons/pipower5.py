from pm_auto.libs.utils import log_error
from pm_auto.libs.addon import Addon
import asyncio

class PiPower5Addon(Addon):
    LOOP_INTERVAL = 1

    DEFAULT_CONFIG = {
        'shutdown_percentage': 10,
        'pipower5_buzzer_volume': 5,
        'pipower5_buzz_on': [],
        'pipower5_buzz_sequence': {},
        'send_email_on': [],
    }

    @log_error
    def __init__(self, *args, config=None, log=None, **kwargs):
        super().__init__(*args, **kwargs)

        from pipower5.pipower5 import PiPower5
        from pipower5.device import is_connected
        if not is_connected():
            self.log.error('PiPower5 not ready')
            self._is_ready = False
            return
        self.pipower5 = PiPower5()

        self.update_config(config, init=True)

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

    @log_error
    def is_ready(self):
        return self._is_ready

    @log_error
    def test_smtp(self):
        if self.email_sender:
            return self.email_sender.test_smtp()
        return False

    @log_error
    def play_pipower5_buzzer(self, event):
        seq = self._config.get('pipower5_buzz_sequence', {}).get(event, [])
        if seq:
            self.pipower5.buzz_sequence(seq)

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

        for key in ('send_email_on', 'send_email_to', 'smtp_server',
                     'smtp_port', 'smtp_email', 'smtp_password', 'smtp_security',
                     'pipower5_buzz_on', 'pipower5_buzz_sequence'):
            if key in cfg:
                patch[key] = cfg[key]

        if init:
            self._config = {**cfg, **patch}
        else:
            self._config = {**self._config, **patch}
        return patch

    @log_error
    def publish_data(self):
        data = self.pipower5.read_all()
        data['device_name'] = self.device_info['name']
        self.event.publish('data_changed', data)

    @log_error
    def _check_events(self):
        try:
            shutdown_req = self.pipower5.read_shutdown_request()
            button_state = self.pipower5.read_power_btn()
            is_plugged = self.pipower5.read_is_input_plugged_in()

            if shutdown_req != self._last_shutdown_request:
                self._last_shutdown_request = shutdown_req
                if shutdown_req == 1:
                    self.event.publish('pipower5_low_battery_shutdown', shutdown_req)
                elif shutdown_req == 2:
                    self.event.publish('pipower5_button_shutdown', shutdown_req)

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

            if is_plugged != self._was_input_plugged_in:
                self._was_input_plugged_in = is_plugged
                if is_plugged:
                    self.event.publish('pipower5_input_plugged_in', is_plugged)
                else:
                    self.event.publish('pipower5_input_unplugged', is_plugged)

        except Exception as e:
            self.log.debug(f'Event check failed: {e}')

    async def _main(self):
        self.log.info('PiPower5 addon main loop started')
        while self.running:
            try:
                self.publish_data()
            except Exception as e:
                self.log.error(f'PiPower5 publish error: {e}')
            try:
                self._check_events()
            except Exception as e:
                pass
            await asyncio.sleep(self.LOOP_INTERVAL)

    @log_error
    async def _start(self):
        cfg = getattr(self, '_config', {})
        try:
            self.pipower5.write_shutdown_percentage(
                cfg.get('shutdown_percentage', 10))
        except Exception as e:
            self.log.warning(f'write_shutdown_percentage failed: {e}')
        try:
            self.pipower5.set_buzzer_volume(
                cfg.get('pipower5_buzzer_volume', 5))
        except Exception as e:
            self.log.warning(f'set_buzzer_volume failed: {e}')

    @log_error
    async def _stop(self):
        pass
