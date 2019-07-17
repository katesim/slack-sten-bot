FROM python:3.6.1

RUN set -ex

RUN mkdir -p project
WORKDIR /project

COPY requirements.txt ./
RUN pip install -r requirements.txt


CMD ["/bin/bash"]

EXPOSE 5000
