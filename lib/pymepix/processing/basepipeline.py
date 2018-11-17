from pymepix.core.log import ProcessLogger
import multiprocessing
from multiprocessing import Queue

class BasePipelineObject(multiprocessing.Process,ProcessLogger):
    """Base class for integration in a processing pipeline
    
    Parameters
    ------------
    name: str
        Name used for logging 
    input_queue: :obj:`multiprocessing.Queue`, optional
        Data queue to perform work on (usually) from previous step in processing pipeline
    create_output: bool, optional
        Whether this creates its own output queue to pass data, ignored if  (Default: True)
    num_outputs: int,optional
        Used with create_output, number of output queues to create (Default: 1)
    shared_output: :obj:`multiprocessing.Queue`, optional
        Data queue to pass results into, useful when multiple processes can put data into the same
        queue (such as results from centroiding). Ignored if create_output is True (Default: None)

    """

    @classmethod
    def hasOutput(cls):
        """Defines whether this class can output results or not,
        e.g. Centroiding can output results but file writing classes do not"""
        return True


    def __init__(self,name,input_queue=None,create_output=True,num_outputs=1,shared_output=None):
        ProcessLogger.__init__(self,name)

        self._input_queue = input_queue


        self.output_queue =[]
        if create_output:
                
            for x in range(num_outputs):
                self.output_queue.append(Queue())
        elif shared_output is not None:
            self.output_queue.append(shared_output)
        
    
    @property
    def outputQueues(self):
        """Exposes the outputs so they may be connected to the next step
        
        Returns
        ---------
        :obj:`list` of :obj:`multiprocessing.Queue`
            All of the outputs
        
        """
        return self.output_queue

    
    def pushOutput(self,data_type,data):
        
        for x in self.output_queue:
            x.put( ( data_type,data))

    



