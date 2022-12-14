FROM python:3-alpine

WORKDIR /app

COPY requirements.txt ./
RUN apk update && apk upgrade && \
    apk add --no-cache bash git openssh
RUN pip install git+https://github.com/lowellinstruments/lowell-mat.git@poor
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "./main.py"]
