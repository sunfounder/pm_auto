class OLED_Page():

    def main(self, oled, data, config):
        pass

    def __call__(self, oled, data, config):
        self.main(oled, data, config)

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()

