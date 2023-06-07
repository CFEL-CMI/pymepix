import os
import pathlib

import h5py
import numpy as np

from pymepix.post_processing import run_post_processing

folder_path = pathlib.Path(__file__).parent / "files"
input_file_name = folder_path / 'out_5sec.raw'

def test_packets_trigger():

    def callback(progress):
        pass

    tmp_file_name = folder_path / "temp.hdf'"

    run_post_processing(input_file_name, tmp_file_name, 4, None, None, callback)

    with h5py.File(tmp_file_name) as new_file:
        hdf_timestamps = new_file['timing/timepix/timestamp'][:]
        hdf_triggers1 = new_file['triggers/trigger1/time'][:]
        hdf_triggers2 = new_file['triggers/trigger2/time'][:]

    with open(input_file_name, 'rb') as file:
        ba = np.fromfile(file, dtype="<u8")

        header = ((ba & 0xF000000000000000) >> 60) & 0xF
        subheader = ((ba & 0x0F00000000000000) >> 56) & 0xF

        triggers1_frombinary = ba[
            np.logical_and(
                np.logical_or(header == 0x4, header == 0x6), subheader == 0xF
            )
        ]

        triggers2_frombinary = ba[np.logical_and(
            header == 0x6, np.logical_or(subheader == 0xE, subheader == 0xB)
        )]

        assert len(hdf_timestamps) == len(hdf_triggers1)
        assert len(hdf_triggers1) == len(triggers1_frombinary)
        assert len(hdf_triggers2) == len(triggers2_frombinary)

        print('Done')

        os.remove(tmp_file_name)


if __name__ == "__main__":
    test_packets_trigger()
