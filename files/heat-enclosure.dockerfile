# dockerfile for python3 environment
FROM python:3.10.7-alpine
# create app directory
# RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
# install requirements used by heat-enclosure.py
COPY ./heat-enclosure-requirements.txt .
RUN pip install -r heat-enclosure-requirements.txt
# copy heat-enclosure.py script
COPY ./heat-enclosure.py .
# set environment
ENV PYTHONUNBUFFERED 1
ENTRYPOINT [ "/usr/src/app/heat-enclosure.py" ]
