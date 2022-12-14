FROM ubuntu:22.04

WORKDIR /app

COPY requirements.txt ./
COPY h5py-3.7.0-cp39-cp39-manylinux_2_12_x86_64.manylinux2010_x86_64.whl ./
RUN apt update
RUN pip install -U pip setuptools wheel
RUN pip install git+https://github.com/lowellinstruments/lowell-mat.git@poor
RUN pip install --no-cache-dir -r requirements.txt  --only-binary=:all:

COPY . .

EXPOSE 8080

CMD ["python", "./main.py"]

# FROM python:3.9-alpine
#
# WORKDIR /app
#
# COPY requirements.txt ./
# COPY h5py-3.7.0-cp39-cp39-manylinux_2_12_x86_64.manylinux2010_x86_64.whl ./
# RUN apk update && apk upgrade && \
#     apk add --no-cache bash git py3-numpy g++
# RUN pip install -U pip setuptools wheel
# RUN pip install git+https://github.com/lowellinstruments/lowell-mat.git@poor
# RUN pip install ./h5py-3.7.0-cp39-cp39-manylinux_2_12_x86_64.manylinux2010_x86_64.whl
# RUN pip install --no-cache-dir -r requirements.txt  --only-binary=:all:
#
# COPY . .
#
# EXPOSE 8080
#
# CMD ["python", "./main.py"]
