import numpy as np
from enum import IntEnum
from multiprocessing.sharedctypes import Value
import os
import time
import h5py
import sys
import struct


class PixelOrientation(IntEnum):
    """Defines how row and col are intepreted in the output"""
    Up = 0
    """Up is the default, x=column,y=row"""
    Left = 1
    """x=row, y=-column"""
    Down = 2
    """x=-column, y = -row """
    Right = 3
    """x=-row, y=column"""


class TOFCentroidingNew(object):
    """Performs centroiding on EventData recieved from Packet processor

    """

    def __init__(self, n_procs=4, timewalk=None, skip_data=1, tot_filter=0, epsilon=3.0, samples=3,
                 num_outputs=1):

        self._n_procs = n_procs
        self._timewalk_lut = timewalk

        self._centroid_count = 0
        self._search_time = 0.0
        self._blob_time = 0.0
        self._skip_data = Value('I', skip_data)
        self._tot_threshold = Value('I', tot_filter)
        self._epsilon = Value('d', 3.0)
        self._min_samples = Value('I', 3)
        self._num_centroids = 0

    @property
    def centroidSkip(self):
        """Sets whether to process every nth pixel packet.

        For example, setting it to 2 means every second packet is processed. 1 means all pixel packets are processed.

        """
        return self._skip_data.value

    @centroidSkip.setter
    def centroidSkip(self, value):
        value = max(1, value)
        self._skip_data.value = value

    @property
    def totThreshold(self):
        return self._tot_threshold.value

    @totThreshold.setter
    def totThreshold(self, value):
        value = max(0, value)
        self._tot_threshold.value = value

    @property
    def epsilon(self):
        """Sets whether to process every nth pixel packet.

        For example, setting it to 2 means every second packet is processed. 1 means all pixel packets are processed.

        """
        return self._epsilon.value

    @epsilon.setter
    def epsilon(self, value):
        # value = max(1,value)
        self.info('Epsilon set to {}'.format(value))
        self._epsilon.value = value

    @property
    def samples(self):
        return self._min_samples.value

    @samples.setter
    def samples(self, value):
        self._min_samples.value = value

    def process(self, data):
        shot, x, y, tof, tot = data

        _, indices, counts = np.unique(shot, return_index=True, return_counts=True)
        comb = zip(indices, counts)

        for idx, cnt in comb:
            start = idx
            end = idx + cnt
            res = self.process_centroid(shot[start:end], x[start:end], y[start:end], tof[start:end], tot[start:end])
            if res is not None:
                return res

        return None

    def process_centroid(self, shot, x, y, tof, tot):

        # print('CENTROID DATA',data)

        self._num_centroids += 1

        # if self._num_centroids % 1000:
        #     self.debug('Search time: {}'.format(self._search_time))
        #     self.debug('Blob time: {} '.format(self._blob_time))

        # if self._num_centroids % self.centroidSkip == 0:
        #     return None,None

        tot_filter = (tot > self.totThreshold)
        # Filter out pixels
        shot = shot[tot_filter]
        x = x[tot_filter]
        y = y[tot_filter]
        tof = tof[tot_filter]
        tot = tot[tot_filter]

        start = time.time()
        labels = self.find_cluster(shot, x, y, tof, tot, epsilon=self.epsilon, min_samples=self.samples)
        self._search_time += time.time() - start
        label_filter = labels != 0

        if labels is None:
            return None

        # print(labels[label_filter ].size)
        if labels[label_filter].size == 0:
            return None
        else:
            start = time.time()
            props = self.cluster_properties(shot[label_filter], x[label_filter], y[label_filter], tof[label_filter],
                                            tot[label_filter], labels[label_filter])
            # print(props)
            self._blob_time += time.time() - start
            return props

    def find_cluster(self, shot, x, y, tof, tot, epsilon=2, min_samples=2, tof_epsilon=None):
        from sklearn.cluster import DBSCAN

        if shot.size == 0:
            return None
        # print(shot.size)
        tof_eps = 81920 * (25. / 4096) * 1E-9

        tof_scale = epsilon / tof_eps
        X = np.vstack((shot * epsilon * 1000, x, y, tof * tof_scale)).transpose()
        dist = DBSCAN(eps=epsilon, min_samples=min_samples, metric='euclidean', n_jobs=1).fit(X)
        labels = dist.labels_ + 1
        return labels

    def cluster_properties(self, shot, x, y, tof, tot, labels):
        import scipy.ndimage as nd

        label_index = np.unique(labels)
        tot_max = np.array(nd.maximum_position(tot, labels=labels, index=label_index)).flatten()
        # tof_min = np.array(nd.minimum_position(tof,labels=labels,index=label_index)).flatten()
        # print(tot_max)
        tot_sum = nd.sum(tot, labels=labels, index=label_index)
        cluster_x = np.array(nd.sum(x * tot, labels=labels, index=label_index) / tot_sum).flatten()
        cluster_y = np.array(nd.sum(y * tot, labels=labels, index=label_index) / tot_sum).flatten()
        cluster_tof = np.array(nd.sum(tof * tot, labels=labels, index=label_index) / tot_sum).flatten()
        cluster_tot = tot[tot_max]
        # cluster_tof = tof[tot_max]
        cluster_shot = shot[tot_max]

        return cluster_shot, cluster_x, cluster_y, cluster_tof, cluster_tot


class TOFCentroiding(object):
    """Performs centroiding on EventData recieved from Packet processor

    """

    def __init__(self, n_procs=32, epsilon=2, samples=5, timewalk=None, startTime=None):

        self._epsilon = epsilon
        self._n_procs = int(n_procs)
        self._samples = samples
        self._timewalk_lut = timewalk
        if startTime is None:
            self._startTime = 0

    def process(self, shot, x, y, tof, tot):

        labels = self.find_cluster(shot, x, y, tof, tot)
        label_filter = labels != 0
        if labels is None:
            return None
        if labels[label_filter].size == 0:
            return None
        else:
            props = self.cluster_properties(shot[label_filter], x[label_filter], y[label_filter], tof[label_filter],
                                            tot[label_filter], labels[label_filter])
            return props

    def moments_com(self, X, Y, tot):

        total = tot.sum()
        x_bar = (X * tot).sum() / total
        y_bar = (Y * tot).sum() / total
        return x_bar, y_bar

    def find_cluster(self, shot, x, y, tof, tot):
        from sklearn.cluster import DBSCAN

        if shot.size == 0:
            return None
        # print(shot.size)
        tof_eps = 81920 * (25. / 4096)

        tof_scale = self._epsilon / tof_eps
        X = np.vstack((shot * self._epsilon * 1000, x, y, tof * tof_scale)).transpose()
        dist = DBSCAN(eps=self._epsilon, min_samples=self._samples, metric='euclidean', n_jobs=self._n_procs).fit(
            X)
        labels = dist.labels_ + 1
        return labels

    def cluster_properties(self, shot, x, y, tof, tot, labels):
        label_iter = np.unique(labels)
        total_objects = label_iter.size

        valid_objects = 0
        # Prepare our output
        cluster_shot = np.ndarray(shape=(total_objects,), dtype=np.int)
        cluster_x = np.ndarray(shape=(total_objects,), dtype=np.float64)
        cluster_y = np.ndarray(shape=(total_objects,), dtype=np.float64)
        cluster_tof = np.ndarray(shape=(total_objects,), dtype=np.float64)
        cluster_tot = np.ndarray(shape=(total_objects,), dtype=np.float64)

        for idx in range(total_objects):
            obj_slice = (labels == label_iter[idx])
            obj_shot = shot[obj_slice]
            # print(obj_shot.size)
            obj_x = x[obj_slice]
            obj_y = y[obj_slice]

            obj_tot = tot[obj_slice]
            max_tot = np.argmax(obj_tot)

            moments = self.moments_com(obj_x, obj_y, obj_tot)

            x_bar, y_bar = moments
            obj_tof = tof[obj_slice]

            cluster_tof[valid_objects] = obj_tof[max_tot]
            cluster_x[valid_objects] = x_bar
            cluster_y[valid_objects] = y_bar
            cluster_tot[valid_objects] = obj_tot[max_tot]
            cluster_shot[valid_objects] = obj_shot[0]
            valid_objects += 1

        if self._timewalk_lut is not None:
            cluster_tof -= self._timewalk_lut[(cluster_tot / 25).astype(np.int) - 1]

        return cluster_shot[:valid_objects], cluster_x[:valid_objects], \
               cluster_y[:valid_objects], cluster_tof[:valid_objects], cluster_tot[:valid_objects]


class PacketProcessor(object):
    """Processes Pixel packets for ToA, ToT,triggers and events

    This class, creates a UDP socket connection to SPIDR and recivies the UDP packets from Timepix
    It them pre-processes them and sends them off for more processing

    """

    def __init__(self,
                 timewalk=None, event_window=(0.0, 10000.0), position_offset=(0, 0),
                 orientation=PixelOrientation.Up, create_output=True, num_outputs=1, startTime=None):

        self.clearBuffers()
        self._timewalk_lut = timewalk
        self._orientation = orientation
        self._x_offset, self._y_offset = position_offset

        self._trigger_counter = 0

        min_window = event_window[0]
        max_window = event_window[1]
        self._min_event_window = Value('d', min_window)
        self._max_event_window = Value('d', max_window)

        self._startTime = startTime
        if startTime is None:
            self._startTime = 0

    def updateBuffers(self, val_filter):
        self._x = self._x[val_filter]
        self._y = self._y[val_filter]
        self._toa = self._toa[val_filter]
        self._tot = self._tot[val_filter]

    def getBuffers(self, val_filter=None):
        if val_filter is None:
            return np.copy(self._x), np.copy(self._y), np.copy(self._toa), np.copy(self._tot)
        else:
            return np.copy(self._x[val_filter]), np.copy(self._y[val_filter]), np.copy(self._toa[val_filter]), np.copy(
                self._tot[val_filter])

    def clearBuffers(self):
        self._x = None
        self._y = None
        self._tot = None
        self._toa = None
        self._triggers = None

    @property
    def minWindow(self):
        return self._min_event_window.value

    @minWindow.setter
    def minWindow(self, value):
        self._min_event_window.value = value

    @property
    def maxWindow(self):
        return self._max_event_window.value

    @maxWindow.setter
    def maxWindow(self, value):
        self._max_event_window.value = value

    @property
    def _eventWindow(self):
        return self._min_event_window.value, self._max_event_window.value

    def preRun(self):
        self.info('Running with triggers? {}'.format(self._handle_events))

    def process(self, data, longtime):

        packet = data

        header = ((packet & 0xF000000000000000) >> 60) & 0xF
        subheader = ((packet & 0x0F00000000000000) >> 56) & 0xF

        pixels = packet[np.logical_or(header == 0xA, header == 0xB)]
        triggers = packet[np.logical_and(np.logical_or(header == 0x4, header == 0x6), subheader == 0xF)]
        # timestamps = packet[np.logical_and(header == 0x01, subheader == 0x05)]

        """
        timingInformation = packet[np.logical_and(np.logical_or(header == 0x4, header == 0x6), np.logical_or(subheader == 0x4, subheader == 0x5))]
        if timingInformation.size > 0:
            for data in timingInformation:
                header = ((packet & 0xF000000000000000) >> 60) & 0xF
                subheader = ((packet & 0x0F00000000000000) >> 56) & 0xF
                if header == 0x4 and subheader == 0x4: # LSB
                    0x00FFFFFFFF00
                elif header == 0x4 and subheader == 0x5: # MSB
        """

        if pixels.size > 0:
            self.process_pixels(np.int64(pixels), longtime)

            if triggers.size > 0:
                # print('triggers', triggers, longtime)
                self.process_triggers(np.int64(triggers), longtime)

            events = self.find_events_fast()

            if events is not None:
                return events
            else:
                return None
        else:
            return None

    def filterBadTriggers(self):
        self._triggers = self._triggers[np.argmin(self._triggers):]

    def find_events_fast(self):
        if self._triggers is None:
            return None, None
        # self.filterBadTriggers()
        if self._triggers.size < 5:
            return None, None
        self.filterBadTriggers()
        if self._toa is None:
            return None, None
        if self._toa.size == 0:
            # Clear out the triggers since they have nothing
            return None, None

        # Get our start/end triggers to get events
        start = self._triggers[0:-1:]
        if start.size == 0:
            return None, None

        min_window, max_window = self._eventWindow

        trigger_counter = np.arange(self._trigger_counter, self._trigger_counter + start.size, dtype=np.int)

        self._trigger_counter = trigger_counter[-1] + 1

        # end = self._triggers[1:-1:]
        # Get the first and last triggers in pile
        first_trigger = start[0]
        last_trigger = start[-1]
        # print('First Trigger las trigger',first_trigger,last_trigger)
        # print('TOA before',self._toa)
        # Delete useless pixels behind the first trigger
        self.updateBuffers(self._toa >= first_trigger)
        # grab only pixels we care about
        x, y, toa, tot = self.getBuffers(self._toa < last_trigger)
        # print('triggers',start)
        # print('TOA',toa)
        self.updateBuffers(self._toa >= last_trigger)
        try:
            event_mapping = np.digitize(toa, start) - 1
        except Exception as e:
            print('Exception has occured {} due to ', str(e))
            print('Writing output TOA {}'.format(toa))
            print('Writing triggers {}'.format(start))
            print('Flushing triggers!!!')
            self._triggers = self._triggers[-1:]
            return None, None
        event_triggers = self._triggers[:-1:]
        self._triggers = self._triggers[-1:]

        # print('Trigger delta',triggers,np.ediff1d(triggers))

        tof = toa - event_triggers[event_mapping]
        event_number = trigger_counter[event_mapping]

        exp_filter = (tof >= min_window) & (tof <= max_window)

        result = event_number[exp_filter], x[exp_filter], y[exp_filter], tof[exp_filter], tot[exp_filter]

        if result[0][0].size > 0:
            timeStamps = np.uint64(start[np.unique(event_mapping)] * 1e9 + self._startTime)  # timestamp in ns for trigger event
            return result, (np.unique(result[0]), timeStamps)
        else:
            return None, None

    def correct_global_time(self, arr, ltime):
        pixelbits = (arr >> 28) & 0x3
        ltimebits = (ltime >> 28) & 0x3
        # diff = (ltimebits - pixelbits).astype(np.int64)
        # neg = (diff == 1) | (diff == -3)
        # pos = (diff == -1) | (diff == 3)
        # zero = (diff == 0) | (diff == 2)

        # res = ( (ltime) & 0xFFFFC0000000) | (arr & 0x3FFFFFFF)
        diff = (ltimebits - pixelbits).astype(np.int64)
        globaltime = (ltime & 0xFFFFC0000000) | (arr & 0x3FFFFFFF)
        neg_diff = (diff == 1) | (diff == -3)
        globaltime[neg_diff] = ((ltime - 0x10000000) & 0xFFFFC0000000) | (arr[neg_diff] & 0x3FFFFFFF)
        pos_diff = (diff == -1) | (diff == 3)
        globaltime[pos_diff] = ((ltime + 0x10000000) & 0xFFFFC0000000) | (arr[pos_diff] & 0x3FFFFFFF)
        # res[neg] =   ( (ltime - 0x10000000) & 0xFFFFC0000000) | (arr[neg] & 0x3FFFFFFF)
        # res[pos] =   ( (ltime + 0x10000000) & 0xFFFFC0000000) | (arr[pos] & 0x3FFFFFFF)
        # arr[zero] = ( (ltime) & 0xFFFFC0000000) | (arr[zero] & 0x3FFFFFFF)
        # arr[zero] =   ( (ltime) & 0xFFFFC0000000) | (arr[zero] & 0x3FFFFFFF)

        return globaltime

    def process_triggers(self, pixdata, longtime):
        coarsetime = pixdata >> 12 & 0xFFFFFFFF
        coarsetime = self.correct_global_time(coarsetime, longtime)
        tmpfine = (pixdata >> 5) & 0xF
        tmpfine = ((tmpfine - 1) << 9) // 12
        trigtime_fine = (pixdata & 0x0000000000000E00) | (tmpfine & 0x00000000000001FF)
        time_unit = 25. / 4096
        tdc_time = (coarsetime * 25E-9 + trigtime_fine * time_unit * 1E-9)

        m_trigTime = tdc_time
        # self.info(f'Trigger time {np.diff(tdc_time)}')

        # print(f'mtirgtime: {m_trigTime}')
        if self._triggers is None:
            self._triggers = m_trigTime
        else:
            self._triggers = np.append(self._triggers, m_trigTime)

    def orientPixels(self, col, row):
        if self._orientation is PixelOrientation.Up:
            return col, row
        elif self._orientation is PixelOrientation.Left:
            return row, 255 - col
        elif self._orientation is PixelOrientation.Down:
            return 255 - col, 255 - row
        elif self._orientation is PixelOrientation.Right:
            return 255 - row, col

    def process_pixels(self, pixdata, longtime):

        dcol = ((pixdata & 0x0FE0000000000000) >> 52)
        spix = ((pixdata & 0x001F800000000000) >> 45)
        pix = ((pixdata & 0x0000700000000000) >> 44)
        col = (dcol + pix // 4)
        row = (spix + (pix & 0x3))

        data = ((pixdata & 0x00000FFFFFFF0000) >> 16)
        spidr_time = (pixdata & 0x000000000000FFFF)
        ToA = ((data & 0x0FFFC000) >> 14)
        FToA = (data & 0xF)
        ToT = ((data & 0x00003FF0) >> 4) * 25
        time_unit = 25. / 4096

        # print('LONGTIME',longtime*25E-9)
        # print('SpidrTime',(spidr_time << 14)*25E-9)
        # print('TOA before global',((spidr_time << 14) |ToA)*25*1E-9)

        ToA_coarse = self.correct_global_time((spidr_time << 14) | ToA, longtime) & 0xFFFFFFFFFFFF
        # print('TOA after global', ToA_coarse*25*1E-9, longtime)
        globalToA = (ToA_coarse << 12) - (FToA << 8)
        # print('TOA after FTOa', globalToA*time_unit*1E-9)
        globalToA += ((col // 2) % 16) << 8
        globalToA[((col // 2) % 16) == 0] += (16 << 8)

        finalToA = globalToA * time_unit * 1E-9

        # print('finalToa',finalToA)
        # Orient the pixels based on Timepix orientation
        x, y = self.orientPixels(col, row)

        # #
        x += self._x_offset
        y += self._y_offset

        # print('PIXEL', finalToA, longtime)
        if self._x is None:
            self._x = x
            self._y = y
            self._toa = finalToA
            self._tot = ToT
        else:
            self._x = np.append(self._x, x)
            self._y = np.append(self._y, y)
            self._toa = np.append(self._toa, finalToA)
            self._tot = np.append(self._tot, ToT)


class RawHandle(object):
    """Reads files and acts like a UDPSampler for the rest of the pipeline
    """

    def __init__(self, filename, output_filename, n_procs=1, timewalk_file=None, cent_timewalk_file=None,
                 startTime=None):
        self._filename = filename
        self._longtime = -1
        self._longtime_msb = 0
        self._longtime_lsb = 0
        self._packet_buffer = []
        self._last_longtime = 0
        self._total_bytes = os.path.getsize(filename)
        self._read_bytes = 0
        self._timewalk_lut = None
        self._cent_timewalk_lut = None
        if timewalk_file is not None:
            self._timewalk_lut = self.load_timewalk(timewalk_file)
        if cent_timewalk_file is not None:
            self._cent_timewalk_lut = self.load_timewalk(cent_timewalk_file)
        self._startTime = startTime
        if startTime is None:
            self._startTime = 0
        self._packet_process = PacketProcessor(timewalk=self._timewalk_lut, startTime=self._startTime)
        self._centroid = TOFCentroiding(n_procs=n_procs, timewalk=self._cent_timewalk_lut, startTime=self._startTime)

        self._output_filename = output_filename

    def load_timewalk(self, filename):
        return np.load(filename)

    def handle_lsb_time(self, pixdata):
        self._longtime_lsb = (pixdata & 0x0000FFFFFFFF0000) >> 16

    def handle_msb_time(self, pixdata):
        self._longtime_msb = (pixdata & 0x00000000FFFF0000) << 16
        tmplongtime = self._longtime_msb | self._longtime_lsb
        if (((tmplongtime + 0x10000000) < (self._longtime)) and (self._longtime > 0)):
            print("Large backward time jump {} {} ignoring".format(self._longtime * 25E-9, tmplongtime * 25E-9))
        elif ((tmplongtime > (self._longtime + 0x10000000)) and (self._longtime > 0)):
            print("Large forward time jump {} {}".format(self._longtime * 25E-9, tmplongtime * 25E-9))
            self._longtime = (self._longtime_msb - 0x10000000) | self._longtime_lsb
        else:
            self._longtime = tmplongtime;
        if self._last_longtime == 0:
            self._last_longtime = self._longtime
            return False

        time_diff = (self._longtime * 25E-9 - self._last_longtime * 25E-9)
        # print(time_diff)

        if (time_diff) > 5.0:
            self._last_longtime = self._longtime
            return True
        else:
            return False

    def push_data(self, out_file):
        if len(self._packet_buffer) > 0:

            events, timeStamps = self._packet_process.process(np.array(self._packet_buffer, dtype=np.uint64), self._longtime)
            self._packet_buffer = []
            if events is not None:
                pass
                
                clusters = self._centroid.process(*events)
                # print(clusters)

                with h5py.File(out_file, 'a') as f:
                    names = ['nr', 'x', 'y', 'tof', 'tot']
                    ###############
                    # save centroided data
                    if clusters is not None:
                        if f.keys().__contains__('raw'):
                            for i, key in enumerate(names):
                                dset = f['centroided'][key]
                                dset.resize(dset.shape[0] + len(clusters[i]), axis=0)
                                dset[-len(clusters[i]):] = clusters[i]
                        else:
                            grp = f.create_group('centroided')
                            for i, key in enumerate(names):
                                grp.create_dataset(key, data=clusters[i], maxshape=(None,))
                            f['centroided/tof'].attrs['unit'] = 's'
                    # out_file.flush()

                    ###############
                    # save raw data
                    if f.keys().__contains__('raw'):
                        for i, key in enumerate(names):
                            dset = f['raw'][key]
                            dset.resize(dset.shape[0] + len(events[i]), axis=0)
                            dset[-len(events[i]):] = events[i]
                    else:
                        grp = f.create_group('raw')
                        for i, key in enumerate(names):
                            grp.create_dataset(key, data=events[i], maxshape=(None,))
                        f['raw/tof'].attrs['unit'] = 's'

                    ###############
                    # save time stamp data
                    if self._startTime is not None:
                        names = ['triggerNr', 'ns']
                        if f.keys().__contains__('tpx3Times'):
                            for i, key in enumerate(names):
                                dset = f['tpx3Times'][key]
                                dset.resize(dset.shape[0] + len(timeStamps[i]), axis=0)
                                dset[-len(timeStamps[i]):] = timeStamps[i]
                        else:
                            grp = f.create_group('tpx3Times')
                            for i, key in enumerate(names):
                                grp.create_dataset(key, data=timeStamps[i], maxshape=(None,))
                            f['tpx3Times/ns'].attrs['unit'] = 'ns'
                

    def handle_other(self, pixdata):
        if self._longtime == -1:
            return

        self._packet_buffer.append(pixdata)

    def bytes_from_file(self, chunksize=8192):
        with open(self._filename, "rb") as f:
            last_progress = 0

            print('Reading to memory', flush=True)
            ba = np.fromfile(f, dtype='<u8')
            print('Done', flush=True)

            for b in np.nditer(ba):
                self._read_bytes += 8
                progress = self._read_bytes * 100.0 / self._total_bytes
                int_progress = int(progress)
                if int_progress != 0 and int_progress % 5 == 0 and int_progress != last_progress:
                    print(f'Progress {progress:.1f} %', flush=True)
                    last_progress = int_progress
                yield b

    def process(self):
        for packet in self.bytes_from_file():
            pixdata = int(packet)
            header = ((pixdata & 0xF000000000000000) >> 60) & 0xF
            should_push = False
            if (header == 0xA or header == 0xB):
                self.handle_other(pixdata)
            elif (header == 0x4 or header == 0x6):
                subheader = ((pixdata & 0x0F00000000000000) >> 56) & 0xF
                if (subheader == 0xF):
                    self.handle_other(pixdata)
                    # print(triggers[-1])
                elif (subheader == 0x4):
                    self.handle_lsb_time(pixdata)
                elif (subheader == 0x5):
                    should_push = self.handle_msb_time(pixdata)
            # print(packet)

            if should_push:
                self.push_data(self._output_filename)

        if len(self._packet_buffer) > 0:
            self.push_data(self._output_filename)


def main():
    import logging
    import glob

    if len(sys.argv) != 2:
        logging.error(f"usage: {sys.argv[0]}, <filename>")
        sys.exit(1)

    time.sleep(60) # sleep so raw only conversion can finish first
    # import configparser
    """Read the necessary parameters from the Config.ini file"""
    outdir = '/asap3/fs-flash-o/gpfs/camp/2019/data/11008905/processed'
    dirr = '/asap3/fs-flash-o/gpfs/camp/2019/data/11008905/raw/timepix/'
    outdir = 'out'
    dirr = 'data'
    timewalk = None
    centtimewalk = None
    startTime = None
    import multiprocessing
    n_procs = multiprocessing.cpu_count()

    in_files = glob.glob(os.path.join(dirr, '2019103*.raw'))
    #print(in_files)

    #in_files = ['data/20191029_e-SoPhy-Pymepix_belke-800-1400_000000.raw',
    #            '',
    #            'data/20191029_e-SoPhy-Femtolab_belke-800-1400_0.raw'
    #            ]
    # in_files = ['data/20191029_e-SoPhy-Pymepix-PLL_belke-800-1400_000000.raw']
    #in_files = ['data/pyrrole__100.raw']
    # in_files = ['data/20191029_e-SoPhy-Pymepix-PLL_belke-800-1400_000000.raw']
    in_files = [sys.argv[1]]

    start = time.time()
    for file in in_files:
        #file = os.path.join(dirr, file)
        base = os.path.basename(file)
        base_name = os.path.splitext(base)[0]
        output_name = os.path.join(outdir, f'{base_name}.hdf5')
        # remove existing file because we append data to it
        try:
            os.remove(output_name)
        except OSError:
            pass
        print('Processing {}'.format(file))
        with open(file, 'rb') as f:
            startTime = struct.unpack('L', f.read(8))[0]
        fr = RawHandle(file, output_name, n_procs=n_procs, \
                       timewalk_file=timewalk, cent_timewalk_file=centtimewalk, startTime=startTime)
        fr.process()
        print(f'Finished {output_name}')

    # put trainIDs into hdf5 file
    traidIDFile = os.path.join(dirr, f'{base_name}.trainID')
    ids = []
    timestamps = []
    with open(traidIDFile, 'rb') as f:
        while True:
            try:
                timestamps.append(np.load(f))
                ids.append(np.load(f))
            except:
                break
    ids = np.row_stack(ids).ravel()
    timestamps = np.row_stack(timestamps).ravel()
    with h5py.File(output_name, 'r+') as f:
        grp = f.create_group('x2Times')
        grp.create_dataset('ns', data=timestamps)
        grp.create_dataset('bunchID', data=ids)
    print(f'took: {time.time() - start}s')

if __name__ == "__main__":
    main()
