FROM debian:8

# systemd is removed and sysvinit is installed instead.
# As of may 2015, systemd is difficult to launch in a docker container, see http://developerblog.redhat.com/2014/05/05/running-systemd-within-docker-container/
# and if systemd is installed, some packages try to launch via systemctl (eg PostgreSQL) and fail
RUN apt-get update && apt-get install -y sysvinit-core locales sudo vim
RUN apt-get remove -y systemd

RUN apt-get install -y  postgresql-server-dev-all postgis

# change configuration to accept untrusted connections from remote hosts
RUN echo 'host  all  all  0.0.0.0/0  password' >> /etc/postgresql/9.4/main/pg_hba.conf
RUN echo "listen_addresses='*'" >> /etc/postgresql/9.4/main/postgresql.conf
