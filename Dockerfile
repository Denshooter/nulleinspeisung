# Verwenden Sie ein offizielles Python-Image als Basis
FROM python:3.12-alpine

# Arbeitsverzeichnis im Container festlegen
WORKDIR /app

RUN pip install --upgrade pip

# Installieren Sie die benötigten Python-Bibliotheken
RUN pip install requests

# Führen Sie das Python-Skript aus, wenn der Container gestartet wird
CMD ["python", "/app/Nulleinspeisung.py"]

