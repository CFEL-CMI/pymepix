import argparse
import logging
import os
import time

import pymepix.config.load_config as cfg
from pymepix.post_processing import run_post_processing
from pymepix.pymepix_connection import PymepixConnection


from tornado.web import Application, RequestHandler
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


