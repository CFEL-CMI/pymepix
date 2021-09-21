import numpy as np
import h5py

from pymepix.processing.rawfilesampler import RawFileSampler


def test_converted_hdf5():
    tmp_file_name = "run_0685_20191217-1533-new.hdf5"
    file_sampler = RawFileSampler("run_0685_20191217-1533.raw", tmp_file_name)
    file_sampler.run()

    with h5py.File(tmp_file_name) as new_file:
        print(new_file['centroided'].keys())
        print(len(new_file['raw/x'][:]))
        print(len(new_file['centroided/x'][:]))

        # The RawConverter has been slightly adjusted for this comparison. The pixels were sorted by the shot number to match the order which is required
        # for the processing in chunks. This is required as the DBSCAN algorithm can be non-deterministic regarding the order in some rare scenarios.
        # Martin Ester, Hans-Peter Kriegel, Jiirg Sander, Xiaowei Xu: A Density Based Algorith for Discovering Clusters [p. 229-230] (https://www.aaai.org/Papers/KDD/1996/KDD96-037.pdf)
        # https://stats.stackexchange.com/questions/306829/why-is-dbscan-deterministic
        with h5py.File('run_0685_20191217-1533.hdf5') as old_file:
            order_new, order_old = new_file['centroided/x'][:].argsort(), old_file['centroided/x'][:].argsort()
            shot_new, shot_old = new_file['centroided/trigger nr'][:][order_new], old_file['centroided/trigger nr'][:][order_old]
            x_new, x_old = new_file['centroided/x'][:][order_new], old_file['centroided/x'][:][order_old]
            y_new, y_old = new_file['centroided/y'][:][order_new], old_file['centroided/y'][:][order_old]
            tof_new, tof_old = new_file['centroided/tof'][:][order_new], old_file['centroided/tof'][:][order_old]
            tot_new, tot_old = new_file['centroided/tot max'][:][order_new], old_file['centroided/tot max'][:][order_old]
            tot_avg_new, tot_avg_old = new_file['centroided/tot avg'][:][order_new], old_file['centroided/tot avg'][:][order_old]
            size_new, size_old = new_file['centroided/clustersize'][:][order_new], old_file['centroided/clustersize'][:][order_old]

    
    assertCentroidsAlmostEqual((x_new, y_new, tof_new, tot_new, tot_avg_new, size_new), (x_old, y_old, tof_old, tot_old, tot_avg_old, size_old))

def assertCentroidsAlmostEqual(expected, actual):
    np.testing.assert_array_equal(expected[0], actual[0])
    np.testing.assert_array_equal(expected[1], actual[1])
    # The centroids (TOF) can only be almost equal due to errors in floating point arithmetics.
    # A more detailed explaination can be found in the documentation of CentroidCalculator.calculate_centroids_properties
    np.testing.assert_array_almost_equal(expected[2], actual[2], 15)
    np.testing.assert_array_equal(expected[3], actual[3])
    np.testing.assert_array_equal(expected[4], actual[4])
    np.testing.assert_array_equal(expected[5], actual[5])