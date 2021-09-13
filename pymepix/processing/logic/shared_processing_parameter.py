from multiprocessing import Value

from pymepix.processing.logic.processing_parameter import ProcessingParameter

class UnknownParameterTypeException(Exception):
    pass

class SharedProcessingParameter(ProcessingParameter):

    def __init__(self, value) :
        if isinstance(value, int):
            super().__init__(Value('i', value, lock=False))
        elif isinstance(value, float):
            super().__init__(Value('d', value, lock=False))
        else:
            raise UnknownParameterTypeException()

    @property
    def value(self):
        return self._value.value

    @value.setter
    def value(self, value):
        self._value.value = value