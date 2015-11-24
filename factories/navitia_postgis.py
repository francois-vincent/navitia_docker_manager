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

from navitia_image_manager import DIM


IMAGE_NAME = 'navitia/postgis'
CONTAINER_NAME = 'postgis'


@clingon.clize
def factory(commit=False):
    drp = DIM.DockerRunParameters(
        ports=('5432:5432',)
    )
    df = DIM.DockerFile(
        'factories/postgres/Dockerfile',
        'factories/postgres/supervisord.conf',
        parameters=drp,
        add_ons=('supervisor', ),
    )
    dim = DIM.DockerImageManager(df, image_name=IMAGE_NAME, parameters=drp)
    dim.build()
    dcm = dim.create_container(CONTAINER_NAME, start=True, if_exist='remove')
    time.sleep(3)
    dcm.exec_container('sudo -u postgres psql -c "CREATE USER cities PASSWORD \'cities\'"')
    dcm.exec_container('sudo -u postgres createdb cities')
    if commit:
        dcm.stop()
        dcm.commit(IMAGE_NAME)
        dcm.remove_container()
