# encoding: utf-8

"""
This executable will install Navitia2 on an existing prepared debian8 image.
The resulting container can be commited with a default name.
This executable can also be used to test the deploy_from_scratch command on
a prepared docker container.
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


@clingon.clize(set_version=('s', 'v'))
def factory(data_folder='', port='', packet_folder='', commit=False, remove=False, set_version=False):
    if commit and DIM.DockerImageManager('', image_name=FINAL_IMAGE_NAME).exists:
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
    try:
        dim.build()
        dcm = dim.create_container(CONTAINER_NAME, start=True, if_exist='remove')
        ffd = FFD.FabricForDocker(dcm, user='navitia', platform='simple', distrib='debian8')
        time.sleep(5)
        with utils.chdir(packet_folder):
            ffd.execute('deploy_from_scratch')
        if commit:
            image_name = FINAL_IMAGE_NAME
            if set_version:
                image_name += ':' + utils.get_packet_version()
            dcm.stop().commit(image_name)
        if remove:
            dcm.remove_container()
    finally:
        if commit or remove:
            dim.remove_image()
