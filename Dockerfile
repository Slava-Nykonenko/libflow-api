FROM python:3.11.14-alpine3.23
LABEL authors="slava.nykon@gmail.com"

ENV PYTHONUNBUFFERED=1
WORKDIR /libflow-api

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
