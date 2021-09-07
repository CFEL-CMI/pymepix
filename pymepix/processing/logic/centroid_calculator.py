import multiprocessing as mp

import numpy as np
import scipy.ndimage as nd
from sklearn.cluster import DBSCAN

from pymepix.processing.logic.processing_step import ProcessingStep

class CentroidCalculator(ProcessingStep):

    def __init__(self, tot_threshold=0, epsilon=2, min_samples=5, chunk_size_limit=6_500, 
        cent_timewalk_lut=None):

        super().__init__("CentroidCalculator")
        self._epsilon = epsilon
        self._min_samples = min_samples
        self._tof_scale = 1e7
        self._tot_threshold = tot_threshold
        self._cent_timewalk_lut = cent_timewalk_lut
        self._chunk_size_limit = chunk_size_limit

        self.removed_by_dbscan = 0

    def process(self, data):
        if data is not None:
            shot, x, y, tof, tot = data

            chunks = self.__divide_into_chunks(shot, x, y, tof, tot)
            # chunks = [data]
            centroids_in_chunks = self.perform_centroiding(chunks)

            return self.__centroid_chunks_to_centroids(centroids_in_chunks)
        else:
            return None

    def debug_condition(self, chunks, size):
        sum = 0
        found_triggers = []
        for chunk in chunks:
            sum += chunk[0].shape[0]
            found_triggers += np.unique(chunk[0]).tolist()
        return sum != size or np.all(np.unique(found_triggers, return_counts=True)[1] > 1)

    def __divide_into_chunks(self, shot, x, y, tof, tot):
        # Reordering the voxels can have an impact on the clusterings result. See CentroidCalculator.perform_clustering string doc for further information!
        order = shot.argsort()
        shot, x, y, tof, tot = shot[order], x[order], y[order], tof[order], tot[order]
        split_indices = self.__calc_trig_chunks_split_indices(shot)
        if len(split_indices) > 0:

            shot, x, y, tof, tot = [np.split(arr, split_indices) for arr in [shot, x, y, tof, tot]]

            chunks = []
            for i in range(len(shot)):
                chunks.append((shot[i], x[i], y[i], tof[i], tot[i]))
            return chunks
        else:
            return [(shot, x, y , tof, tot)]
        
    def __calc_trig_chunks_split_indices(self, shot):
        _, unique_trig_nr_indices, unique_trig_nr_counts = np.unique(shot, return_index=True, return_counts=True)
        
        trigger_chunks = []
        trigger_chunk_voxel_counter = 0
        for index, unique_trig_nr_index in enumerate(unique_trig_nr_indices):
            if trigger_chunk_voxel_counter < self._chunk_size_limit:
                trigger_chunk_voxel_counter += unique_trig_nr_counts[index]
            else:
                trigger_chunks.append(unique_trig_nr_index)
                trigger_chunk_voxel_counter = unique_trig_nr_counts[index]

        return trigger_chunks

    def __centroid_chunks_to_centroids(self, chunks):
        centroids = [[] for i in range(7)]
        for chunk in list(chunks):
            if chunk != None:
                for index, coordinate in enumerate(chunk):
                    centroids[index].append(coordinate)

        return [np.concatenate(coordinate) for coordinate in centroids]

    def perform_centroiding(self, chunks):
        return map(self.calculate_centroids, chunks)

    def calculate_centroids(self, chunk):
        shot, x, y, tof, tot = chunk

        tot_filter = tot > self._tot_threshold
        # Filter out pixels
        shot = shot[tot_filter]
        x = x[tot_filter]
        y = y[tot_filter]
        tof = tof[tot_filter]
        tot = tot[tot_filter]

        labels = self.perform_clustering(shot, x, y, tof)

        label_filter = labels != 0

        self.removed_by_dbscan += np.where(label_filter == False)[0].shape[0]

        if labels is not None and labels[label_filter].size > 0:
            return self.calculate_centroids_properties(
                shot[label_filter],
                x[label_filter],
                y[label_filter],
                tof[label_filter],
                tot[label_filter],
                labels[label_filter],
            )

        return None
        
    def perform_clustering(self, shot, x, y, tof):
        """ The clustering with DBSCAN, which is performed in this function is dependent on the order of the data in rare cases. Therefore reordering in any means can
            lead to slightly changed results, which should not be an issue.

            Martin Ester, Hans-Peter Kriegel, Jiirg Sander, Xiaowei Xu: A Density Based Algorith for Discovering Clusters [p. 229-230] (https://www.aaai.org/Papers/KDD/1996/KDD96-037.pdf)
            A more specific explaination can be found here: https://stats.stackexchange.com/questions/306829/why-is-dbscan-deterministic"""
        if x.size >= 0:
            X = np.column_stack((shot * self._epsilon * 1_000, x, y, tof * self._tof_scale))

            dist = DBSCAN(
                eps=self._epsilon, min_samples=self._min_samples, metric="euclidean", n_jobs=1
            ).fit(X)

            return dist.labels_ + 1
        
        return None

    def calculate_centroids_properties(self, shot, x, y, tof, tot, labels):
        """
        Calculates the properties of the centroids from labeled data points.

        ATTENTION! The order of the points can have an impact on the result due to errors in 
        the floating point arithmetics. 

        Very simple example: 
        arr = np.random.random(100)
        arr.sum() - np.sort(arr).sum()
        This example shows that there is a very small difference between the two sums. The inaccuracy of 
        floating point arithmetics can depend on the order of the values. Strongly simplified (3.2 + 3.4) + 2.7 
        and 3.2 + (3.4 + 2.7) can be unequal for floating point numbers. 

        Therefore there is no guarantee for strictly equal results. Even after sorting. The error we observed
        can be about 10^-22 nano seconds. 

        Currently this is issue exists only for the TOF-column as the other columns are integer-based values.
        """
        label_index, cluster_size = np.unique(labels, return_counts=True)
        tot_max = np.array(
            nd.maximum_position(tot, labels=labels, index=label_index)
        ).flatten()

        tot_sum = nd.sum(tot, labels=labels, index=label_index)
        tot_mean = nd.mean(tot, labels=labels, index=label_index)
        cluster_x = np.array(
            nd.sum(x * tot, labels=labels, index=label_index) / tot_sum
        ).flatten()
        cluster_y = np.array(
            nd.sum(y * tot, labels=labels, index=label_index) / tot_sum
        ).flatten()
        cluster_tof = np.array(
            nd.sum(tof * tot, labels=labels, index=label_index) / tot_sum
        ).flatten()
        cluster_totMax = tot[tot_max]
        cluster_totAvg = tot_mean
        cluster_shot = shot[tot_max]

        if self._cent_timewalk_lut is not None:
            # cluster_tof -= self._timewalk_lut[(cluster_tot / 25).astype(np.int) - 1]
            # cluster_tof *= 1e6
            cluster_tof -= self._cent_timewalk_lut[np.int(cluster_totMax // 25) - 1] * 1e3
            # TODO: should totAvg not also be timewalk corrected?!
            # cluster_tof *= 1e-6

        return cluster_shot, cluster_x, cluster_y, cluster_tof, cluster_totAvg, cluster_totMax, cluster_size


class CentroidCalculatorPooled(CentroidCalculator):

    def __init__(self, number_of_processes=4, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._number_of_processes = number_of_processes
        
    def perform_centroiding(self, chunks):
        return self._pool.map(self.calculate_centroids, chunks)
        
    def pre_process(self):
        self._pool = mp.Pool(self._number_of_processes)
        return super().pre_process()

    def post_process(self):
        self._pool.close()
        self._pool.join()
        return super().post_process()

    def __getstate__(self):
        self_dict = self.__dict__.copy()
        del self_dict['_pool']
        return self_dict