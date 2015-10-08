FROM debian:8

RUN apt-get update && apt-get install -y sysvinit-core python-pip python-dev supervisor git vim
RUN apt-get install -y libprotobuf9 libprotobuf-dev libprotoc9 protobuf-compiler
RUN apt-get install -y postgresql-9.4 postgresql-server-dev-all
RUN apt-get install -y rabbitmq-server
RUN apt-get remove -y systemd

RUN mkdir -p /root/.ssh
COPY id_rsa /root/.ssh/id_rsa
COPY id_rsa.pub /root/.ssh/id_rsa.pub
RUN chmod 700 /root/.ssh/id_rsa
RUN echo "Host github.com\n\tStrictHostKeyChecking no\n" >> /root/.ssh/config

RUN cd /root && git clone git@github.com:CanalTP/kirin.git
WORKDIR /root/kirin
RUN git submodule update --init

RUN pip install uwsgi requests
RUN sed -i '/requests/d' requirements.txt
RUN pip install -r requirements.txt

ENV KIRIN_CONFIG_FILE /root/kirin/kirin/settings.py
COPY settings.py /root/kirin/kirin/settings.py
COPY .env /root/kirin/.env

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord"]

EXPOSE 80
