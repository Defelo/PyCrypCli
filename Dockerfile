FROM python:3.10-alpine

LABEL org.opencontainers.image.source=https://github.com/Defelo/PyCrypCli

WORKDIR /app

COPY requirements.txt /app/

RUN pip install -r requirements.txt

COPY PyCrypCli /app/PyCrypCli

CMD ["python", "-m", "PyCrypCli"]
