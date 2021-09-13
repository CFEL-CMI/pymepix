from multiprocessing import Value

class SharedProcessingParameter:

    def __init__(self, value) :
        super().__init__(Value(type(value), value))

    @property
    def value(self):
        return self._value.value

    @value.setter
    def value(self, value):
        self._value.value = value