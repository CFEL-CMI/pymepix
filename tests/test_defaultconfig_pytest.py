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

"""
Module to test mendatory default configuration
"""
import os
import yaml
import os

import pymepix.config.load_config as cfg


def read_yaml(file_path: str):
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def test_file_exists():
    cfg_file = os.path.join(os.path.dirname(cfg.__file__), "default.yaml")
    read_yaml(cfg_file)


def test_tpx_content():
    assert cfg.default_cfg["timepix"]["pc_ip"] in ["192.168.1.1", "192.168.100.1"]
    assert cfg.default_cfg["timepix"]["tpx_ip"] in ["192.168.1.10", "192.168.100.10"]
    assert "trainID" in cfg.default_cfg
    assert isinstance(cfg.default_cfg["trainID"]["connected"], bool)
