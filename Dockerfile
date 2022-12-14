FROM python:3.9-alpine

WORKDIR /app

COPY requirements.txt ./
RUN apk update && apk upgrade && \
    apk add --no-cache bash git py3-numpy g++
RUN pip install -U pip setuptools wheel
RUN pip install git+https://github.com/lowellinstruments/lowell-mat.git@poor
RUN pip install --no-cache-dir -r requirements.txt  --only-binary=:all:

COPY . .

EXPOSE 8080

CMD ["python", "./main.py"]
