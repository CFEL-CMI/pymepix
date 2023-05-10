from .packet_processor import PacketProcessor
from .packet_processor_tpx4 import PacketProcessor_tpx4


def packet_processor_factory(camera_generation):
    packet_processors = {3: PacketProcessor, \
                         4: PacketProcessor_tpx4}
    if camera_generation in packet_processors.keys():
        return packet_processors[camera_generation]
    else:
        raise ValueError(f'No packet processor for camera generation {camera_generation}')