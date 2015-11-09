# encoding: utf-8

"""
FFD: Fabric for Docker
A set of convenience classes to run fabric scripts on docker containers
"""

from __future__ import unicode_literals, print_function
from importlib import import_module

from fabric import api, context_managers, tasks

import fabfile


class FabricForDocker(object):

    def __init__(self, container, **kwargs):
        self.container = container
        self.log = container.log
        self.__dict__.update(kwargs)
        if hasattr(self, 'platform'):
            self.set_platform()

    def set_platform(self):
        module = import_module('navitia_docker_manager.platforms.' + self.platform)
        api.env.distrib = self.distrib
        getattr(module, self.platform)(self.get_host())
        return self

    def get_host(self):
        return "{}@{}".format(self.user, self.container.inspect())

    def execute(self, cmd, *args, **kwargs):
        """
        Executes a fabric-navitia command
        :param cmd: the fabric command
        :param *args are passed to api.execute
        :param **kwargs are passed to api.execute, except 'let' which is
               passed to settings
        """
        let = kwargs.pop('let', {})
        self.log.info("Container '{}' exec fabric command {}({}, {})".format(
            self.container.container_name, cmd, args, kwargs))
        if '.' in cmd:
            command = fabfile
            for compo in cmd.split('.'):
                command = getattr(command, compo, command)
        else:
            command = getattr(fabfile, cmd, None)
        if not isinstance(command, tasks.WrappedCallableTask):
            raise RuntimeError("Unknown Fabric command %s" % cmd)
        with context_managers.settings(context_managers.hide('stdout'), **let):
            api.execute(command, *args, **kwargs)
        return self
