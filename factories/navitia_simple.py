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


@clingon.clize(navitia_folder=('n', 'f'), set_version=('s', 'v'))
def factory(data_folder='', port='', navitia_folder='', commit=False, remove=False, set_version=''):
    if commit and DIM.DockerImageManager('', image_name=FINAL_IMAGE_NAME).exists:
        print("image {} already exists".format(FINAL_IMAGE_NAME))
        return 1
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
        with utils.chdir(navitia_folder):
            ffd.execute('deploy_from_scratch')
        if commit:
            dcm.stop()
            if set_version.lower() in ('true', 'yes'):
                version = utils.get_packet_version(navitia_folder)
                dcm.commit(FINAL_IMAGE_NAME, version)
                os.environ['DEBIAN8_SIMPLE_VERSION'] = version
            elif not set_version or set_version.lower() in ('false', 'no'):
                dcm.commit(FINAL_IMAGE_NAME)
            else:
                dcm.commit(FINAL_IMAGE_NAME, set_version)
        if remove:
            dcm.remove_container()
    finally:
        if remove:
            dim.remove_image()
