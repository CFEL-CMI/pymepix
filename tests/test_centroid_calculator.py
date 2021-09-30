import numpy as np

from pymepix.processing.logic.centroid_calculator import CentroidCalculator

"""
The purpose of this test is the validation of the implemented calculation of centroids. The implemented 
centroiding consists of slightly more functionality than DBSCAN + calculation of centroids. In addition 
the data is split into chunks to optimise the performance of DBSCAN. The following tests have the purpose to
verify this splitting procedure.
"""

def test_calculate_centroid_properties_1():
    centroid_calculator = CentroidCalculator()
    shot = np.array([1, 1, 1, 1, 1])
    x = np.array([0, 0, 1, 0, -1])
    y = np.array([0, 1, 0, -1, 0])
    tof = np.array([1, 1, 1, 1, 1])
    tot = np.array([1, 1, 1, 1, 1])
    label = np.array([0, 0, 0, 0, 0])
    # cluster_shot, cluster_x, cluster_y, cluster_tof, cluster_totAvg, cluster_totMax, cluster_size
    expected_result = [1], [0], [0], [1], [1], [1], [5]
    assertCentroidsEqual(expected_result, centroid_calculator.calculate_centroids_properties(shot, x, y, tof, tot, label))

def test_calculate_centroid_properties_2():
    centroid_calculator = CentroidCalculator()
    shot = np.array([1, 1, 1, 1, 1, 2, 2, 2, 2, 2])
    x = np.array([0, 0, 1, 0, -1, 1, 1, 2, 1, 0])
    y = np.array([0, 1, 0, -1, 0, 1, 2, 1, 0, 1])
    tof = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    tot = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    label = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    # cluster_shot, cluster_x, cluster_y, cluster_tof, cluster_totAvg, cluster_totMax, cluster_size
    expected_result = [1, 2], [0, 1], [0, 1], [1, 1], [1, 1], [1, 1], [5, 5]
    assertCentroidsEqual(expected_result, centroid_calculator.calculate_centroids_properties(shot, x, y, tof, tot, label))

def test_calculate_centroid_properties_3():
    centroid_calculator = CentroidCalculator()
    shot = np.array([1, 1, 1, 1, 1, 2, 2, 2, 2, 2])
    x = np.array([0, 0, 1, 0, -1, 1, 1, 2, 1, 0])
    y = np.array([0, 1, 0, -1, 0, 1, 2, 1, 0, 1])
    tof = np.array([0, 0, 0, 0, 1, 0, 0, 0, 0, 1])
    tot = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    label = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    # cluster_shot, cluster_x, cluster_y, cluster_tof, cluster_totAvg, cluster_totMax, cluster_size
    expected_result = [1, 2], [0, 1], [0, 1], [1/5, 1/5], [1, 1], [1, 1], [5, 5]
    assertCentroidsEqual(expected_result, centroid_calculator.calculate_centroids_properties(shot, x, y, tof, tot, label))

def test_divide_into_chunks_1():
    centroid_calculator = CentroidCalculator()

    factor = 6_500

    data = [3, 1, 2, 4, 5, 6]

    shot, x, y, tof, tot = __create_timepix_data(data, factor)

    chunks = centroid_calculator._CentroidCalculator__divide_into_chunks(shot, x, y, tof, tot)

    for elem in data:
        for arr in chunks[elem - 1]:
            assert factor == len(arr)

def test_divide_into_chunks_2():
    centroid_calculator = CentroidCalculator()

    factor = 1
    shot, x, y, tof, tot = __create_timepix_data([1, 2], factor)

    np.testing.assert_array_equal([1, 2],
        centroid_calculator._CentroidCalculator__divide_into_chunks(shot, x, y, tof, tot)[0][1])

def test_divide_into_chunks_3():
    centroid_calculator = CentroidCalculator()

    factor = 1
    shot, x, y, tof, tot = __create_timepix_data([1, 2], factor)

    chunks = centroid_calculator._CentroidCalculator__divide_into_chunks(shot, x, y, tof, tot)
    sum = 0
    found_triggers = []
    for chunk in chunks:
        sum += chunk[0].shape[0]
        assert 0 == chunk[0].shape[0] % factor
        found_triggers + np.unique(chunk[0]).tolist()
    assert shot.shape[0] == sum
    assert np.all(np.unique(found_triggers, return_counts=True)[1] == 1)

def test_divide_into_chunks_4():
    centroid_calculator = CentroidCalculator()

    factor = 2_500

    data = [3, 1, 2, 4, 5, 6, 4, 4, 4]

    shot, x, y, tof, tot = __create_timepix_data(data, factor)

    chunks = centroid_calculator._CentroidCalculator__divide_into_chunks(shot, x, y, tof, tot)
    sum = 0
    found_triggers = []
    for chunk in chunks:
        sum += chunk[0].shape[0]
        assert 0 == chunk[0].shape[0] % factor
        found_triggers + np.unique(chunk[0]).tolist()
    assert shot.shape[0] == sum
    assert np.all(np.unique(found_triggers, return_counts=True)[1] == 1)

def test_divide_into_chunks_5():
    centroid_calculator = CentroidCalculator()

    factor = 3_500

    data = [3, 1, 2, 4, 5, 6, 1, 1]

    shot, x, y, tof, tot = __create_timepix_data(data, factor)

    chunks = centroid_calculator._CentroidCalculator__divide_into_chunks(shot, x, y, tof, tot)
    sum = 0
    found_triggers = []
    for chunk in chunks:
        sum += chunk[0].shape[0]
        assert 0 == chunk[0].shape[0] % factor
        found_triggers += np.unique(chunk[0]).tolist()
    assert shot.shape[0] == sum
    assert np.all(np.unique(found_triggers, return_counts=True)[1] == 1)

def test_divide_into_chunks_6():
    centroid_calculator = CentroidCalculator()

    factor = 1

    data = range(0, 10_000)
    shot, x, y, tof, tot = __create_timepix_data(data, factor)

    chunks = centroid_calculator._CentroidCalculator__divide_into_chunks(shot, x, y, tof, tot)
    sum = 0
    found_triggers = []
    for chunk in chunks:
        sum += chunk[0].shape[0]
        assert 0 == chunk[0].shape[0] % factor
        found_triggers + np.unique(chunk[0]).tolist()
    assert shot.shape[0] == sum
    assert np.all(np.unique(found_triggers, return_counts=True)[1] == 1)

def test_process():
    centroid_calculator = CentroidCalculator()
    shot = np.array([1, 1, 1, 1, 1, 1] + [2, 2, 2, 2, 2, 2])
    x = np.concatenate(([0, 0, 0, 1, 0, -1], np.array([1, 1, 1, 2, 1, 0]) + 5))
    y = np.concatenate(([0, 0, 1, 0, -1, 0], np.array([1, 1, 2, 1, 0, 1]) + 5))
    tof = np.array([0, 0, 0, 0, 0, 0] + [0, 0, 0, 0, 0, 0])
    tot = np.array([1, 1, 1, 1, 1, 1] + [1, 1, 1, 1, 1, 1])

    expected_result = [1, 2], [0, 6], [0, 6], [0, 0], [1, 1], [1, 1], [6, 6]
    assertCentroidsEqual(expected_result, centroid_calculator.process((shot, x, y, tof, tot)))

def assertCentroidsEqual(expected, actual):
    for i in range(len(expected)):
        np.testing.assert_array_equal(expected[i], actual[i])

def __create_timepix_data(data, factor):
    shot = np.repeat(data, factor)
    x = np.repeat(data, factor)
    y = np.repeat(data, factor)
    tof = np.repeat(data, factor)
    tot = np.repeat(data, factor)
    return shot, x, y, tof, tot
