from pymepix.core.log import Logger
from multiprocessing import Queue

class AcquisitionStage(Logger):
    """Defines a single acquisition stage"""

    def __init__(self,stage):
        Logger.__init__(self,'AcqStage-{}'.format(stage))
        self._stage_number = stage

        self._pipeline_objects = []
        self._pipeline_klass = None
        self._num_processes  = 0
        self._running = False
        self._input_queue = None
        self._output_queue = None

        self._args = []
        self._kwargs = {}
    @property
    def stage(self):
        return self._stage_number
    @stage.setter
    def stage(self,value):
        self._stage_number = value
    def configureStage(self,pipeline_klass,num_processes=1,*args,**kwargs):
        self.debug('Assigning stage to klass {} with {} processes'.format(pipeline_klass,num_processes))
        self._pipeline_klass = pipeline_klass
        
        self._num_processes = num_processes

        self._args =args
        self._kwargs = kwargs

    def build(self,input_queue=None,output_queue=None,file_writer=None):
        pass
        
    
    def start(self):
        pass

    
    def stop(self,force=False):
        self.info('Stopping stage {}'.format(self.stage))
        if self._input_queue is not None:
            #Put a none in and join all threads
            self._input_queue.put(None)

            for idx,p in enumerate(self._pipeline_objects):
                self.debug('Waiting for process {}'.format(idx))
                p.join()
            if self._input_queue.get() is not None:
                self.error('Queue should only contain None!!')
                raise Exception('Queue contains more data')
            self._input_queue.close()
        else:
            for p in self._pipeline_objects:
                p.terminate()
        self._pipeline_objects = []
        


class AcquisitionPipeline(Logger):
    """Class that manages all pipeline objects"""

    def __init__(self,name):
        Logger.__init__(name)

        self._stages = []
    

