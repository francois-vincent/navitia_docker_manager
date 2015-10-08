# encoding: utf-8


def absjoin(*p):
    return os.path.abspath(os.path.join(*p))

import os
ROOT = absjoin(__file__, '..', '..', '..')
import sys
sys.path[0] = ROOT

from clingon import clingon
clingon.DEBUG = True

from image_manager import DIM, FFD

CONTAINER_NAME = 'navitia_simple'


@clingon.clize
def factory(cmd, packages='', source='debian8'):
    dcm = DIM.DockerContainerManager(container_name=CONTAINER_NAME)
    ffd = FFD.FabricForDocker(dcm, user='navitia', platform='simple', distrib=source)
    dcm.start()
    if packages:
        os.chdir(os.path.abspath(os.path.expanduser(packages)))
    ffd.execute(cmd)
