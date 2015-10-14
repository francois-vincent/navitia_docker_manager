# encoding: utf-8

"""
This executable will build a docker image for Kirin
"""


def absjoin(*p):
    return os.path.abspath(os.path.join(*p))

import os.path
ROOT = absjoin(__file__, '..', '..', '..')
import sys
sys.path[0] = ROOT

from clingon import clingon
clingon.DEBUG = True

from navitia_docker_manager import DIM, FFD, utils


KRIRIN_ROOT = [p for p in sys.path if p.endswith('kirin')][0]
IMAGE_NAME = 'navitia/kirin'


@clingon.clize
def factory(version, commit=False, port='80'):
    drp = DIM.DockerRunParameters(
        hostname='kirin',
        ports=(port + ':9090',)
    )
    df = DIM.DockerFile(
        os.path.join(KRIRIN_ROOT, 'Dockerfile'),
        parameters=drp
    )
    dim = DIM.DockerImageManager(df, image_name=IMAGE_NAME, parameters=drp)
    dim.build()
