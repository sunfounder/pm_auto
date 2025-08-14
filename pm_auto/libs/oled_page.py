class OLEDPage():

    def main(self, oled, *args, **kwargs):
        pass

    def __call__(self, oled, *args, **kwargs):
        self.main(oled, *args, **kwargs)

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()

