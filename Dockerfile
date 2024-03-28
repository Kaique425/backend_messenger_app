FROM python:3.12.1

ENV PYTHONUNBUFFERED=1
WORKDIR /usr/src/app
COPY requirements.txt ./
# Atualizar o pip
RUN pip install --upgrade pip

# Copiar e instalar os requisitos do projeto
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt