

# Docker Image Manager

A set of convenience classes and utilies for abstracting
and automating the creation, run and management of Docker images and containers.
This is oriented for the creation of monolithic docker images (opposite to the usual
microservices view)


## DIM: Docker Image Manager classes

A set of classes to create new docker images out of:

 - a base image or a base Dockerfile that can be inline or file
 - Dockerfiles addons (for apache, postgresql, user, ...)
 - Dockerfile parameters (ports and volumes)
 - Different configuration files


## FFD: Fabric for Docker

A class and a set of platforms that allows the deployment of Navitia on
a Docker image via Fabric scripts.


## Factories

A set of scripts that automates the creation of images, or anything else
regarding docker images and containers (running, deletings, ...)

 - navitia_simple.py: create a monolithic Navitia image with a single 'default' coverage.
 - navitia_artemis.py: create an Artemis image for running artemis tests.

You can run any of these scripts with option '--help' for help on the available options.

> Written with [StackEdit](https://stackedit.io/).
