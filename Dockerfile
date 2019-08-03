FROM python:3.7.4-buster

WORKDIR /app

COPY ./requirements.txt .
RUN pip install -r requirements.txt
COPY . /app/
