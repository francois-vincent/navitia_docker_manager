# encoding: utf-8

"""
This executable will install Navitia2 on an existing prepared debian8 image.
The resulting container can be commited with a default name.
"""


def absjoin(*p):
    return os.path.abspath(os.path.join(*p))

import os.path
ROOT = absjoin(__file__, '..', '..', '..')
import sys
import time
sys.path[0] = ROOT

from clingon import clingon
clingon.DEBUG = True

from navitia_docker_manager import DIM, FFD, utils

Dockerfile = """
FROM navitia/debian8:latest

"""

FINAL_IMAGE_NAME = 'navitia/debian8_simple'
CONTAINER_NAME = 'navitia_simple'


@clingon.clize
def factory(data_folder='', port='', folder='', commit=False):
    if DIM.DockerImageManager('', image_name=FINAL_IMAGE_NAME).exists:
        print("image {} already exists".format(FINAL_IMAGE_NAME))
        return
    drp = DIM.DockerRunParameters(
        hostname='navitia',
        volumes=(data_folder + ':/srv/ed/data',),
        ports=(port + ':80',)
    )
    df = DIM.DockerFile(
        Dockerfile=Dockerfile,
        parameters=drp
    )
    dim = DIM.DockerImageManager(df, parameters=drp)
    dim.build()
    dcm = dim.create_container(CONTAINER_NAME, start=True)
    ffd = FFD.FabricForDocker(dcm, user='navitia', platform='simple', distrib='debian8')
    time.sleep(5)
    with utils.chdir(folder):
        ffd.execute('deploy_from_scratch')
    if commit:
        dcm.stop().commit(FINAL_IMAGE_NAME).remove_container()
        dim.remove_image()
