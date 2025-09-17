FROM python:3-alpine3.12

RUN pip install --no-cache-dir requests

WORKDIR /usr/src/app

COPY main.py .

ENTRYPOINT ["python3", "main.py"]