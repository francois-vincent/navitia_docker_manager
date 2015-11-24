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

from navitia_image_manager import DIM, FFD, utils

Dockerfile = """
FROM navitia/debian8:latest

RUN pip install pytest

RUN mkdir -m 777 -p /srv/ed/data

COPY {supervisord_conf} /etc/supervisor/conf.d/supervisord.conf
COPY {kraken_service_wrapper} /usr/local/bin/kraken_service_wrapper
RUN chmod a+x /usr/local/bin/kraken_service_wrapper
"""

FINAL_IMAGE_NAME = 'navitia/debian8_artemis'
CONTAINER_NAME = 'artemis'


@clingon.clize(artemis_source=('as',), artemis_data=('ad',), set_version=('v',))
def factory(navitia_packages='',
            port='',
            artemis_source='',
            artemis_data='',
            commit=False,
            remove=False,
            set_version='',
            tag=False):
    if commit:
        if set_version.lower() in ('true', 'yes'):
            version = utils.get_packet_version(navitia_packages)
        elif not set_version or set_version.lower() in ('false', 'no'):
            version = None
        else:
            version = set_version
        image_name = "{}:{}".format(FINAL_IMAGE_NAME, version)
        if DIM.DockerImageManager('', image_name=image_name).exists:
            print("image {} already exists".format(image_name))
            return 1
    drp = DIM.DockerRunParameters(
        hostname='artemis',
        volumes=(artemis_data + ':/artemis/data',
                 artemis_source + ':/artemis/source'),
        ports=(port + ':80', '9002:9001')
    )
    ffd = FFD.FabricForDocker(None, user='navitia', platform='artemis', distrib='debian8')
    df = DIM.DockerFile(
        os.path.join('factories', CONTAINER_NAME, 'supervisord.conf.jinja'),
        os.path.join('factories', CONTAINER_NAME, 'kraken_service_wrapper'),
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
        with utils.chdir(navitia_packages):
            ffd.execute('deploy_from_scratch')
        if commit:
            dcm.stop()
            if version:
                dcm.commit(FINAL_IMAGE_NAME, version)
                if tag:
                    dcm.tag(FINAL_IMAGE_NAME, version)
            else:
                dcm.commit(FINAL_IMAGE_NAME)
        print("Run this image with:")
        print(dim.print_command(FINAL_IMAGE_NAME, CONTAINER_NAME))
        if remove:
            dcm.remove_container()
    finally:
        if remove:
            dim.remove_image()
