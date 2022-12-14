FROM python:3-alpine

WORKDIR /app

COPY requirements.txt ./
RUN pip install git+https://github.com/lowellinstruments/lowell-mat.git@v4
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "./main.py"]
