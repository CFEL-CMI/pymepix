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
import time
import os
import struct

import numpy as np
import h5py
from .logic.centroid_calculator import CentroidCalculator, CentroidCalculatorPooled
from .logic.packet_processor_factory import packet_processor_factory


class RawFileSampler():

    def __init__(
        self,
        file_name,
        output_file,
        number_of_processes=None,
        timewalk_file=None,
        cent_timewalk_file=None,
        progress_callback=None,
        camera_generation=3,
        clustering_args={},
        dbscan_clustering=True,
        **kwargs
    ):
        self._filename = file_name
        self._output_file = output_file
        self.timewalk_file = timewalk_file
        self.cent_timewalk_file = cent_timewalk_file

        self._number_of_processes = number_of_processes
        self._progress_callback = progress_callback

        self._clustering_args = clustering_args
        self._dbscan_clustering = dbscan_clustering
        self.camera_generation = camera_generation

    def init_new_process(self, file):
        """create connections and initialize variables in new process"""
        self._startTime = None
        with open(self._filename, 'rb') as file:
            self._startTime = struct.unpack("L", file.read(8))[0]

        self._longtime = -1
        self._longtime_msb = 0
        self._longtime_lsb = 0
        self._packet_buffer = []
        
        self._last_longtime = 0
        timewalk_lut = None
        cent_timewalk_lut = None
        if self.timewalk_file is not None:
            timewalk_lut = np.load(self.timewalk_file)
        if self.cent_timewalk_file is not None:
            cent_timewalk_lut = np.load(self.cent_timewalk_file)

        self.packet_processor = packet_processor_factory(self.camera_generation)(start_time=self._startTime, timewalk_lut=timewalk_lut)

        self.centroid_calculator = CentroidCalculator(cent_timewalk_lut=cent_timewalk_lut,
                                                      number_of_processes=self._number_of_processes,
                                                      clustering_args=self._clustering_args,
                                                      dbscan_clustering=self._dbscan_clustering)

    def pre_run(self):
        """init stuff which should only be available in new process"""

        try:
            os.remove(self._output_file)
        except OSError:
            pass

        self.init_new_process(self._filename)
        self._last_update = time.time()

        self.packet_processor.pre_process()
        self.centroid_calculator.pre_process()

    def post_run(self):
        result = self.packet_processor.post_process()

        self._packet_buffer = []
        if result is not None:
            lenth_of_data = len(result)
            self.__calculate_and_save_centroids(*result)

        self.centroid_calculator.post_process()

    def bytes_from_file(self, data_type="<u8"):
        print("Reading to memory", flush=True)
        with open(self._filename, 'rb') as file:
            ba = np.fromfile(file, dtype=data_type)
        print("Done", flush=True)

        packets_to_process = len(ba)
        packets_processed = 0

        for b in np.nditer(ba):
            yield b
            packets_processed += 1
            if self._progress_callback is not None:
                self._progress_callback(packets_processed / packets_to_process)

    def handle_lsb_time(self, pixdata):
        self._longtime_lsb = (pixdata & 0x0000FFFFFFFF0000) >> 16

    def handle_msb_time(self, pixdata):
        self._longtime_msb = (pixdata & 0x00000000FFFF0000) << 16
        tmplongtime = self._longtime_msb | self._longtime_lsb
        if ((tmplongtime + 0x10000000) < (self._longtime)) and (self._longtime > 0):
            print(
                "Large backward time jump {} {} ignoring".format(
                    self._longtime * 25e-9, tmplongtime * 25e-9
                )
            )
        elif (tmplongtime > (self._longtime + 0x10000000)) and (self._longtime > 0):
            print(
                "Large forward time jump {} {}".format(self._longtime * 25e-9, tmplongtime * 25e-9)
            )
            self._longtime = (self._longtime_msb - 0x10000000) | self._longtime_lsb
        else:
            self._longtime = tmplongtime
        if self._last_longtime == 0:
            self._last_longtime = self._longtime
            return False

        time_diff = (self._longtime - self._last_longtime) * 25e-9
        # print('msb_time:', time_diff, tmplongtime)

        if (time_diff) > 5.0:
            self._last_longtime = self._longtime
            return True
        else:
            return False

    def handle_other(self, pixdata):
        """trash data which arrives before 1st timestamp data (heartbeat)"""
        if self._longtime == -1:
            return

        self._packet_buffer.append(pixdata)

    def push_data(self, post=False):
        result = self.__run_packet_processor(self._packet_buffer)

        self._packet_buffer = []
        if result is not None:
            self.__calculate_and_save_centroids(*result)

    def __run_packet_processor(self, packet_buffer):
        if len(packet_buffer) > 0:
            packet_buffer.append(np.uint64(self._longtime))
            return self.packet_processor.process(np.array(packet_buffer, dtype=np.uint64).tobytes())

        return None

    def __calculate_and_save_centroids(self, event_data, _pixel_data, timestamps, _trigger_data):
        centroids = self.centroid_calculator.process(event_data)
        self.saveToHDF5(self._output_file, event_data, centroids, timestamps, _trigger_data)

    def saveToHDF5(self, output_file, raw, clusters, timeStamps, _trigger_data):
        if output_file is not None:
            with h5py.File(output_file, "a") as f:
                names = ["trigger nr", "x", "y", "tof", "tot avg", "tot max", "clustersize"]
                ###############
                # save centroided data
                if clusters is not None:
                    if f.keys().__contains__("centroided"):
                        for i, key in enumerate(names):
                            dset = f["centroided"][key]
                            dset.resize(dset.shape[0] + len(clusters[i]), axis=0)
                            dset[-len(clusters[i]) :] = clusters[i]
                    else:
                        grp = f.create_group("centroided")
                        grp.attrs["description"] = "centroided events"
                        grp.attrs["nr events"] = 0
                        for i, key in enumerate(names):
                            grp.create_dataset(key, data=clusters[i], maxshape=(None,))
                        f["centroided/tot max"].attrs["unit"] = "s"
                        f["centroided/tot avg"].attrs["unit"] = "s"
                        f["centroided/tot max"].attrs[
                            "description"
                        ] = "maximum of time above threshold in cluster"
                        f["centroided/tot avg"].attrs[
                            "description"
                        ] = "mean of time above threshold in cluster"
                        f["centroided/tof"].attrs["unit"] = "s"
                        f["centroided/x"].attrs["unit"] = "pixel"
                        f["centroided/y"].attrs["unit"] = "pixel"
                # out_file.flush()

                ###############
                # save raw data
                if raw is not None:
                    names = ["trigger nr", "x", "y", "tof", "tot"]
                    if f.keys().__contains__("raw"):
                        for i, key in enumerate(names):
                            dset = f["raw"][key]
                            dset.resize(dset.shape[0] + len(raw[i]), axis=0)
                            dset[-len(raw[i]) :] = raw[i]
                    else:
                        grp = f.create_group("raw")
                        grp.attrs["description"] = "timewalk corrected raw events"
                        grp.attrs["nr events"] = 0
                        grp.create_dataset("trigger nr", data=raw[0].astype(np.uint64), maxshape=(None,))
                        grp.create_dataset("x", data=raw[1].astype(np.uint8), maxshape=(None,))
                        grp.create_dataset("y", data=raw[2].astype(np.uint8), maxshape=(None,))
                        grp.create_dataset("tof", data=raw[3], maxshape=(None,))
                        grp.create_dataset("tot", data=raw[4].astype(np.uint32), maxshape=(None,))

                        f["raw/tof"].attrs["unit"] = "s"
                        f["raw/tot"].attrs["unit"] = "s"
                        f["raw/x"].attrs["unit"] = "pixel"
                        f["raw/y"].attrs["unit"] = "pixel"

                ###############
                # save time stamp data                
                if timeStamps is not None and self._startTime is not None:
                    names = ["trigger nr", "timestamp"]
                    if f.keys().__contains__("timing/timepix"):
                        for i, key in enumerate(names):
                            dset = f["timing/timepix"][key]
                            dset.resize(dset.shape[0] + len(timeStamps[i]), axis=0)
                            dset[-len(timeStamps[i]) :] = timeStamps[i]
                    else:
                        grp = f.create_group("timing")
                        grp.attrs["description"] = "timing information from TimePix and facility"
                        subgrp = grp.create_group("timepix")
                        subgrp.attrs["description"] = "timing information from TimePix"
                        subgrp.attrs["nr events"] = 0
                        for i, key in enumerate(names):
                            subgrp.create_dataset(
                                key, data=timeStamps[i], maxshape=(None,)
                            )
                        f["timing/timepix/timestamp"].attrs["unit"] = "ns"

                # save trigger1 data
                if _trigger_data is not None:
                    for trig_num, trigger in enumerate(_trigger_data):
                        if trigger is None:
                            continue
                        if f.keys().__contains__(f"triggers/trigger{trig_num+1}"):
                            dset = f[f"triggers/trigger{trig_num+1}/time"]
                            dset.resize(dset.shape[0] + len(trigger), axis=0)
                            dset[-len(trigger) :] = trigger
                        else:
                            if not f.keys().__contains__("triggers"):
                                grp = f.create_group("triggers")
                                grp.attrs["description"] = "triggering information from TimePix"
                            else:
                                grp = f["triggers"]
                            grp.attrs["description"] = "triggering information from TimePix"
                            subgrp = grp.create_group(f"trigger{trig_num+1}")
                            subgrp.attrs["description"] = f"trigger{trig_num+1} time from TimePix starting"
                            subgrp.create_dataset(
                                "time", data=trigger, maxshape=(None,))
                            f[f"triggers/trigger{trig_num+1}/time"].attrs["unit"] = "s"





    def run(self):
        """method which is executed in new process via multiprocessing.Process.start"""
        self.pre_run()

        if self.camera_generation == 4:

            chunk_size = 65536 # draft implementation of raw file splitting, will need rework
            self._longtime = 0

            for i, packet in enumerate(self.bytes_from_file('<i8')):
                #print(packet)
                #pixdata = struct.pack('>i', packet)
                self.handle_other(packet)
                if i > 0 and i%chunk_size == 0:
                    self.push_data()

            if len(self._packet_buffer) > 0:
                self.push_data()


        elif self.camera_generation == 3:
            for packet in self.bytes_from_file():
                # if we'd leave this with numpy we had to write
                # ((packet & 0xF000000000000000) >> np.uint64(60)) & np.uint64(0xF)
                # see: https://stackoverflow.com/questions/30513741/python-bit-shifting-with-numpy
                pixdata = int(packet)
                header = ((pixdata & 0xF000000000000000) >> 60) & 0xF
                should_push = False
                # Read Pixel Matrix Sequential (Header=0hA0)
                # Read Pixel Matrix Data-Driven (Header=0hB0)
                if header == 0xA or header == 0xB:
                    self.handle_other(pixdata)
                # 0x4X timer configuration
                elif header == 0x4 or header == 0x6:
                    subheader = ((pixdata & 0x0F00000000000000) >> 56) & 0xF
                    if subheader == 0x4:
                        self.handle_lsb_time(pixdata)
                    elif subheader == 0x5:
                        should_push = self.handle_msb_time(pixdata)
                    else:
                        self.handle_other(pixdata)

                if should_push:
                    self.push_data()

            if len(self._packet_buffer) > 0:
                self.push_data()

        else:
            raise ValueError(f'No implementation of rawfilesampler for camera version {self.camera_generation}')
        
        self.post_run()