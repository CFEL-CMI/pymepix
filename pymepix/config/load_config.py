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
# global import for config file

from pathlib import Path, PurePath
import sys

import yaml
import random

global default_cfg

# print("\033[93m" + "USB trainID not started" + "\033[0m")


def load_config(config_name = "default.yaml"):
    global default_cfg
    cfg_file = Path((PurePath(__file__).parent.parent), 'config_files', config_name)
    if Path(cfg_file).is_file():
        with open(cfg_file, "r") as f:
            default_cfg = yaml.safe_load(f)
    else:
        print(f"Cannot find config {cfg_file} file")
        sys.exit()
    # choose random port for ZMQ connections
    default_cfg['zmq_port'] = random.randint(2000, 65000)

load_config()
