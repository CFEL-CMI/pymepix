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

""" Main module for pymepix """

import os
import argparse
import logging
import time

import pymepix.config.load_config as cfg
from pymepix.post_processing import run_post_processing

from pymepix.pymepix_connection import PollBufferEmpty, PymepixConnection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def connect_timepix(args):
    if not os.path.exists(args.output):
        # Connect to SPIDR
        pymepix = PymepixConnection(spidr_address=(args.ip, args.port))
        # If there are no valid timepix detected then quit()
        if len(pymepix) == 0:
            logging.error(
                "-------ERROR: SPIDR FOUND BUT NO VALID TIMEPIX DEVICE DETECTED ---------- "
            )
            quit()
        if args.spx:
            logging.info("Opening Sophy file {}".format(args.spx))
            pymepix[0].loadConfig(args.spx)

        # Switch to TOF mode if set
        if args.decode and args.tof:
            pymepix[0].acquisition.enableEvents = True

        # Set the bias voltage
        pymepix.biasVoltage = args.bias

        # self._timepix._spidr.resetTimers()
        # self._timepix._spidr.restartTimers()
        # time.sleep(1)  # give camera time to reset timers

        # Start acquisition
        pymepix.start()

        pymepix._timepix_devices[0].start_recording(args.output)
        time.sleep(args.time)
        pymepix._timepix_devices[0].stop_recording()

        pymepix.stop()

    else:
        logging.info(
            f"Outputfile {args.output} already exists. Please make sure the specified file does not exist."
        )


def post_process(args):
    run_post_processing(
        args.file.name,
        args.output_file,
        args.number_of_processes,
        args.timewalk_file,
        args.cent_timewalk_file,
    )


def main():

    parser = argparse.ArgumentParser(description="Timepix acquisition script")
    subparsers = parser.add_subparsers(
        description="Processing type",
        help="Select which type of process should be executed",
        required=True,
        dest="command",
    )

    parser_connect = subparsers.add_parser(
        "connect", help="Connect to TimePix camera and acquire data."
    )
    parser_connect.set_defaults(func=connect_timepix)

    parser_connect.add_argument(
        "-i",
        "--ip",
        dest="ip",
        type=str,
        default=cfg.default_cfg["timepix"]["tpx_ip"],
        help="IP address of Timepix",
    )
    parser_connect.add_argument(
        "-p",
        "--port",
        dest="port",
        type=int,
        default=50000,
        help="TCP port to use for the connection",
    )
    parser_connect.add_argument(
        "-s", "--spx", dest="spx", type=str, help="Sophy config file to load"
    )
    parser_connect.add_argument(
        "-v",
        "--bias",
        dest="bias",
        type=float,
        default=50,
        help="Bias voltage in Volts",
    )
    parser_connect.add_argument(
        "-t",
        "--time",
        dest="time",
        type=float,
        help="Acquisition time in seconds",
        required=True,
    )
    parser_connect.add_argument(
        "-o",
        "--output",
        dest="output",
        type=str,
        help="output filename prefix",
        required=True,
    )
    parser_connect.add_argument(
        "-d",
        "--decode",
        dest="decode",
        type=bool,
        help="Store decoded values instead",
        default=False,
    )
    parser_connect.add_argument(
        "-T",
        "--tof",
        dest="tof",
        type=bool,
        help="Compute TOF if decode is enabled",
        default=False,
    )
    parser_connect.add_argument(
        "-c",
        "--config",
        dest="cfg",
        type=str,
        default="default.yaml",
        help="Config file",
    )

    parser_post_process = subparsers.add_parser(
        "post-process", help="Perform post-processing with a acquired raw data file."
    )
    parser_post_process.set_defaults(func=post_process)
    parser_post_process.add_argument(
        "-f",
        "--file",
        dest="file",
        type=argparse.FileType("rb"),
        help="Raw data file for postprocessing",
        required=True,
    )
    parser_post_process.add_argument(
        "-o",
        "--output_file",
        dest="output_file",
        type=str,
        help="Filename where the processed data is stored",
        required=True,
    )
    parser_post_process.add_argument(
        "-t",
        "--timewalk_file",
        dest="timewalk_file",
        type=argparse.FileType("rb"),
        help="File containing the time walk information",
    )
    parser_post_process.add_argument(
        "-c",
        "--cent_timewalk_file",
        dest="cent_timewalk_file",
        type=argparse.FileType("rb"),
        help="File containing the centroided time walk information",
    )
    parser_post_process.add_argument(
        "-n",
        "--number_of_processes",
        dest="number_of_processes",
        type=int,
        default=-1,
        help="The number of processes used for the centroiding (default: None which ensures all existing system cores are used')",
    )

    args = parser.parse_args()

    cfg.load_config(args.cfg)
    args.func(args)

if __name__ == "__main__":
    main()
