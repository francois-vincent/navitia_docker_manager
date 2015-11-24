# encoding: utf-8

"""
FFD: Fabric for Docker
A set of convenience classes to run fabric scripts on docker containers
"""

from __future__ import unicode_literals, print_function
from importlib import import_module

from fabric import api, operations, context_managers, tasks

import fabfile


class FabricForDocker(object):

    def __init__(self, container, **options):
        self.container = container
        self.log = options.pop('log', log)
        self.__dict__.update(options)
        if hasattr(self, 'platform'):
            self.set_platform()

    def set_platform(self, container=None):
        if container:
            self.container = container
        module = import_module('navitia_image_manager.platforms.' + self.platform)
        api.env.distrib = getattr(self, 'distrib')
        getattr(module, self.platform)(self.get_host() if self.container else 'a@b')
        return self

    def get_host(self):
        return "{}@{}".format(getattr(self, 'user', 'root'), self.container.inspect())

    @property
    def get_env(self):
        return api.env

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

    def run(self, cmd, sudo=False):
        host = self.get_host()
        launch = operations.sudo if sudo and not host.startswith('root@') else operations.run
        with context_managers.settings(
                context_managers.hide('stdout'),
                host_string=host):
            self.output = launch(cmd)
        return self

    def put(self, source, dest, sudo=False):
        with context_managers.settings(host_string=self.get_host()):
            operations.put(source, dest, use_sudo=sudo)
        return self
