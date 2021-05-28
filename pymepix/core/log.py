# This file is part of Pymepix
#
# In all scientific work using Pymepix, please reference it as
#
# A. F. Al-Refaie, M. Johny, J. Correa, D. Pennicard, P. Svihra, A. Nomerotski, S. Trippel, and J. Küpper:
# "PymePix: a python library for SPIDR readout of Timepix3", J. Inst. 14, P10003 (2019)
# https://doi.org/10.1088/1748-0221/14/10/P10003
# https://arxiv.org/abs/1905.07999
#
# Pymepix is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not,
# see <https://www.gnu.org/licenses/>.


import logging
import threading
from multiprocessing import Queue

__all__ = ["Logger", "ProcessLogger"]


class PymepixLogger(object):
    """Base class for logging in pymepix

    This class wraps logging functionality and provides them to the derived classes
    providing info,debug,critical, error and warning methods

    Should not be used directly

    Parameters
    -----------
    name : str
        Name used for logging

    """

    _proc_log_queue = Queue()

    _init = False

    @classmethod
    def getLogQueue(cls):
        """Provides logging queue for multiprocessing logging

        Returns
        --------
        :obj:`multiprocessing.Queue`
            Queue where logs should go

        """
        return cls._proc_log_queue

    @classmethod
    def _logging_thread(cls):
        """This thread collects logs from Processes and writes them to stream"""

        thread_log = PymepixLogger.getLogger("log_thread")
        log_queue = cls.getLogQueue()

        thread_log.info("Starting Multiprocess logging")
        while True:
            name, log_level, message, args, kwargs = log_queue.get()
            _log = logging.getLogger(name)
            _log.log(log_level, message, *args, **kwargs)

    @classmethod
    def getRootLogger(cls):
        return cls._root_logger

    @classmethod
    def getLogger(cls, name):
        return logging.getLogger("pymepix.{}".format(name))

    @classmethod
    def reInit(cls):
        if cls._init is False:
            cls._root_logger = logging.getLogger("pymepix")

            cls._root_logger.info("Reinitializing PymepixLogger")
            cls._log_thread = threading.Thread(target=cls._logging_thread)
            cls._log_thread.daemon = True
            cls._log_thread.start()
        cls._init = True

    def __init__(self, name):
        self._log_name = "pymepix.{}".format(name)
        PymepixLogger.reInit()

    @property
    def logName(self):
        return self._log_name

    def info(self, message, *args, **kwargs):
        pass

    def warning(self, message, *args, **kwargs):
        pass

    def debug(self, message, *args, **kwargs):
        pass

    def error(self, message, *args, **kwargs):
        pass

    def critical(self, message, *args, **kwargs):
        pass


class Logger(PymepixLogger):
    """Standard logging using logger library

    Parameters
    -----------
    name : str
        Name used for logging

    """

    def __init__(self, name):
        PymepixLogger.__init__(self, name)
        self._logger = logging.getLogger(self.logName)

    def info(self, message, *args, **kwargs):
        """ See :class:`logging.Logger` """
        self._logger.info(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        """ See :class:`logging.Logger` """
        self._logger.warning(message, *args, **kwargs)

    def debug(self, message, *args, **kwargs):
        """ See :class:`logging.Logger` """
        self._logger.debug(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        """ See :class:`logging.Logger` """
        self._logger.error(message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        """ See :class:`logging.Logger` """
        self._logger.critical(message, *args, **kwargs)


class ProcessLogger(PymepixLogger):
    """Sends logs to queue to be processed by logging thread

    Parameters
    -----------
    name : str
        Name used for logging

    """

    def __init__(self, name):
        PymepixLogger.__init__(self, name)
        self._logger = logging.getLogger(self.logName)
        self._log_queue = PymepixLogger.getLogQueue()

    def info(self, message, *args, **kwargs):
        """ See :class:`logging.Logger` """
        self._log_queue.put((self._log_name, logging.INFO, message, args, kwargs))

    def warning(self, message, *args, **kwargs):
        """ See :class:`logging.Logger` """
        self._log_queue.put((self._log_name, logging.WARNING, message, args, kwargs))

    def debug(self, message, *args, **kwargs):
        """ See :class:`logging.Logger` """
        self._log_queue.put((self._log_name, logging.DEBUG, message, args, kwargs))

    def error(self, message, *args, **kwargs):
        """ See :class:`logging.Logger` """
        self._log_queue.put((self._log_name, logging.ERROR, message, args, kwargs))

    def critical(self, message, *args, **kwargs):
        """ See :class:`logging.Logger` """
        self._log_queue.put((self._log_name, logging.CRITICAL, message, args, kwargs))


def main():
    pass


if __name__ == "__main__":
    main()

# Local Variables:
# fill-column: 100
# truncate-lines: t
# End:
