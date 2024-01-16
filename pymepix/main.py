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
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program.
# If not, see <https://www.gnu.org/licenses/>.

""" Main module for pymepix """

import argparse
import logging
import os
import time

import re

import pymepix.config.load_config as cfg
from pymepix.post_processing import run_post_processing
from pymepix.pymepix_connection import PymepixConnection

from pymepix.processing.acquisition import PixelPipeline, CentroidPipeline

from tornado.web import Application, RequestHandler, HTTPError
import json

#from .api.api import make_app
from tornado.ioloop import IOLoop


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def connect_timepix(args):
    if not os.path.exists(args.output):
        # Connect to camera
        pymepix = PymepixConnection(spidr_address=(args.ip, args.port),
                                    camera_generation=args.cam_gen)
        # If there are no valid timepix detected then quit()
        if len(pymepix) == 0:
            logging.error(
                "-------ERROR: SPIDR FOUND BUT NO VALID TIMEPIX DEVICE DETECTED ---------- "
            )
            quit()
        if args.spx:
            logging.info(f"Opening Sophy file {args.spx}")
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
        args.cam_gen,
    )


def is_jsonable(x):
    try:
        json.dumps(x)
        return True
    except (TypeError, OverflowError):
        return False

def get_path(ref, path):
    try:
        for tkn in path:
            if tkn[0] != '[':
                ref = getattr(ref, tkn)
            else:
                ref = ref[int(tkn[1:-1])]
    except:
        raise HTTPError(400, u"Bad request")
    return ref

class RootHandler(RequestHandler):
    def get(self):
        self.write({'message': 'Online'})


class TPXpropertyHandler(RequestHandler):
    def get(self):

        global pymepix_connection_obj

        arguments = self.get_arguments('param_name')

        tkns = re.findall(r"[\w']+|\[\d+\]", arguments[0])

        ref = pymepix_connection_obj
        ref = get_path(ref, tkns)

        if is_jsonable(ref):
            self.write({arguments[0]: ref})
        else:
            raise HTTPError(405, u"Parameter value is not JSON serializable")


    def post(self):
        global pymepix_connection_obj

        try:
            data = json.loads(self.request.body)
        except:
            raise HTTPError(400, u"Bad request")

        for key, val in data.items():
            ref = pymepix_connection_obj
            tkns = re.findall(r"[\w']+|\[\d+\]", key)
            ref = get_path(ref, tkns[:-1])
            if tkns[-1][0] != '[':
                setattr(ref, tkns[-1], val)
            else:
                ref[int(tkns[-1][1:-1])] = val

        self.write(data)

class TPXmethodHandler(RequestHandler):
    def post(self):
        global pymepix_connection_obj
        try:
            data = json.loads(self.request.body)
        except:
            raise HTTPError(400, u"Bad request")

        try:
            func_name = data['func_name']

            tkns = re.findall(r"[\w']+|\[\d+\]", func_name)

            ref = pymepix_connection_obj
            ref = get_path(ref, tkns)

            data.pop('func_name')
            res = ref(**data)
            if is_jsonable(res):
                self.write({'result': res})
            else:
                self.write({'result': 'Result is not JSON serializable'})
        except:
            raise HTTPError(400, u"Bad request")

class PostprocessHandler(RequestHandler):
    def post(self):
        try:
            data = json.loads(self.request.body)
        except:
            raise HTTPError(400, u"Bad request")

        try:
            run_post_processing(**data)
        except:
            raise HTTPError(400, u"Bad request")


def make_app():
    urls = [
        ("/", RootHandler),
        (r"/tpxproperty", TPXpropertyHandler),
        (r"/tpxmethod", TPXmethodHandler),
        (r"/postprocess", PostprocessHandler)
    ]
    return Application(urls, debug=True)


def start_api(args):
    global pymepix_connection_obj

    if args.pixel_pipeline == 'centroid':
        pipeline_class = CentroidPipeline
    else:
        pipeline_class = PixelPipeline

    pymepix_connection_obj = PymepixConnection(spidr_address=(args.ip, args.port),\
                                               camera_generation=args.cam_gen,
                                               pipeline_class=pipeline_class)


    if len(pymepix_connection_obj) == 0:
        logging.error(
            "-------ERROR: SPIDR FOUND BUT NO VALID TIMEPIX DEVICE DETECTED ---------- "
        )
        quit()
    if args.spx:
        logging.info(f"Opening Sophy file {args.spx}")
        pymepix_connection_obj[0].loadConfig(args.spx)

    # Switch to TOF mode if set
    if args.decode and args.tof:
        pymepix_connection_obj[0].acquisition.enableEvents = True

    # Set the bias voltage
    pymepix_connection_obj.biasVoltage = args.bias

    app = make_app()
    app.listen(args.api_port)
    IOLoop.instance().start()


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

    parser_connect.add_argument(
        "-g",
        "--cam_gen",
        dest="cam_gen",
        type=int,
        default=3,
        help="Camera generation",
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
        default=1,
        help="The number of processes used for the centroiding (default: 1 => parallel processing disabled')",
    )
    
    parser_post_process.add_argument(
        "--config",
        dest="cfg",
        type=str,
        default="default.yaml",
        help="Config file",
    )

    parser_post_process.add_argument(
        "-g",
        "--cam_gen",
        dest="cam_gen",
        type=int,
        default=3,
        help="Camera generation",
    )


    parser_api_service = subparsers.add_parser(
        "api-service", help="start api service."
    )

    parser_api_service.set_defaults(func=start_api)

    parser_api_service.add_argument(
        "-i",
        "--ip",
        dest="ip",
        type=str,
        default=cfg.default_cfg["timepix"]["tpx_ip"],
        help="IP address of Timepix",
    )

    parser_api_service.add_argument(
        "-p",
        "--port",
        dest="port",
        type=int,
        default=50000,
        help="TCP port to use for the connection",
    )

    parser_api_service.add_argument(
        "-api_p",
        "--api_port",
        dest="api_port",
        type=int,
        default=8080,
        help="TCP port to use for API",
    )

    parser_api_service.add_argument(
        "--config",
        dest="cfg",
        type=str,
        default="default.yaml",
        help="Config file",
    )

    parser_api_service.add_argument(
        "-s", "--spx", dest="spx", type=str, help="Sophy config file to load"
    )

    parser_api_service.add_argument(
        "-d",
        "--decode",
        dest="decode",
        type=bool,
        help="Store decoded values instead",
        default=False,
    )
    parser_api_service.add_argument(
        "-T",
        "--tof",
        dest="tof",
        type=bool,
        help="Compute TOF if decode is enabled",
        default=False,
    )

    parser_api_service.add_argument(
        "-v",
        "--bias",
        dest="bias",
        type=float,
        default=50,
        help="Bias voltage in Volts",
    )

    parser_api_service.add_argument(
        "-g",
        "--cam_gen",
        dest="cam_gen",
        type=int,
        default=3,
        help="Camera generation",
    )

    parser_api_service.add_argument(
        "-pl",
        "--pipeline",
        dest="pixel_pipeline",
        type=str,
        default='pixel',
        help="Processing pipeline, options: centroid, pixel. Default - pixel",
    )


    args = parser.parse_args()
    print(args)

    cfg.load_config(args.cfg)
    args.func(args)

if __name__ == "__main__":
    main()
