# encoding: utf-8

from __future__ import unicode_literals, print_function
import os

from fabric.api import env

ROOT = os.path.dirname(__file__)
SSH_KEY_FILE = os.path.join(ROOT, '..', 'ssh', 'unsecure_key')


def env_common(tyr, ed, kraken, jormun):
    env.key_filename = SSH_KEY_FILE
    env.use_ssh_config = True
    env.container = 'docker'
    env.use_syslog = False

    env.roledefs = {
        'tyr':  [tyr],
        'tyr_master': [tyr],
        'db':   [ed],
        'eng':  [kraken],
        'ws':   [jormun],
    }

    env.excluded_instances = []
    env.manual_package_deploy = True
    env.setup_apache = True

    env.kraken_monitor_listen_port = 85
    env.jormungandr_save_stats = False
    env.jormungandr_is_public = True
    env.tyr_url = 'localhost:6000'

    env.tyr_backup_dir_template = '/srv/ed/data/{instance}/backup/'
    env.tyr_source_dir_template = '/srv/ed/data/{instance}'
    env.tyr_base_destination_dir = '/srv/ed/data/'

    env.jormungandr_url = jormun.split('@')[-1]
    env.kraken_monitor_base_url = kraken.split('@')[-1]

    env.jormungandr_url_prefix = '/navitia'

    base_apache_conf = '/etc/apache2/conf.d' if env.distrib == 'debian7' else '/etc/apache2/conf-enabled'
    env.jormungandr_apache_config_file = os.path.join(base_apache_conf, 'jormungandr.conf')
    env.kraken_monitor_apache_config_file = os.path.join(base_apache_conf, 'monitor-kraken.conf')

    # add your own custom configuration variables in file custom.py
    # e.g. env.email
    try:
        import custom
    except ImportError:
        pass
