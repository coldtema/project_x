FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --disabled-password --gecos '' celeryuser

RUN mkdir -p /code/staticfiles && chown -R celeryuser:celeryuser /code/staticfiles

USER celeryuser
