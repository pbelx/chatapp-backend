# ChatApp

Real-time chat API built with **FastAPI**, **PostgreSQL**, and **WebSockets**.

## Features
- JWT authentication (register / login)
- Real-time direct messages via WebSocket
- REST endpoints for DM history and conversation list
- Async SQLAlchemy + asyncpg
- Alembic migrations

## Stack
| Layer | Tech |
|-------|------|
| Framework | FastAPI |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2 (async) |
| Migrations | Alembic |
| Auth | JWT (python-jose) |
| Passwords | bcrypt (passlib) |
| Runtime | uvicorn |

## Quick Start (Docker)

```bash
cp .env.example .env
# Edit .env — change SECRET_KEY at minimum

docker compose up --build
```

API is available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

## Quick Start (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Set DATABASE_URL to your local postgres

alembic upgrade head
uvicorn app.main:app --reload
```

## API Reference

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Get JWT token |

### Users
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/users/me` | Current user profile |

### Messages (REST)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/messages/dm` | Send a DM |
| GET | `/api/v1/messages/dm/{user_id}` | DM history with a user |
| GET | `/api/v1/messages/conversations` | List all conversations |

### WebSocket

```
ws://localhost:8000/ws/chat?token=<JWT>
```

Send JSON:
```json
{ "recipient_id": "<uuid>", "content": "Hello!" }
```

Receive JSON (sent to both sender and recipient):
```json
{
  "id": "<uuid>",
  "sender_id": "<uuid>",
  "sender_username": "alice",
  "recipient_id": "<uuid>",
  "content": "Hello!",
  "created_at": "2026-02-25T12:00:00+00:00"
}
```

## Project Structure

```
chatapp/
├── app/
│   ├── api/v1/endpoints/
│   │   ├── auth.py        # register, login
│   │   ├── users.py       # /me
│   │   ├── messages.py    # DM REST endpoints
│   │   └── websocket.py   # WS /ws/chat
│   ├── core/
│   │   ├── config.py      # Settings (pydantic-settings)
│   │   ├── deps.py        # get_current_user dependency
│   │   └── security.py    # JWT + bcrypt helpers
│   ├── db/session.py      # Engine, session, Base
│   ├── models/            # SQLAlchemy ORM models
│   ├── schemas/           # Pydantic request/response schemas
│   ├── services/
│   │   └── connection_manager.py  # WebSocket manager
│   └── main.py
├── alembic/               # DB migrations
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```
