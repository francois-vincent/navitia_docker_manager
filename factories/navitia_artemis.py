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

# mapped volumes
VOLUME /srv/ed/data

COPY {supervisord_conf} /etc/supervisor/conf.d/supervisord.conf
"""

FINAL_IMAGE_NAME = 'navitia/debian8_artemis'
CONTAINER_NAME = 'artemis'


@clingon.clize(navitia_folder=('n', 'f'), set_version=('s', 'v'))
def factory(data_folder='', port='', navitia_folder='', commit=False, remove=False, set_version='', tag=False):
    if commit:
        if set_version.lower() in ('true', 'yes'):
            version = utils.get_packet_version(navitia_folder)
        elif not set_version or set_version.lower() in ('false', 'no'):
            version = None
        else:
            version = set_version
        image_name = "{}:{}".format(FINAL_IMAGE_NAME, version)
        if DIM.DockerImageManager('', image_name=image_name).exists:
            print("image {} already exists".format(image_name))
            return 1
    drp = DIM.DockerRunParameters(
        hostname='navitia',
        volumes=(data_folder + ':/srv/ed/data',),
        ports=(port + ':80',)
    )
    ffd = FFD.FabricForDocker(None, user='navitia', platform='artemis', distrib='debian8')
    df = DIM.DockerFile(
        os.path.join('factories', CONTAINER_NAME, 'supervisord.conf.jinja'),
        Dockerfile=Dockerfile,
        parameters=drp,
        template_context=dict(krakens=list(ffd.get_env.instances))
    )
    dim = DIM.DockerImageManager(df, parameters=drp)
    try:
        dim.build()
        dcm = dim.create_container(CONTAINER_NAME, start=True, if_exist='remove')
        ffd.set_platform(dcm)
        time.sleep(5)
        with utils.chdir(navitia_folder):
            ffd.execute('deploy_from_scratch')
        if commit:
            dcm.stop()
            if version:
                dcm.commit(FINAL_IMAGE_NAME, version, tag)
            else:
                dcm.commit(FINAL_IMAGE_NAME)
        if remove:
            dcm.remove_container()
    finally:
        if remove:
            dim.remove_image()
