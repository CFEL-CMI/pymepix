class ProcessingParameter:

    def __init__(self, value) :
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value