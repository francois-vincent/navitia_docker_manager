# encoding: utf-8

import collections
from contextlib import contextmanager, nested
import glob
from jinja2 import Template
import os
import random
import semver
import shutil
import tempfile

log = None

global_temp_im_dir = '/tmp/temp_im'
if not os.access(global_temp_im_dir, os.W_OK):
    os.mkdir(global_temp_im_dir, 0766)


def absjoin(*p):
    return os.path.abspath(os.path.join(*p))


@contextmanager
def chdir(path):
    """
    Changes dir to path then comes back to original
    """
    try:
        if path:
            original = os.getcwd()
            path = os.path.abspath(os.path.expanduser(path))
            os.chdir(path)
        yield path
    finally:
        if path:
            os.chdir(original)


@contextmanager
def temp_file(temp, file_name, content, context):
    """
    Manages a temp file life cycle.
    The temp file content can be rendered from a template.
    The context is enriched for nested tempfile
    :param content: content or template
    :param file_name: optional file name
    :param context: context if content is a template
    """
    path = None
    try:
        use_jinja = file_name.endswith('.jinja')
        file_name = file_name.replace('.jinja', '')
        file_name = file_name.replace('.', '_')
        path = os.path.join(temp, file_name)
        log.debug("Create temp file {}".format(path))
        context[file_name] = file_name
        with open(path, 'w') as f:
            f.write(render(content, context, use_jinja=use_jinja))
        yield path
    finally:
        if path:
            log.debug("Remove temp file {}".format(path))
            del context[file_name]


@contextmanager
def chain_temp_files(files, context):
    temp = None
    try:
        temp = tempfile.mkdtemp(dir=global_temp_im_dir)
        log.debug("Create temp folder {}".format(temp))
        with nested(*[temp_file(temp, name, content, context) for name, content in files.iteritems()]):
            yield temp
    finally:
        if temp:
            log.debug("Remove temp folder {}".format(temp))
            shutil.rmtree(temp, ignore_errors=True)


def render(string, context, use_jinja=False):
    if isinstance(string, unicode):
        string = string.encode('utf-8')
    return Template(string).render(**context) if use_jinja else string.format(**context)


def wait(iterable):
    if isinstance(iterable, (collections.Iterable, collections.Iterator)):
        for line in iterable:
            log.debug(line)
            if line.startswith(b'{"errorDetail'):
                raise RuntimeError("Build failed @" + line)


def random_hex(len=24):
    return ''.join(random.choice('0123456789abcdef') for _ in xrange(len))


def semver_max_ver(*v):
    l = len(v)
    if l > 2:
        return semver.max_ver(v[0], semver_max_ver(*v[1:]))
    elif l == 2:
        return semver.max_ver(*v)
    else:
        return v[0]


def get_packet_version(folder='', pattern='navitia*deb'):
    with chdir(folder):
        return semver_max_ver(*[p.split('_')[1] for p in glob.glob(pattern)])
