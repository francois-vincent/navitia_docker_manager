# encoding: utf-8

"""
DIM: Docker Image Manager
A set of convenience classes to create and manage Docker Images and Containers
"""

from __future__ import unicode_literals, print_function
from collections import OrderedDict
from contextlib import contextmanager
import os
ROOT = os.path.abspath(os.path.dirname(__file__))

import docker

from utils import wait, random_hex, chain_temp_files

docker_client = docker.Client(base_url='unix://var/run/docker.sock', version='auto')


class betterdict(dict):

    def __add__(self, other):
        self.update(other)
        return self


class DockerRunParameters(betterdict):
    """
    A class to define parameters for the docker create/run commands.
    Is also used to enrich Dockerfile EXPOSE and VOLUME instructions.
    """
    allowed = ()

    def __init__(self, **options):
        dict.__init__(self)
        self.log = options.pop('log', log)
        volumes = options.pop('volumes', ())
        ports = options.pop('ports', ())
        self.update(options)
        self.kwargs = {}
        for vol in volumes:
            self.add_volume(vol)
        for port in ports:
            self.add_port(port)
        self.finalize()

    def clone(self):
        # TODO provide true clone
        return betterdict(self)

    def add_volume(self, vol):
        binds = self.kwargs.setdefault('binds', {})
        volumes = self.setdefault('volumes', set())
        # host can be void (volume has no mapping)
        if ':' in vol:
            host, guest = vol.split(':', 1)
        else:
            host, guest = None, vol
        # default mode is 'rw', you can specify 'ro' instead
        if ':' in guest:
            guest, mode = guest.split(':')
        else:
            mode = 'rw'
        if host:
            host = os.path.abspath(os.path.expanduser(host))
            binds[host] = {'bind': guest, 'mode': mode}
        volumes.add(guest)

    def add_port(self, port):
        port_bindings = self.kwargs.setdefault('port_bindings', {})
        ports = self.setdefault('ports', set())
        if isinstance(port, basestring):
            if ':' in port:
                # TODO does not accept format host_ip:host_port:guest_port yet
                host, guest = port.rsplit(':', 1)
                guest = int(guest)
                port_bindings[guest] = int(host) if host else None
                ports.add(guest)
            elif '-' in port:
                start, end = port.split('-')
                for p in xrange(int(start), int(end) + 1):
                    port_bindings[p] = None
                    ports.add(p)
            else:
                port = int(port)
                port_bindings[port] = None
                ports.add(port)
        else:
            port_bindings[port] = None
            ports.add(port)

    def finalize(self):
        if self.kwargs:
            self['host_config'] = docker.utils.create_host_config(**self.kwargs)
        if 'ports' in self:
            self['ports'] = list(self['ports'])
            self['ports'].sort()
        if 'volumes' in self:
            self['volumes'] = list(self['volumes'])

    def __add__(self, other):
        res = self.clone()
        res.update(other)
        return res


class DockerFile(object):
    """
    A class to manage Dockerfile like objects
    """
    def __init__(self, *files, **options):
        self.log = options.pop('log', log)
        # this is the global context used by every template involved in the build process
        # templates can be Dockerfile, configuration files, ...
        self.template_context = options.pop('template_context', None) or {}
        self.parameters = options.pop('parameters', None) or {}
        self.add_ons = options.pop('add_ons', None) or ()
        # a file can be a real file, specified by a path,
        # or a pseudo file, specified via a (name, content) pair
        self.files = OrderedDict()
        for file in files:
            if isinstance(file, tuple):
                name, content = file
            else:
                name = os.path.basename(file)
                with open(os.path.expanduser(file), 'rb') as f:
                    content = f.read()
            self.files[name] = content
        self.files.update(options)
        if not 'Dockerfile' in self.files:
            raise ValueError("No Dockerfile specified")
        # Dockerfile must be the last element
        self.files['Dockerfile'] = self.files.pop('Dockerfile')

    def process_parameters(self):
        dockerfile = self.files['Dockerfile']
        if 'ports' in self.parameters and not '\nEXPOSE' in dockerfile:
            extension = '\nEXPOSE ' + ' '.join(str(p) for p in self.parameters['ports']) + '\n'
            self.files['Dockerfile'] += extension
        if 'volumes' in self.parameters and not '\nVOLUME' in dockerfile:
            extension = '\nVOLUME ["' + '" "'.join(str(p) for p in self.parameters['volumes']) + '"]\n'
            self.files['Dockerfile'] += extension
        return self

    def process_addons(self):
        for add_on in self.add_ons:
            with open(os.path.join(ROOT, 'addons', add_on)) as f:
                self.files['Dockerfile'] += f.read()
        return self

    def get_dockerfile(self, process=True):
        with self.get_docker_context(process=process) as context:
            with open(os.path.join(context, 'Dockerfile'), 'rb') as f:
                return f.read()

    @contextmanager
    def get_docker_context(self, process=True):
        if process:
            self.process_addons().process_parameters()
        with chain_temp_files(self.files, self.template_context) as context:
            yield context


class DockerImageManager(object):
    """
    A class to manage Docker images, wich features:
    - Creating a new image out of an existing image.
    - Creating a new image out of a Dockerfile that can be inline or file,
      raw or template.
    - Running an image with a set of parameters.
    - Pushing an image to dockerhub, provided the user is logged in.
    An instance manages a single image.
    """

    def __init__(self, source, **kwargs):
        self.source = source
        kwargs['image'] = self.image_name = kwargs.pop('image_name', None) or self.random_name()
        self.log = kwargs.pop('log', log)
        self.log.debug("New {}(image_name='{}')".format(self.__class__.__name__, self.image_name))
        self.parameters = kwargs.pop('parameters', None)
        if self.parameters:
            self.parameters.update(kwargs)
        else:
            self.parameters = DockerRunParameters(**kwargs)

    @staticmethod
    def random_name():
        return 'nav_' + random_hex()

    @property
    def exists(self):
        return bool(self.inspect())

    @property
    def untagged_name(self):
        return self.image_name.split(':')[0]

    def pull(self):
        wait(docker_client.pull(self.source, stream=True))
        return self

    def build(self, fail_if_exists=True):
        if self.exists:
            if fail_if_exists:
                raise RuntimeError("Image '{}' already exists".format(self.image_name))
        else:
            self.log.info("Building image {}".format(self.image_name))
            with self.source.get_docker_context() as context:
                wait(docker_client.build(path=context, tag=self.image_name, rm=True))
        return self

    def create_image(self):
        if isinstance(self.source, DockerFile):
            return self.build()
        return self.pull()

    def inspect(self, field=None, image_name=None):
        try:
            config = docker_client.inspect_image(image_name or self.image_name)
            if field:
                config = config.get(field, '')
            return config
        except docker.errors.NotFound:
            return None

    def resolve_tag(self, image_name, tag):
        image_name = image_name or self.image_name
        try:
            image_name, _tag = image_name.split(':')
            tag = tag or _tag
        except ValueError:
            pass
        return image_name, tag

    def push(self, image_name=None, tag=None):
        image_name, tag = self.resolve_tag(image_name, tag)
        if tag:
            self.log.info("Pushing image '{}:{}'".format(image_name, tag))
            docker_client.push(image_name, tag)
        else:
            self.log.info("Pushing image '{}'".format(image_name))
            docker_client.push(image_name)
        return self

    def remove_image(self, image_name=None, tag=None):
        image_name, tag = self.resolve_tag(image_name, tag)
        try:
            docker_client.remove_image(image=image_name)
            self.log.info("Removing image '{}'".format(image_name))
        except docker.errors.APIError:
            self.log.warning("Can't remove image '{}': not found".format(image_name))
        return self

    def get_container(self, container_name=None):
        return DockerContainerManager(self, container_name=container_name)

    def create_container(self, container_name=None, **kwargs):
        return DockerContainerManager(self, container_name=container_name).create(**kwargs)

    def print_command(self, image_name, container_name):
        cmd = "docker run -d"
        for k, v in self.parameters.kwargs['port_bindings'].iteritems():
            cmd += ' -p {}:{}'.format(k, v)
        for k, v in self.parameters.kwargs['binds'].iteritems():
            cmd += ' -v {}:{}'.format(k, v['bind'])
        cmd += ' --name {}'.format(container_name)
        cmd += ' {}'.format(image_name)
        return cmd


class DockerContainerManager(object):
    """
    A class to manage docker containers
    """
    def __init__(self, image=None, **kwargs):
        kwargs['name'] = self.container_name = kwargs.pop('container_name', None) or self.random_name()
        if image:
            self.image, self.image_name = image, image.image_name
            self.parameters = self.image.parameters + kwargs
            self.log = image.log
        else:
            self.image, self.image_name = None, None
            self.log = kwargs.pop('log', log)
        self.log.debug("New {}(container_name='{}')".format(self.__class__.__name__, self.container_name))

    def random_name(self):
        if self.image:
            return self.image_name[:12] + '_' + random_hex(11)
        else:
            return random_hex()

    @property
    def exists(self):
        return bool(self.inspect('State'))

    @property
    def is_running(self):
        return self.inspect('State.Running')

    def create(self, start=False, if_exist='fail'):
        """
        Create a container
        :param if_exist: what to do if container already exists
               'fail': raise exception, 'remove': remove container, 'silent': silently do nothing
        """
        if self.exists:
            if if_exist == 'fail':
                raise RuntimeError("Container '{}' already exists".format(self.container_name))
            elif if_exist == 'remove':
                self.remove_container()
        if not self.exists:
            docker_client.create_container(**self.parameters)
        if start:
            self.start()
        return self

    def start(self):
        if not self.is_running:
            self.log.debug("Starting container {}".format(self.container_name))
            docker_client.start(self.container_name)
        return self

    def inspect(self, field='NetworkSettings.IPAddress', container_name=None):
        try:
            config = docker_client.inspect_container(container_name or self.container_name)
            if field:
                for x in field.split('.'):
                    if x and config:
                        config = config.get(x, '')
            return config
        except docker.errors.NotFound:
            return None

    def exec_container(self, cmd, wait=True):
        id = docker_client.exec_create(self.container_name, cmd, stdout=False, stdin=False)
        docker_client.exec_start(execid=id, detach=not wait)
        return self

    def copy_from_container(self, guest_path, host_path=None):
        data = docker_client.copy(self.container_name, guest_path)
        if host_path:
            with open(os.path.abspath(os.path.expanduser(host_path)), 'wb') as f:
                f.write(data)
        else:
            return data

    def stop(self):
        if self.is_running:
            self.log.debug("Stopping container {}".format(self.container_name))
            docker_client.stop(self.container_name)
        return self

    def commit(self, image_name, version=''):
        params = (self.container_name, image_name)
        message = "Commiting container {} as {}".format(*params)
        if version:
            params += (version,)
            message += ':' + version
        self.log.debug(message)
        docker_client.commit(*params)
        return self

    def tag(self, image_name, version=''):
        tagged_name = '{}:{}'.format(image_name, version) if version else image_name
        image_name = image_name.split(':')[0]
        if image_name == tagged_name:
            self.log.warning("Trying to tag image_name == tagged_name, nothing to do")
            return self
        self.log.debug("Tagging image {} as last version".format(tagged_name))
        docker_client.tag(tagged_name, image_name)
        return self

    def remove_container(self):
        self.stop()
        if self.exists:
            self.log.debug("Removing container {}".format(self.container_name))
            docker_client.remove_container(self.container_name)
        return self
