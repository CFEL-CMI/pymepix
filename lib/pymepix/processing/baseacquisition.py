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
    def configureStage(self,pipeline_klass,*args,**kwargs):
        if 'num_processes' in kwargs:
            num_processes = kwargs.pop('num_processes')
         
        else:
            num_processes = 1

        self.debug('Assigning stage {} to klass {} with {} processes'.format(self.stage,pipeline_klass,num_processes))
        self._pipeline_klass = pipeline_klass
        
        self._num_processes = num_processes

        self._args =args
        self._kwargs = kwargs

    def build(self,input_queue=None,output_queue=None,file_writer=None):
        self._input_queue = input_queue
        self._output_queue = output_queue

        if self._output_queue is None:
            self.debug('I am creating the queue')
            self._output_queue = Queue()
        else:
            self.debug('Recieved the queue {}'.format(output_queue))
        self.debug('Building stage {} '.format(self._stage_number))
        for n in range(self._num_processes):
            
            p = self._pipeline_klass(*self._args,**self._kwargs,input_queue=self._input_queue,shared_output=self._output_queue)
            p.daemon=True
            self._pipeline_objects.append(p)
            if self._output_queue is None:
                self._output_queue = p.outputQueues()[-1]
    @property
    def outputQueue(self):
        return self._output_queue
        
    
    def start(self):
        for p in self._pipeline_objects:
            p.start()

    
    def stop(self,force=False):
        self.info('Stopping stage {}'.format(self.stage))
        if self._input_queue is not None:
            #Put a none in and join all threads
            self._input_queue.put(None)     
            for idx,p in enumerate(self._pipeline_objects):
                p.enable = False
                self.debug('Waiting for process {}'.format(idx))
                p.join()
                self.debug('Process stop complete')
            if self._input_queue.get() is not None:
                self.error('Queue should only contain None!!')
                raise Exception('Queue contains more data')
            self._input_queue.close()
        else:
            for p in self._pipeline_objects:
                p.enable=False
                self.info('Joining thread {}'.format(p))
                p.join()
        self.info('Stop complete')
        self._pipeline_objects = []
        


class AcquisitionPipeline(Logger):
    """Class that manages all pipeline objects"""

    def __init__(self,name,data_queue):
        Logger.__init__(self,name+' AcqPipeline')
        self.info('Initializing pipeline')
        self._stages = []

        self._data_queue = data_queue

        self._running = False

    def addStage(self,stage_number,pipeline_klass,*args,**kwargs):
        """Adds a stage to the pipeline"""
        stage = AcquisitionStage(stage_number)
        self.info('Adding stage {} with klass {}'.format(stage_number,pipeline_klass))
        stage.configureStage(pipeline_klass,*args,**kwargs)
        self._stages.append(stage)
        self._stages = sorted(self._stages,key=lambda x: x.stage)
    def start(self):

        #Sort them by stage number
        
        self.info('Starting acquisition')
        #Build them
        last_stage = None
        last_index = len(self._stages)-1
        self.debug('Last index is {}'.format(last_index))
        for idx,s in enumerate(self._stages):
            self.debug('Building stage {} {}'.format(idx,s.stage))
            if last_stage != None:
                queues = last_stage.outputQueue
                self.debug('Queues: {}'.format(queues))
                if idx != last_index:
                    s.build(input_queue=queues)
                else:
                    self.debug('This is the last queue so output is the last one')
                    s.build(input_queue=queues,output_queue=self._data_queue)
            else:
                if idx != last_index:
                    s.build()
                else:
                    self.info('First stage shares output')
                    s.build(output_queue=self._data_queue)
            last_stage = s
            self.debug('Last stage is {}'.format(s))
        
        for s in self._stages:
            s.enable = True
            s.start()
        self._running = True

                
    def stop(self):
        self.info('Stopping acquisition')
        self.debug(self._stages)
        if self._running is True:
            for s in self._stages:
                s.stop() 
        self._running = False           




def main():
    import logging
    import time
    from .udpsampler import UdpSampler
    from .packetprocessor import PacketProcessor
    from multiprocessing.sharedctypes import Value
    import threading
    #Create the logger
    logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    end_queue = Queue()

    acqpipline = AcquisitionPipeline('Test',end_queue)
    
    test_value = Value('I',0)

    acqpipline.addStage(0,UdpSampler,('192.168.1.1',8192),test_value,num_processes=1)
    acqpipline.addStage(2,PacketProcessor,num_processes=1)
    def get_queue_thread(queue):
        while True:
            value = queue.get()
            print(value)
            if value is None:
                break
    t = threading.Thread(target=get_queue_thread,args=(end_queue,))
    t.daemon = True
    t.start()

    acqpipline.start()
    time.sleep(10.0)
    acqpipline.stop()
    end_queue.put(None)


    t.join()
    print('Done')

if __name__=="__main__":
    main()