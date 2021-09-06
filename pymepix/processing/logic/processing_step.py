from abc import abstractmethod, ABC

from pymepix.core.log import Logger

class ProcessingStep(Logger, ABC):

    def __init__(self, name):
        super().__init__(name)

    def pre_process(self):
        pass

    def post_process(self):
        pass

    @abstractmethod
    def process(self, data):
        pass