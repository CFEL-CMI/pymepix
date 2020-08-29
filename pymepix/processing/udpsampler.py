##############################################################################
##
# This file is part of Pymepix
#
# https://arxiv.org/abs/1905.07999
#
#
# Pymepix is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pymepix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Pymepix.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import ctypes
import numpy as np
import multiprocessing
import socket
import time
import zmq

from multiprocessing.sharedctypes import Value
from pymepix.core.log import ProcessLogger
# from pymepix.processing.basepipeline import BasePipelineObject
from pymepix.processing.rawtodisk import Raw2Disk


class UdpSampler(multiprocessing.Process, ProcessLogger):
    """Recieves udp packets from SPDIR

    This class, creates a UDP socket connection to SPIDR and recivies the UDP packets from Timepix
    It them pre-processes them and sends them off for more processing

    """

    def __init__(self, address, longtime, chunk_size=10_000, flush_timeout=0.3, input_queue=None, create_output=True,
                 num_outputs=1, shared_output=None):
        #BasePipelineObject.__init__(self, 'UdpSampler', input_queue=input_queue, create_output=create_output,
        #                            num_outputs=num_outputs, shared_output=shared_output)
        name = 'UdpSampler'
        ProcessLogger.__init__(self, name)
        multiprocessing.Process.__init__(self)


        self.init_param = {'address': address,
                           'chunk_size': chunk_size,
                           'flush_timeout': flush_timeout,
                           'longtime': longtime}
        self._record = Value(ctypes.c_bool, False)
        self._enable = Value(ctypes.c_bool, True)
        self._close_file = Value(ctypes.c_bool, False)
        self.loop_count = 0

    def init_new_process(self):
        """create connections and initialize variables in new process"""
        try:
            self.create_socket_connection(self.init_param['address'])
            self._chunk_size = self.init_param['chunk_size'] * 8192
            self._flush_timeout = self.init_param['flush_timeout']
            self._packets_collected = 0
            self._packet_buffer_list = [bytearray(int(1.5 * self._chunk_size))
                                        for i in range(5)]  # ring buffer to put received data in
            self._buffer_list_idx = 0
            self._packet_buffer_view_list = [memoryview(self._packet_buffer_list[i])
                                             for i in range(len(self._packet_buffer_list))]
            self._packet_buffer_view = self._packet_buffer_view_list[self._buffer_list_idx]
            self._recv_bytes = 0
            self._total_time = 0.0
            self._longtime = self.init_param['longtime']

            # create connection to packetprocessor
            self.debug('create packetprocessor socket')
            ctx = zmq.Context.instance()
            self._packet_sock = ctx.socket(zmq.PUSH)
            self._packet_sock.bind('ipc:///tmp/packetProcessor')
        except Exception as e:
            self.error('Exception occured in init!!!')
            self.error(e, exc_info=True)
            raise

    def create_socket_connection(self, address):
        """Establishes a UDP connection to spidr"""
        self._sock = socket.socket(socket.AF_INET,     # Internet
                                   socket.SOCK_DGRAM)  # UDP
        self._sock.settimeout(1.0)
        self.info('Establishing connection to : {}'.format(address))
        self._sock.bind(address)

    def get_useful_packets(self, packet):
        # Get the header
        header = ((packet & 0xF000000000000000) >> 60) & 0xF
        subheader = ((packet & 0x0F00000000000000) >> 56) & 0xF
        pix_filter = (header == 0xA) | (header == 0xB)
        trig_filter = ((header == 0x4) | (header == 0x6)) & (subheader == 0xF)
        tpx_filter = pix_filter | trig_filter
        tpx_packets = packet[tpx_filter]
        return tpx_packets

    @property
    def enable(self):
        """Enables processing

        Determines whether the class will perform processing, this has the result of signalling the process to terminate.
        If there are objects ahead of it then they will stop receiving data
        if an input queue is required then it will get from the queue before checking processing
        This is done to prevent the queue from growing when a process behind it is still working

        Parameters
        -----------
        value : bool
            Enable value


        Returns
        -----------
        bool:
            Whether the process is enabled or not


        """
        return bool(self._enable.value)

    @enable.setter
    def enable(self, value):
        self.debug('Setting enabled flag to {}'.format(value))
        self._enable.value = bool(value)

    @property
    def record(self):
        """Enables saving data to disk

        Determines whether the class will perform processing, this has the result of signalling the process to terminate.
        If there are objects ahead of it then they will stop recieving data
        if an input queue is required then it will get from the queue before checking processing
        This is done to prevent the queue from growing when a process behind it is still working

        Parameters
        -----------
        value : bool
            Enable value

        Returns
        -----------
        bool:
            Whether the process should record and write to disk or not
        """
        return bool(self._record.value)

    @record.setter
    def record(self, value):
        self.debug(f'Setting record flag to {value}')
        self._record.value = bool(value)

    @property
    def close_file(self):
        return bool(self._close_file.value)

    @close_file.setter
    def close_file(self, value):
        self.debug(f'Setting close_file to {value}')
        self._close_file.value = bool(value)

    @property
    def outfile_name(self):
        return self._outfile_name

    @outfile_name.setter
    def outfile_name(self, fileN):
        self.info(f'Setting file name flag to {fileN}')
        if self.write2disk.open_file(fileN):
            self.info(f"file {fileN} opened")
        else:
            self.error("Huston, here's a problem, file cannot be created.")

    def pre_run(self):
        """init stuff which should only be available in new process"""
        self.init_new_process()
        self.write2disk = Raw2Disk()
        self._last_update = time.time()

    def post_run(self):
        """
        method get's called either at the very end of the process live or
        if there's a socket timeout and raw2disk file should be closed
        """
        if self._recv_bytes > 1:
            bytes_to_send = self._recv_bytes
            self._recv_bytes = 0

            curr_list_idx = self._buffer_list_idx
            self._buffer_list_idx = (self._buffer_list_idx + 1) % len(self._packet_buffer_list)
            self._packet_buffer_view = self._packet_buffer_view_list[self._buffer_list_idx]

            self.write2disk.my_sock.send(
                self._packet_buffer_list[curr_list_idx][:bytes_to_send], copy=False)
            if self.write2disk.writing:
                self.write2disk.my_sock.send(b'EOF')  # we should get a response here, this ends up in nirvana at this point
                self.debug('post_run: closed file')
            #return MessageType.RawData, (
            #    self._packet_buffer_list[curr_list_idx][:bytes_to_send], self._longtime.value)
            return None, None
        else:
            if self.write2disk.writing:
                self.debug('post_run: close file')
                self.write2disk.my_sock.send(b'EOF')  # we should get a response here, but the socket is elsewhere...
                self.debug('post_run: closed file')
            return None, None


    def run(self):
        """method which is executed in new process via multiprocessing.Process.start"""
        self.pre_run()
        enabled = self.enable
        start = time.time()
        while True:
            if enabled:
                try:
                    self._recv_bytes += self._sock.recv_into(
                        self._packet_buffer_view[self._recv_bytes:])
                except socket.timeout:
                    enabled = self.enable
                    # put close file here to get the cases where there's no data coming and file should be closed
                    # mainly there for test to succeed
                    if self.close_file:
                        self.close_file = False
                        self.post_run()
                    else:
                        self.debug('Socket timeout')
                except socket.error:
                    self.debug('socket error')

                self._packets_collected += 1
                end = time.time()

                self._total_time += end - start
                #if self._packets_collected % 1000 == 0:
                #    self.debug('Packets collected {}'.format(self._packets_collected))
                #    self.debug('Total time {} s'.format(self._total_time))

                flush_time = end - self._last_update

                # sends empty packets if flush_timeout==True but no data was received
                #
                if (self._recv_bytes > self._chunk_size) or (flush_time > self._flush_timeout):
                    # tpx_packets = self.get_useful_packets(packet)
                    if self.record:
                        self.write2disk.my_sock.send(
                            self._packet_buffer_list[self._buffer_list_idx][:self._recv_bytes], copy=False)
                    elif self.close_file:
                        self.close_file = False
                        self.debug('received close file')
                        self.write2disk.my_sock.send(
                            self._packet_buffer_list[self._buffer_list_idx][:self._recv_bytes], copy=False)
                        self.write2disk.my_sock.send(b'EOF')
                    # send stuff to packet processor
                    #elif self._buffer_list_idx == 4:
                    # add longtime to buffers end
                    bytes_to_send = self._recv_bytes + 8
                    self._packet_buffer_view[self._recv_bytes:bytes_to_send] = np.uint64(self._longtime.value).tobytes()
                    self._packet_sock.send(
                            self._packet_buffer_list[self._buffer_list_idx][:bytes_to_send], copy=False)

                    self._recv_bytes = 0
                    self._buffer_list_idx = (self._buffer_list_idx + 1) % len(self._packet_buffer_list)
                    self._packet_buffer_view = self._packet_buffer_view_list[self._buffer_list_idx]
                    self._last_update = time.time()
                    enabled = self.enable
                    # if len(packet) > 1:

                    #if not curr_list_idx % 20:
                    #   return MessageType.RawData, (self._packet_buffer_list[curr_list_idx][:bytes_to_send], self._longtime.value)
                    # else:
                    # return None, None
                    # else:
                    #    return None, None
                # else:
                #    return None, None
            else:
                self.debug('I AM LEAVING')
                break
        self.post_run()
        self.write2disk.my_sock.close()



    def stopRaw2Disk(self):
        # TODO: this doesn't work for now. should probably go to post_run
        '''
        self.debug('Stopping Raw2Disk')
        self.write2disk.close()
        self.write2disk.my_sock.send_string('SHUTDOWN')
        # print(write2disk.my_sock.recv())
        self.write2disk.write_thr.join()
        self.debug('Raw2Disk stopped')
        '''

def main():
    from multiprocessing import Process
    import zmq
    import time
    import numpy as np
    # Create the logger
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def send_data(packets, chunk_size, start=0, sleep=0.0001):
        ############
        # send data
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        test_data = np.arange(start, start + packets * chunk_size,
                              dtype=np.uint64)  # chunk size 135 -> max number=1_012_500
        test_data_view = memoryview(test_data)
        time.sleep(1)  # seems to be necessary if this function get called as a Process
        # first packet 0...134, second packet 135...269 and so on
        print('sending process')
        start = time.time()
        for i in range(0, len(test_data_view), chunk_size):
            sock.sendto(test_data_view[0:0 + chunk_size], ('127.0.0.1', 50000))
            #time.sleep(sleep)  # if there's no sleep, packets get lost
        stop = time.time()
        dt = stop - start
        print(f'time to send {dt:.2f}',
              f'time to send 1M: {dt/packets*1_000_002:.2f}s, '
              #f'bytes: {len(test_data_view.tobytes())}, '
              f'MBytes: {len(test_data_view.tobytes()) * 1e-6:.1f}, '
              f'{len(test_data_view.tobytes()) * 1e-6 / dt:.2f} MByte/s')
        #return test_data

    ctx = zmq.Context.instance()
    z_sock = ctx.socket(zmq.PAIR)
    z_sock.bind('tcp://127.0.0.1:40000')
    # z_sock.send_string('hallo')
    # print(z_sock.recv_string())

    sampler = UdpSampler(('127.0.0.1', 50000), 1)
    time.sleep(1)  # give thread time to start
    # send data
    packets = 3_500_000
    chunk_size = 139
    # test_data = np.arange(0, packets * chunk_size, dtype=np.uint64)
    # test_data = send_data(packets=10_000, chunk_size=135, start=15000, sleep=1e-4)
    p = Process(target=send_data, args=(packets, chunk_size, 0, 0))
    start = time.time()
    p.start()

    sampler.start()
    p.join()
    print('sending finished')
    stop = time.time()
    z_sock.send_string('SHUTDOWN')
    time.sleep(1)
    z_sock.close()
    sampler.enable = False

    print(f'took {stop - start}s')

if __name__ == "__main__":
    main()