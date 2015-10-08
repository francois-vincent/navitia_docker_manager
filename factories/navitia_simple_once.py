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

IMAGE_NAME = 'navitia/debian8_simple'
CONTAINER_NAME = 'navitia_simple'


@clingon.clize
def factory(data_folder, port='8080', source='debian8', folder=''):
    drp = DIM.DockerRunParameters(
        hostname='navitia',
        volumes=(data_folder + ':/srv/ed/data',),
        ports=(port + ':80',)
    )
    df = DIM.DockerFile(
        os.path.join('ssh', 'unsecure_key.pub'),
        os.path.join('factories', CONTAINER_NAME, 'supervisord.conf'),
        os.path.join('factories', source, 'Dockerfile'),
        parameters=drp,
        add_ons=('apache', 'user', 'french', 'postgres', 'sshserver', 'rabbitmq', 'redis', 'supervisor'),
        template_context=dict(user='navitia', password='navitia', home_ssh='/home/navitia/.ssh')
    )
    dim = DIM.DockerImageManager(df, image_name=IMAGE_NAME, parameters=drp)
    dim.build(fail_if_exists=False)
    dcm = dim.create_container(CONTAINER_NAME, start=True)
    ffd = FFD.FabricForDocker(dcm, user='navitia', platform='simple', distrib=source)
    time.sleep(5)
    with utils.chdir(folder):
        ffd.execute('deploy_from_scratch')
