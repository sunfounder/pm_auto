from pm_auto.libs.utils import log_error
from pm_auto.libs.addon import Addon
import asyncio

class PiPower5Addon(Addon):
    LOOP_INTERVAL = 1
    BUTTON_POLL_INTERVAL = 0.1

    DEFAULT_CONFIG = {
        'shutdown_percentage': 10,
        'pipower5_buzzer_volume': 5,
        'pipower5_buzz_on': [],
        'pipower5_buzz_sequence': {},
    }

    EMAIL_KEYS = ('send_email_on', 'send_email_to', 'smtp_server',
                  'smtp_port', 'smtp_email', 'smtp_password', 'smtp_security')

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

        # Sync email config from pipower5 CLI to pironman5 config, then merge into defaults
        cli_email = self._sync_email_from_cli()
        if cli_email:
            config = {**(config or {}), **cli_email}

        self.update_config(config, init=True)

        self._apply_buzz_on()

        self._last_button_state = None
        self._last_shutdown_request = None
        self._was_input_plugged_in = self.pipower5.read_is_input_plugged_in()
        self._is_ready = True

    def _sync_email_from_cli(self):
        """On init, copy email settings from pipower5 CLI config.
        Returns merged dict for init, and publishes to pironman5 config."""
        import json, os
        cli_cfg = os.path.expanduser('~/.config/pipower5/config.json')
        if not os.path.exists(cli_cfg):
            return {}
        try:
            with open(cli_cfg, 'r') as f:
                cli = json.load(f).get('system', {})
        except Exception:
            return {}
        patch = {k: cli[k] for k in self.EMAIL_KEYS if cli.get(k)}
        if patch:
            self.event.publish('config_changed', patch)
            self.log.info(f'Synced email config from pipower5 CLI: {list(patch.keys())}')
        return patch

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
        # Merge CLI config as fallback for SMTP fields that may be empty in dashboard config
        import json, os
        cfg = dict(self._config)
        cli_cfg = os.path.expanduser('~/.config/pipower5/config.json')
        if os.path.exists(cli_cfg):
            try:
                with open(cli_cfg, 'r') as f:
                    cli = json.load(f).get('system', {})
                for k in ('send_email_to', 'smtp_server', 'smtp_email', 'smtp_password', 'smtp_port', 'smtp_security'):
                    if not cfg.get(k) and cli.get(k):
                        cfg[k] = cli[k]
            except Exception:
                pass
        return self.pipower5.test_smtp(cfg)

    def _apply_buzz_on(self):
        """Sync pipower5_buzz_on config list to kernel driver bitmask."""
        try:
            events = self._config.get("pipower5_buzz_on", [])
            self.pipower5.set_buzz_on(events)
        except Exception as e:
            self.log.debug(f"Failed to apply buzz_on: {e}")

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
            self.pipower5.write_shutdown_percentage(val)
            patch['shutdown_percentage'] = val

        if 'pipower5_buzzer_volume' in cfg:
            val = cfg['pipower5_buzzer_volume']
            self.pipower5.set_buzzer_volume(val)
            patch['pipower5_buzzer_volume'] = val

        for key in self.EMAIL_KEYS + ('pipower5_buzz_on', 'pipower5_buzz_sequence'):
            if key in cfg:
                patch[key] = cfg[key]

        if init:
            self._config = {**cfg, **patch}
        else:
            self._config = {**self._config, **patch}

        if 'pipower5_buzz_on' in cfg and not init:
            self._apply_buzz_on()

        # Reverse-sync email config to pipower5 CLI config
        email_patch = {k: cfg[k] for k in self.EMAIL_KEYS if k in cfg}
        if email_patch:
            try:
                self._write_cli_config(email_patch)
            except Exception as e:
                self.log.debug(f'CLI config sync skipped: {e}')

        return patch

    def _write_cli_config(self, patch):
        """Write email config changes to pipower5 CLI config for udev/CLI sync.
        Only writes non-empty values — empty strings/lists are treated as 'not set'."""
        import json, os
        if not patch:
            return
        cli_cfg = os.path.expanduser('~/.config/pipower5/config.json')
        os.makedirs(os.path.dirname(cli_cfg), exist_ok=True)
        current = {}
        if os.path.exists(cli_cfg):
            with open(cli_cfg, 'r') as f:
                current = json.load(f)
        if 'system' not in current:
            current['system'] = {}
        current['system'].update(patch)
        with open(cli_cfg, 'w') as f:
            json.dump(current, f, indent=4)

    @log_error
    def publish_data(self):
        data = self.pipower5.read_all()
        data['device_name'] = self.device_info['name']
        self.event.publish('data_changed', data)

    @log_error
    def _check_events(self):
        """Lightweight event bridge: read driver state, publish pm_auto events.
        Buzzer and email are handled by kernel driver + udev, not here."""
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
                elif shutdown_req == 3:
                    self.event.publish('pipower5_low_voltage_shutdown', shutdown_req)

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
