from pm_auto.libs.utils import log_error
from pm_auto.libs.addon import Addon

class PiPower5Addon(Addon):
    LOOP_INTERVAL = 0.1 # 100ms

    REG_PWR_BTN_STATE= 154
    REG_WRITE_POWER_BTN_STATE = 12

    DEFAULT_CONFIG = {
        'shutdown_percentage': 10,
    }

    @log_error
    def __init__(self, *args, config=None, log=None, **kwargs):
        super().__init__(*args, **kwargs)
        name = self.device_info['name']
        from pipower5.pipower5_service import PiPower5Service
        self.service = PiPower5Service(config=config, device_name=name, log=log)
        if not self.service.is_ready():
            self.log.error('PiPower5 Init error')
            return
        
        self.service.set_on_config_changed(self.update_config)
        self.service.set_on_button_click(self.handle_button_click)
        self.service.set_on_button_double_click(self.handle_button_double_click)
        self.service.set_on_button_long_press(self.handle_button_long_press)
        self.service.set_on_button_long_press_released(self.handle_button_long_press_released)
        self.service.set_on_battery_critical_shutdown(self.handle_low_battery_shutdown)
        self.service.set_on_button_shutdown(self.handle_button_shutdown)
        self.service.set_on_battery_voltage_critical_shutdown(self.handle_low_voltage_shutdown)
        self.service.set_on_low_battery(self.handle_low_power)
        self.service.set_on_power_insufficient(self.handle_power_insufficient)
        self.service.set_on_battery_activated(self.handle_battery_activated)
        self.service.set_on_power_restore(self.handle_input_plugged_in)
        self.service.set_on_power_disconnected(self.handle_input_unplugged)
        self.service.set_on_data_changed(self.handle_data_changed)

        self._is_ready = True

    @log_error
    def test_smtp(self):
        return self.service.test_smtp()

    @log_error
    def handle_button_click(self, button_state):
        self.log.info(f'PiPower button click: {button_state}')
        self.event.publish('pipower5_button_click', button_state)

    @log_error
    def handle_button_double_click(self, button_state):
        self.log.info(f'PiPower button double click: {button_state}')
        self.event.publish('pipower5_button_double_click', button_state)

    @log_error
    def handle_button_long_press(self, button_state):
        self.log.info(f'PiPower button long press: {button_state}')
        self.event.publish('pipower5_button_long_press', 'button_long_press')

    @log_error
    def handle_button_long_press_released(self, button_state):
        self.log.info(f'PiPower button long press released: {button_state}')
        self.event.publish('pipower5_button_long_press_released', 'button_long_press_released')



    @log_error
    def handle_low_battery_shutdown(self, button_state):
        self.log.info(f'PiPower low battery shutdown: {button_state}')
        self.event.publish('pipower5_low_battery_shutdown', button_state)

    @log_error
    def handle_button_shutdown(self, button_state):
        self.log.info(f'PiPower button shutdown: {button_state}')
        self.event.publish('pipower5_button_shutdown', button_state)

    @log_error
    def handle_low_voltage_shutdown(self, button_state):
        self.log.info(f'PiPower low voltage shutdown: {button_state}')
        self.event.publish('pipower5_low_voltage_shutdown', button_state)

    @log_error
    def handle_low_power(self, button_state):
        self.log.warning(f'PiPower low power: {button_state}')
        self.event.publish('pipower5_low_power', button_state)

    @log_error
    def handle_power_insufficient(self, button_state):
        self.log.warning(f'PiPower power insufficient: {button_state}')
        self.event.publish('pipower5_power_insufficient', button_state)

    @log_error
    def handle_battery_activated(self, button_state):
        self.log.warning(f'PiPower battery activated: {button_state}')
        self.event.publish('pipower5_battery_activated', button_state)

    @log_error
    def handle_input_plugged_in(self, button_state):
        self.log.info(f'PiPower input plugged in: {button_state}')
        self.event.publish('pipower5_input_plugged_in', button_state)

    @log_error
    def handle_input_unplugged(self, button_state):
        self.log.info(f'PiPower input unplugged: {button_state}')
        self.event.publish('pipower5_input_unplugged', button_state)

    @log_error
    def handle_data_changed(self, data, delete_keys: list = []):
        self.event.publish('data_changed', data, delete_keys=delete_keys)

    @log_error
    def update_config(self, config, init=False):
        '''
        Update config.

        Args:
            config (Dict): New config dict.

        Returns:
            A dict of config patch to update the config file.
        '''
        patch = {}
        if not init:
            patch = self.service.update_config(config, init)
        return patch

    @log_error
    async def _main(self):
        await self.service.main()

    @log_error
    async def _start(self):
        self.service.running = True

    @log_error
    async def _stop(self):
        self.service.running = False
