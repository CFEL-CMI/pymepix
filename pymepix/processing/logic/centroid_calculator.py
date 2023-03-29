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
import multiprocessing as mp
from multiprocessing.pool import Pool
from threading import current_thread

import numpy as np
import scipy.ndimage as nd
from sklearn.cluster import DBSCAN

from pymepix.processing.logic.processing_step import ProcessingStep
from pymepix.clustering.cluster_stream import ClusterStream


class CentroidCalculator(ProcessingStep):
    """
    Class responsible for calculating centroids in timepix data. This includes the calculation
    of the clusters first and the centroids. The data processed is not the direct raw data but the
    data that has been processed by the PacketProcessor before (x, y, tof, tot).

    Methods
    -------
    process(data):
        Process data and return the result. To use this class only this method should be used! Use the other methods only for testing or
        if you are sure about what you are doing
    """

    def __init__(
        self,
        cent_timewalk_lut=None,
        number_of_processes=4,
        clustering_args={},
        dbscan_clustering = True,
        *args,
        **kwargs,
    ):
        """
        Constructor for  the CentroidCalculator.

        Parameters
        ----------
        tot_threshold : int
            Threshold applied before calculating the clusters. A higher threshold can lead to more clusters found in some cases.
        epsilon : float
            see DBSCAN
        min_samples : int
            see DBSCAN
        triggers_processed : int
            every triggers_processed trigger is used for the calculation. Increasing the value can speed up online processing if the
            data rate is too high to process all triggers directly.
        chunk_size_limit : int
            Maximum size of the chunks to increase the performance of DBSCAN. Higher and Lower values might increase the runtime.
        cent_timewalk_lut
            Data for correction of the time-walk
        parameter_wrapper_classe : ProcessingParameter
            Class used to wrap the processing parameters to make them changable while processing is running (useful for online optimization)
        """

        super().__init__("CentroidCalculator", *args, **kwargs)

        self._epsilon = self.parameter_wrapper_class(clustering_args.pop('epsilon', 2.0))
        self._min_samples = self.parameter_wrapper_class(clustering_args.pop('min_samples', 3))
        self._tot_threshold = self.parameter_wrapper_class(clustering_args.pop('tot_threshold', 0))
        self._triggers_processed = self.parameter_wrapper_class(clustering_args.pop('triggers_processed', 1))

        self._cs_sensor_size = self.parameter_wrapper_class(clustering_args.pop('cs_sensor_size', 256))
        self._cs_min_cluster_size = self.parameter_wrapper_class(clustering_args.pop('cs_min_cluster_size', 3))
        self._cs_max_dist_tof = self.parameter_wrapper_class(clustering_args.pop('cs_max_dist_tof', 5e-8))
        self._cs_tot_offset = self.parameter_wrapper_class(clustering_args.pop('cs_tot_offset', 0.5))

        self._chunk_size_limit = clustering_args.pop('chunk_size_limit',6_500)

        self._tof_scale = 1.7e7
        self._cent_timewalk_lut = cent_timewalk_lut

        self._dbscan_clustering = self.parameter_wrapper_class(int(dbscan_clustering))

        self.number_of_processes = number_of_processes


    @property
    def epsilon(self):
        return self._epsilon.value

    @epsilon.setter
    def epsilon(self, epsilon):
        self._epsilon.value = epsilon

    @property
    def min_samples(self):
        return self._min_samples.value

    @min_samples.setter
    def min_samples(self, min_samples):
        self._min_samples.value = min_samples

    @property
    def tot_threshold(self):
        """Determines which time over threshold values to filter before centroiding

        This is useful in reducing the computational time in centroiding and can filter out
        noise. """
        return self._tot_threshold.value

    @tot_threshold.setter
    def tot_threshold(self, tot_threshold):
        self._tot_threshold.value = tot_threshold

    @property
    def triggers_processed(self):
        """ Setting for the number of packets skipped during processing. Every packet_skip packet is processed.
        This means for a value of 1 every packet is processed. For 2 only every 2nd packet is processed. """
        return self._triggers_processed.value

    @triggers_processed.setter
    def triggers_processed(self, triggers_processed):
        self._triggers_processed.value = triggers_processed

    @property
    def cs_sensor_size(self):
        """ Setting for the number of packets skipped during processing. Every packet_skip packet is processed.
        This means for a value of 1 every packet is processed. For 2 only every 2nd packet is processed. """
        return self._cs_sensor_size.value
    @cs_sensor_size.setter
    def cs_sensor_size(self, cs_sensor_size):
        self._cs_sensor_size.value = cs_sensor_size

    @property
    def cs_min_cluster_size(self):
        """ Setting the minimal cluster size in Cluster Streaming algorithm"""
        return self._cs_min_cluster_size.value
    @cs_min_cluster_size.setter
    def cs_min_cluster_size(self, cs_min_cluster_size):
        self._cs_min_cluster_size.value = cs_min_cluster_size

    @property
    def cs_max_dist_tof(self):
        """Setting the maximal ToF distance between the voxels belonging to the cluster in Cluster Streaming algorithm"""
        return self._cs_max_dist_tof.value
    @cs_max_dist_tof.setter
    def cs_max_dist_tof(self, cs_max_dist_tof):
        self._cs_max_dist_tof.value = cs_max_dist_tof

    @property
    def cs_tot_offset(self):
        """ Setting the ToT ratio factor of the voxel to the ToT of previous voxel in Cluster Streaming algorithm.
        Zero factor means ToT of prev. voxel should be larger. 0.5 factor means ToT of prev voxel could be high than
        the half of the considered voxel"""
        return self._cs_tot_offset.value
    @cs_tot_offset.setter
    def cs_tot_offset(self, cs_tot_offset):
        self._cs_tot_offset.value = cs_tot_offset

    @property
    def dbscan_clustering(self):
        return bool(self._dbscan_clustering.value)

    @dbscan_clustering.setter
    def dbscan_clustering(self, dbscan_clustering):
        self._dbscan_clustering.value = int(dbscan_clustering)
    def process(self, data):

        if data is None:
            return None

        if self.dbscan_clustering:
            shot, x, y, tof, tot = self.__skip_triggers(*data)
            chunks = self.__divide_into_chunks(shot, x, y, tof, tot)
            centroids_in_chunks = self.perform_centroiding_dbscan(chunks)
        else:
            chunks = self.cluster_stream_preprocess(*data)
            centroids_in_chunks = self.perform_centroiding_cluster_stream(chunks)

        return self.centroid_chunks_to_centroids(centroids_in_chunks)

    def __skip_triggers(self, shot, x, y, tof, tot):
        unique_shots = np.unique(shot)
        selected_shots = unique_shots[:: self.triggers_processed]
        mask = np.isin(shot, selected_shots)
        return shot[mask], x[mask], y[mask], tof[mask], tot[mask]

    def cluster_stream_preprocess(self, shot, x, y, tof, tot):

        order = shot.argsort()
        shot, x, y, tof, tot = shot[order], x[order], y[order], tof[order], tot[order]
        _, unique_trig_nr_indices, unique_trig_nr_counts = np.unique(
            shot, return_index=True, return_counts=True
        )

        shot, x, y, tof, tot = [
            np.split(arr, unique_trig_nr_indices[1:]) for arr in [shot, x, y, tof, tot]
        ]

        for i, sh in enumerate(shot):
            sorting_indexes = np.lexsort((-tot[i], tof[i]))
            x[i] = x[i][sorting_indexes]
            y[i] = y[i][sorting_indexes]
            tof[i] = tof[i][sorting_indexes]
            tot[i] = tot[i][sorting_indexes]

        chunks = []
        for i in range(len(shot)):
             chunks.append(np.vstack((shot[i], x[i], y[i], tof[i], tot[i])))
        return chunks


    def __divide_into_chunks(self, shot, x, y, tof, tot):
        """ Reordering the voxels can have an impact on the clusterings result. See CentroidCalculator.perform_clustering
        string doc for further information! """
        order = shot.argsort()
        shot, x, y, tof, tot = shot[order], x[order], y[order], tof[order], tot[order]
        split_indices = self.__calc_trig_chunks_split_indices(shot)
        if len(split_indices) > 0:

            shot, x, y, tof, tot = [
                np.split(arr, split_indices) for arr in [shot, x, y, tof, tot]
            ]

            chunks = []
            for i in range(len(shot)):
                chunks.append((shot[i], x[i], y[i], tof[i], tot[i]))
            return chunks
        else:
            return [(shot, x, y, tof, tot)]

    def __calc_trig_chunks_split_indices(self, shot):
        _, unique_trig_nr_indices, unique_trig_nr_counts = np.unique(
            shot, return_index=True, return_counts=True
        )

        trigger_chunks = []
        trigger_chunk_voxel_counter = 0
        for index, unique_trig_nr_index in enumerate(unique_trig_nr_indices):
            if trigger_chunk_voxel_counter < self._chunk_size_limit:
                trigger_chunk_voxel_counter += unique_trig_nr_counts[index]
            else:
                trigger_chunks.append(unique_trig_nr_index)
                trigger_chunk_voxel_counter = unique_trig_nr_counts[index]

        return trigger_chunks

    def centroid_chunks_to_centroids(self, chunks):
        # range(7) because the centroids have 7 dimensions: shot, x, y, tof, tot avg, tot max, cluster size
        """centroids = [[] for i in range(7)]
        for chunk in list(chunks):
            if chunk != None:
                for index, coordinate in enumerate(chunk):
                    centroids[index].append(coordinate)"""
        joined_chunks = list(filter(None, chunks))
        if joined_chunks:
            return np.concatenate(joined_chunks, axis=1)
        else:
            return None

    def perform_centroiding_dbscan(self, chunks):
#        with Pool(self.number_of_processes) as p:
#            return p.map(self.calculate_centroids_dbscan, chunks)
        return map(self.calculate_centroids_dbscan, chunks)

    def perform_centroiding_cluster_stream(self, chunks):
        self.cstream = ClusterStream(self.cs_sensor_size, self.cs_max_dist_tof,\
                                     self.cs_min_cluster_size, self.cs_tot_offset)

#        with Pool(self.number_of_processes) as p:
#            return p.map(self.calculate_centroids_cluster_stream, chunks)
        return map(self.calculate_centroids_cluster_stream, chunks)

    def calculate_centroids_dbscan(self, chunk):
        shot, x, y, tof, tot = chunk

        tot_filter = tot > self.tot_threshold
        # Filter out pixels
        shot = shot[tot_filter]
        x = x[tot_filter]
        y = y[tot_filter]
        tof = tof[tot_filter]
        tot = tot[tot_filter]

        labels = self.perform_clustering_dbscan(shot, x, y, tof)

        label_filter = labels != 0

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

    def calculate_centroids_cluster_stream(self, chunk):

        labels = self.cstream.perform(np.transpose(chunk[1:,:]))

        label_filter = labels != 0

        shot, x, y, tof, tot = chunk

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

    def perform_clustering_dbscan(self, shot, x, y, tof):
        """ The clustering with DBSCAN, which is performed in this function is dependent on the
            order of the data in rare cases. Therefore, reordering in any means can
            lead to slightly changed results, which should not be an issue.

            Martin Ester, Hans-Peter Kriegel, Jiirg Sander, Xiaowei Xu: A Density Based Algorithm for
            Discovering Clusters [p. 229-230] (https://www.aaai.org/Papers/KDD/1996/KDD96-037.pdf)
            A more specific explaination can be found here:
            https://stats.stackexchange.com/questions/306829/why-is-dbscan-deterministic"""
        if x.size >= 0:
            X = np.column_stack(
                (shot * self.epsilon * 1_000, x, y, tof * self._tof_scale)
            )

            dist = DBSCAN(
                eps=self.epsilon,
                min_samples=self.min_samples,
                metric="euclidean",
                n_jobs=1,
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
            cluster_tof -= (
                self._cent_timewalk_lut[np.int_(cluster_totMax // 25) - 1] * 1e3
            )
            # TODO: should totAvg not also be timewalk corrected?!
            # cluster_tof *= 1e-6

        return (
            cluster_shot,
            cluster_x,
            cluster_y,
            cluster_tof,
            cluster_totAvg,
            cluster_totMax,
            cluster_size,
        )


class CentroidCalculatorPooled(CentroidCalculator):

    """
    Parallelized implementation of CentroidCalculator using mp.Pool for parallelization.
    """

    def __init__(self, number_of_processes=None, *args, **kwargs):
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
        del self_dict["_pool"]
        return self_dict
