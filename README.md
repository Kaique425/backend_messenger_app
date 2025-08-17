# Backend_messenger_app

Backend de mensageria integrado à WhatsApp Official Cloud API (Application Programming Interface).  
Suporta envio/recebimento de mensagens, imagens, respostas com citação e **HSM (Highly Structured Message)**, também chamadas de **Template Messages**.

## Sumário
- [Visão Geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Arquitetura](#arquitetura)
- [Stack Técnica](#stack-técnica)
- [Requisitos](#requisitos)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Instalação](#instalação)
  - [Sem Docker](#sem-docker)
  - [Com Docker Compose](#com-docker-compose)
- [Execução](#execução)
- [Webhook do WhatsApp Cloud](#webhook-do-whatsapp-cloud)
- [Autenticação](#autenticação)
- [Endpoints Principais](#endpoints-principais)
- [Fluxo de Mensagem](#fluxo-de-mensagem)
- [Testes](#testes)
- [Qualidade de Código](#qualidade-de-código)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Licença](#licença)

---

## Visão Geral
Este projeto expõe uma API (Application Programming Interface) REST para integrar sistemas internos com a **WhatsApp Official Cloud API**.  
Inclui Webhook para recebimento de eventos, envio de mensagens usando templates (HSM/Template Messages) e **WebSockets** via **Django Channels** para atualizações em tempo real na aplicação cliente.

## Funcionalidades
- Enviar mensagens de WhatsApp (texto simples).
- Receber mensagens de WhatsApp via Webhook.
- Enviar e receber imagens, com legenda (caption).
- Responder mensagens de clientes usando a funcionalidade de **reply** do WhatsApp.
- Enviar **HSM (Highly Structured Message)** / **Template Messages** aprovados.
- Atualizações em tempo real via **WebSocket**.
- Filas de processamento com **Celery** e **Redis (Remote Dictionary Server)**.

## Arquitetura
```mermaid
flowchart LR
  ClientApp[Cliente REST/Front-end] -->|HTTPS| API[Django + DRF]
  API -->|REST| WhatsAppAPI[WhatsApp Cloud API]
  WhatsAppAPI -->|Webhook| Webhook[Endpoint Webhook]
  Webhook -->|Task Async| CeleryQueue[Celery + Redis]
  CeleryQueue -->|Persistência| DB[(PostgreSQL)]
  API -->|WebSocket| Channels[Django Channels]
  DB <--> API
```

## Stack Técnica
- **Django** (framework web em Python)
- **DRF (Django REST Framework)** para API REST
- **Django Channels** para **WebSocket**
- **Celery** para processamento assíncrono
- **Redis (Remote Dictionary Server)** como broker/resultado do Celery e cache
- **PostgreSQL** como banco de dados
- **SimpleJWT (JSON Web Token)** para autenticação

## Requisitos
- Python >= 3.11
- PostgreSQL >= 13
- Redis >= 6
- Docker e Docker Compose (opcional, para ambiente containerizado)

## Variáveis de Ambiente
Configure-as em `.env` (ou no ambiente do container):

| Variável | Descrição |
|---------|-----------|
| `DJANGO_SECRET_KEY` | Chave secreta do Django. |
| `DJANGO_DEBUG` | `1` para debug, `0` para produção. |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos, separados por espaço. |
| `DATABASE_URL` | URL no formato `postgres://user:pass@host:port/db`. |
| `CELERY_BROKER` | Ex.: `redis://redis:6379/0`. |
| `CELERY_BACKEND` | Ex.: `redis://redis:6379/0`. |
| `WHATSAPP_TOKEN` | Token de acesso da WhatsApp Cloud API. |
| `WHATSAPP_VERIFY_TOKEN` | Token de verificação do Webhook (usado pelo GET de verificação). |
| `WHATSAPP_PHONE_NUMBER_ID` | ID do número no WhatsApp Cloud. |
| `WHATSAPP_BUSINESS_ID` | ID do WABA (WhatsApp Business Account). |
| `WHATSAPP_API_BASE_URL` | Base da API (ex.: `https://graph.facebook.com/v20.0`). |

> Dica: armazene segredos usando um cofre de segredos quando for para produção.

## Instalação

### Sem Docker
1. Crie e ative um ambiente virtual.
2. Instale dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure o `.env`.
4. Aplique migrações:
   ```bash
   python manage.py migrate
   ```
5. Crie um superusuário (opcional):
   ```bash
   python manage.py createsuperuser
   ```

### Com Docker Compose
Exemplo mínimo de `docker-compose.yml`:
```yaml
services:
  django:
    build: .
    command: >
      sh -c "python manage.py migrate &&
             python manage.py runserver 0.0.0.0:8001"
    env_file: .env
    volumes:
      - .:/usr/src/app/
    ports:
      - "8001:8001"
    depends_on:
      - pgdb
      - redis

  celery:
    build: .
    command: celery -A core worker -l INFO -P solo --concurrency=1
    env_file: .env
    volumes:
      - .:/usr/src/app/
    depends_on:
      - redis
      - pgdb

  redis:
    image: redis:7

  pgdb:
    image: postgres:16
    environment:
      POSTGRES_DB: messenger
      POSTGRES_USER: messenger
      POSTGRES_PASSWORD: messenger
    ports:
      - "5432:5432"
```

Subir os serviços:
```bash
docker compose up --build
```

## Execução
- Servidor Django:
  ```bash
  python manage.py runserver 0.0.0.0:8001
  ```
- Worker Celery:
  ```bash
  celery -A core worker -l INFO -P solo --concurrency=1
  ```
- (Opcional) Beat do Celery para tarefas periódicas:
  ```bash
  celery -A core beat -l INFO
  ```


## Fluxo de Mensagem
```mermaid
sequenceDiagram
  participant C as "Cliente (WhatsApp)"
  participant W as "WhatsApp Cloud API"
  participant S as "Backend (Django/DRF)"
  participant Q as "Celery/Redis"
  participant DB as "PostgreSQL"

  C->>W: Envia mensagem
  W->>S: POST /webhook/whatsapp (payload)
  S->>Q: Enfileira processamento
  Q->>DB: Persiste/atualiza entidades
  S-->>C: Notifica via WebSocket (Channels)
  S->>W: (Opcional) Responde usando Send Message/Template
  W->>C: Entrega mensagem
```
