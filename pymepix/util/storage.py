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

"""Useful functions to store data"""
import numpy as np


def open_output_file(filename, ext, index=0):
    import os, logging
    file_format = '{}_{:06d}.{}'
    raw_filename = file_format.format(filename, index, ext)
    while os.path.isfile(raw_filename):
        index += 1
        raw_filename = file_format.format(filename, index, ext)
    logging.info('Opening output file {}'.format(filename))

    return open(raw_filename, 'wb')


def store_raw(f, data):
    raw, longtime = data
    f.write(raw.tostring())


def store_toa(f, data):
    x, y, toa, tot = data

    np.save(f, x)
    np.save(f, y)
    np.save(f, toa)
    np.save(f, tot)


def store_tof(f, data):
    counter, x, y, tof, tot = data

    np.save(f, counter)
    np.save(f, x)
    np.save(f, y)
    np.save(f, tof)
    np.save(f, tot)


def store_centroid(f, data):
    cluster_shot, cluster_x, cluster_y, cluster_tof, cluster_tot = data

    np.save(f, cluster_shot)
    np.save(f, cluster_x)
    np.save(f, cluster_y)
    np.save(f, cluster_tof)
    np.save(f, cluster_tot)
