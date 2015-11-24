# encoding: utf-8

"""
This executable will build a debian8 prepared image for Navitia2,
including: apache2, ssh, redis, postgresql, rabbitmq, supervisord
and a user named navitia.
"""


def absjoin(*p):
    return os.path.abspath(os.path.join(*p))

import os.path
ROOT = absjoin(__file__, '..', '..', '..')
import sys
sys.path[0] = ROOT

from clingon import clingon
clingon.DEBUG = True

from navitia_image_manager import DIM

IMAGE_NAME = 'navitia/debian8'
CONTAINER_NAME = 'navitia_simple'


@clingon.clize
def factory(source='debian8'):
    df = DIM.DockerFile(
        os.path.join('factories', source, 'Dockerfile'),
        os.path.join('factories', source, 'supervisord.conf'),
        os.path.join('ssh', 'unsecure_key.pub'),
        add_ons=('apache', 'user', 'french', 'postgres', 'sshserver', 'rabbitmq', 'redis', 'supervisor'),
        template_context=dict(user='navitia', password='navitia', home_ssh='/home/navitia/.ssh')
    )
    dim = DIM.DockerImageManager(df, image_name=IMAGE_NAME)
    dim.build()
