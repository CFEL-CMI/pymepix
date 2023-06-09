import pathlib

import h5py
import numpy as np

from pymepix.processing.rawfilesampler import RawFileSampler

"""Perform the calculation of centroids (post-processing) for a complete, real-world dataset.
The result is verified against data processed with the previously, internally used RawConverter. 
The results of the RawConverter are therefore assumed to be absolute Truth. 

If changes are expected due to adjustments in Clustering or Centroiding, the ground truth data has
to be replaced or adjusted! If there are issues with this test do not assume the code to be wrong in any case
as this test is only based on the RawConverters results. Different results are not necessarily bad! But check 
your results very carefully if they differ!"""

def updateProgressBar(progress):
   pass

folder_path = pathlib.Path(__file__).parent / "files"
def test_converted_hdf5():
    filename = folder_path / "ion-run_0006_20221112-1024.raw"
    tmp_file_name = folder_path / "ion-run_0006_20221112-1024-temp.hdf5"
    file_sampler = RawFileSampler(filename, tmp_file_name, 4, None, None, updateProgressBar)
    file_sampler.run()

    with h5py.File(tmp_file_name) as new_file:
        print(new_file['centroided'].keys())
        print(len(new_file['raw/x'][:]))
        print(len(new_file['centroided/x'][:]))

        # The RawConverter has been slightly adjusted for this comparison. The pixels were sorted by the shot number to match the order which is required
        # for the processing in chunks. This is required as the DBSCAN algorithm can be non-deterministic regarding the order in some rare scenarios.
        # Martin Ester, Hans-Peter Kriegel, Jiirg Sander, Xiaowei Xu: A Density Based Algorith for Discovering Clusters [p. 229-230] (https://www.aaai.org/Papers/KDD/1996/KDD96-037.pdf)
        # https://stats.stackexchange.com/questions/306829/why-is-dbscan-deterministic
        with h5py.File(folder_path / "ion-run_0006_20221112-1024.hdf5") as old_file:
            order_new, order_old = new_file['centroided/x'][:].argsort(), old_file['centroided/x'][:].argsort()
            shot_new, shot_old = new_file['centroided/trigger nr'][:][order_new], old_file['centroided/trigger nr'][:][order_old]
            x_new, x_old = new_file['centroided/x'][:][order_new], old_file['centroided/x'][:][order_old]
            y_new, y_old = new_file['centroided/y'][:][order_new], old_file['centroided/y'][:][order_old]
            tof_new, tof_old = new_file['centroided/tof'][:][order_new], old_file['centroided/tof'][:][order_old]
            tot_new, tot_old = new_file['centroided/tot max'][:][order_new], old_file['centroided/tot max'][:][order_old]
            tot_avg_new, tot_avg_old = new_file['centroided/tot avg'][:][order_new], old_file['centroided/tot avg'][:][order_old]
            size_new, size_old = new_file['centroided/clustersize'][:][order_new], old_file['centroided/clustersize'][:][order_old]

    
    assertCentroidsAlmostEqual((x_new, y_new, tof_new, tot_new, tot_avg_new, size_new), (x_old, y_old, tof_old, tot_old, tot_avg_old, size_old))

    tmp_file_name.unlink()

def assertCentroidsAlmostEqual(expected, actual):
    np.testing.assert_array_equal(expected[0], actual[0])
    np.testing.assert_array_equal(expected[1], actual[1])
    # The centroids (TOF) can only be almost equal due to errors in floating point arithmetics.
    # A more detailed explaination can be found in the documentation of CentroidCalculator.calculate_centroids_properties
    np.testing.assert_array_almost_equal(expected[2], actual[2], 15)
    np.testing.assert_array_equal(expected[3], actual[3])
    np.testing.assert_array_equal(expected[4], actual[4])
    np.testing.assert_array_equal(expected[5], actual[5])

def test_singleproc_multiproc():
    '''Test if processing with single process and multiple processes yield the same results.'''
    import subprocess
    import hashlib
    files_root = pathlib.Path(__file__).parent / "files"
    in_file = files_root / "ion-run_0006_20221112-1024.raw"
    out_file1 = files_root / "ion-run_0006_20221112-1024_temp1.hdf5"
    out_file2 = files_root / "ion-run_0006_20221112-1024_temp2.hdf5"

    _ = subprocess.run(["pymepix-acq", "post-process", f"-f={in_file}", f"-o={out_file1}"])
    _ = subprocess.run(["pymepix-acq", "post-process", '-n 5', f"-f={in_file}", f"-o={out_file2}"])
    sum_file1 = hashlib.sha1(open(out_file1, 'rb').read()).hexdigest()
    sum_file2 = hashlib.sha1(open(out_file2, 'rb').read()).hexdigest()

    assert sum_file1 == sum_file2

    out_file1.unlink()
    out_file2.unlink()
    

if __name__ == "__main__":
    test_converted_hdf5()
    test_singleproc_multiproc()