# encoding: utf-8


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

INTER_IMAGE_NAME = 'navitia/debian8_inter'
FINAL_IMAGE_NAME = 'navitia/debian8_simple'
CONTAINER_NAME = 'navitia_simple'


@clingon.clize
def factory(data_folder, port='8080', packages=''):
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
    dim = DIM.DockerImageManager(df, image_name=INTER_IMAGE_NAME, parameters=drp)
    dim.build(fail_if_exists=False)
    dcm = dim.create_container(CONTAINER_NAME, start=True, fail_if_exists=False)
    ffd = FFD.FabricForDocker(dcm, user='navitia', platform='simple', distrib='debian8')
    time.sleep(5)
    with utils.chdir(packages):
        ffd.execute('deploy_from_scratch')
        dcm.stop().commit(FINAL_IMAGE_NAME)
