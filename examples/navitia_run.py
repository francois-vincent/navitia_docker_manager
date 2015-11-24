# encoding: utf-8

"""
This executable will execute a fabric_navitia command on a running container
"""

def absjoin(*p):
    return os.path.abspath(os.path.join(*p))

import os.path
ROOT = absjoin(__file__, '..', '..', '..')
import sys
sys.path[0] = ROOT

from clingon import clingon
clingon.DEBUG = True

from navitia_image_manager import DIM, FFD, utils


@clingon.clize
def factory(cmd, container='navitia_simple', folder='', distrib='debian8'):
    dcm = DIM.DockerContainerManager(container_name=container)
    ffd = FFD.FabricForDocker(dcm, user='navitia', platform='simple', distrib=distrib)
    dcm.start()
    with utils.chdir(folder):
        ffd.execute(cmd)
