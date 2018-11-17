"""Base implementation of objects relating to the processing pipeline"""

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
        multiprocessing.Process.__init__(self)
        self.input_queue = input_queue


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
        """Pushes results to output queue (if available)
        

        Parameters
        -----------
        data_type : int
            Identifier for data type (see :obj:`MeesageType` for types)
        data : any
            Results from processing (must be picklable)

        """

        for x in self.output_queue:
            x.put( ( data_type,data))

    
    def process(self,data_type=None,data=None):
        """Main processing function, override this do perform work

        To perform work within the pipeline, a class must override this function.
        General guidelines include, check for correct data type, and must return
        None for both if no output is given.

        Returns
        ---------
        A datatype identifier for the next in


        """

        return None,None

    def run(self):

        while True:

            if self.input_queue is not None:
                data_type,data = self.input_queue.get()

                output_type,result = self.process(data_type,data)

            else:
                output_type,result = self.process()

            if output_type is not None and result is not None:
                self.pushOutput(output_type,result)

            



