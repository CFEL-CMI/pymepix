"""Processors relating to centroiding"""

from .basepipeline import BasePipelineObject
import socket
from .datatypes import MessageType
import time
import numpy as np
from enum import IntEnum
from multiprocessing.sharedctypes import Value

class TOFCentroiding(BasePipelineObject):
    """Performs centroiding on EventData recieved from Packet processor

    """

    def __init__(self,skip_data=1,tot_filter=0,input_queue=None,create_output=True,num_outputs=1,shared_output=None):
        BasePipelineObject.__init__(self,TOFCentroiding.__name__,input_queue=input_queue,create_output=create_output,num_outputs=num_outputs,shared_output=shared_output)

        self._centroid_count = 0
        self._search_time = 0.0
        self._blob_time = 0.0
        self._skip_data = Value('I',skip_data)
        self._tot_threshold = Value('I',0)
        self._num_centroids = 0

    @property
    def centroidSkip(self):
        """Sets whether to process every nth pixel packet. 
        
        For example, setting it to 2 means every second packet is processed. 1 means all pixel packets are processed.

        """
        return self._skip_data.value
    
    @centroidSkip.setter
    def centroidSkip(self,value):
        value = max(1,value)
        self._skip_data.value = value

    @property
    def totThreshold(self):
        return self._tot_threshold.value
    
    @totThreshold.setter
    def totThreshold(self,value):
        value = max(0,value)
        self._tot_threshold.value = value


    def process(self,data_type,data):
        if data_type != MessageType.EventData:
            return None,None

        self._num_centroids +=1

        if self._num_centroids % 1000:
            self.debug('Search time: {}'.format(self._search_time))
            self.debug('Blob time: {} '.format(self._blob_time))

        if self._num_centroids % self.centroidSkip == 0:
            return None,None

        shot,x,y,tof,tot = data
        
        tot_filter = (tot > self.totThreshold)
        #Filter out pixels
        shot = shot[tot_filter]
        x = x[tot_filter]
        y = y[tot_filter]
        tof = tof[tot_filter]
        tot = tot[tot_filter]

        start = time.time()
        labels = self.find_cluster(shot,x,y,tof,tot,epsilon=2,min_samples=5)
        self._search_time += time.time() - start
        label_filter = labels!=0
        if labels is None:
            return None,None
        if labels[label_filter ].size ==0:
            return None,None
        else:
            start = time.time()
            props = self.cluster_properties(shot[label_filter ],x[label_filter ],y[label_filter ],tof[label_filter ],tot[label_filter ],labels[label_filter ])
            self._blob_time += time.time() - start
            return MessageType.CentroidData,props





    # def moments_com(self,X,Y,tot):

    #     total = tot.sum()
    #     x_bar = (X*tot).sum()/total
    #     y_bar = (Y*tot).sum()/total
    #     area = tot.size
    #     x_cm = X - x_bar
    #     y_cm = Y - y_bar
    #     coords = np.vstack([x_cm, y_cm])
        
    #     cov = np.cov(coords)
    #     try:

    #         evals, evecs = np.linalg.eig(cov)
    #     except:
    #         return None

    #     return x_bar,y_bar,area,total,evals,evecs.flatten()

    def find_cluster(self,shot,x,y,tof,tot,epsilon=3,min_samples=10,tof_epsilon=None):
        from sklearn.cluster import DBSCAN
        
        if shot.size == 0:
            return None
        #print(shot.size)
        tof_eps = 500*1E-9


        tof_scale = epsilon/tof_eps
        X = np.vstack((shot*epsilon*1000,x,y,tof*tof_scale)).transpose()
        dist= DBSCAN(eps=epsilon, min_samples=min_samples,metric='euclidean',n_jobs=1).fit(X)
        labels = dist.labels_ + 1
        return labels

    def cluster_properties(self,shot,x,y,tof,tot,labels):
        import scipy.ndimage as nd

        label_index = np.unique(labels)
        tot_max = np.array(nd.maximum_position(tot,labels=labels,index=label_index)).flatten()
        #tof_min = np.array(nd.minimum_position(tof,labels=labels,index=label_index)).flatten()
        #print(tot_max)
        tot_sum = nd.sum(tot,labels=labels,index=label_index)
        cluster_x = np.array(nd.sum(x*tot,labels=labels,index=label_index)/tot_sum).flatten()
        cluster_y = np.array(nd.sum(y*tot,labels=labels,index=label_index)/tot_sum).flatten()
        cluster_tof = np.array(nd.sum(tof*tot,labels=labels,index=label_index)/tot_sum).flatten()
        cluster_tot = tot[tot_max]
        #cluster_tof = tof[tot_max]
        cluster_shot = shot[tot_max]


        return cluster_shot,cluster_x,cluster_y,cluster_tof,cluster_tot

    # def cluster_properties(self,shot,x,y,tof,tot,labels):
    #     label_iter = np.unique(labels)
    #     total_objects = label_iter.size

    #     valid_objects = 0
    #     #Prepare our output
    #     cluster_shot = np.ndarray(shape=(total_objects,),dtype=np.int)
    #     cluster_x = np.ndarray(shape=(total_objects,),dtype=np.float64)
    #     cluster_y = np.ndarray(shape=(total_objects,),dtype=np.float64)
    #     cluster_eig = np.ndarray(shape=(total_objects,2,),dtype=np.float64)
    #     cluster_area = np.ndarray(shape=(total_objects,),dtype=np.float64)
    #     cluster_integral = np.ndarray(shape=(total_objects,),dtype=np.float64)
    #     cluster_tof = np.ndarray(shape=(total_objects,),dtype=np.float64)
        

    #     for idx in range(total_objects):


    #         obj_slice = (labels == label_iter[idx])
    #         obj_shot = shot[obj_slice]
    #         #print(obj_shot.size)
    #         obj_x = x[obj_slice]
    #         obj_y = y[obj_slice]

    #         obj_tot = tot[obj_slice]
    #         max_tot = np.argmax(obj_tot)

    #         moments = self.moments_com(obj_x,obj_y,obj_tot)
    #         if moments is None:
    #             continue    


    #         x_bar,y_bar,area,integral,evals,evecs = moments
    #         obj_tof = tof[obj_slice]
    #         max_tot = np.argmax(obj_tot)


    #         cluster_tof[valid_objects] = obj_tof[max_tot]
    #         cluster_x[valid_objects] = x_bar
    #         cluster_y[valid_objects] = y_bar
    #         cluster_area[valid_objects] = area
    #         cluster_integral[valid_objects] = integral
    #         cluster_eig[valid_objects]=evals
    #         cluster_shot[valid_objects] = obj_shot[0]
    #         valid_objects+=1
    #     return cluster_shot[:valid_objects],cluster_x[:valid_objects], \
    #             cluster_y[:valid_objects],cluster_area[:valid_objects], \
    #             cluster_integral[:valid_objects],cluster_eig[:valid_objects],cluster_eig[:valid_objects,:],cluster_tof[:valid_objects]