# Unified Transaction & Messaging Platform

FastAPI + PostgreSQL backend with wallet transfers and real-time messaging.

## Structure

```
app/
├── main.py          # App entry, middleware, router registration
├── config.py        # Settings from .env
├── database.py      # Engine, session, Base
├── models.py        # All DB tables (User, Wallet, Transaction, Message)
├── schemas.py       # All Pydantic request/response models
├── security.py      # JWT + bcrypt
├── deps.py          # get_current_user dependency
├── routers/
│   ├── auth.py          # POST /auth/register, /auth/login
│   ├── users.py         # GET/PATCH /users/me, /users/, /users/search
│   ├── wallet.py        # GET /wallet/, POST /wallet/add-money, /wallet/transfer
│   ├── transactions.py  # GET /transactions/, /sent, /received, /{id}
│   └── messages.py      # POST /messages/, GET /messages/history/{id}, WS /messages/ws
└── tests/
    ├── conftest.py
    └── test_main.py
```

## Local Setup

```bash
# 1. Clone and enter
git clone <repo>
cd clean-platform

# 2. Virtual environment
python -m venv venv
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows

# 3. Install
pip install -r requirements.txt

# 4. Environment
cp .env.example .env
# Edit .env with your Postgres connection string

# 5. Create database
psql -U postgres -c "CREATE DATABASE unified_platform;"

# 6. Migrate
alembic revision --autogenerate -m "initial"
alembic upgrade head

# 7. Run
python -m uvicorn app.main:app --reload
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs

## Tests

```bash
pytest app/tests/ -v
```

## Render Deployment

1. Push to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your repo — `render.yaml` handles everything automatically
4. After deploy, open Render Shell and run:
   ```bash
   alembic revision --autogenerate -m "initial"
   alembic upgrade head
   ```

## WebSocket Usage

```
Connect: ws://localhost:8000/messages/ws?token=YOUR_JWT
Send:    {"receiver_id": "<uuid>", "message": "hello"}
Receive: {"type": "message", "sender_id": "...", "message": "...", "created_at": "..."}
```

## Key Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /auth/register | No | Register + auto-create wallet |
| POST | /auth/login | No | Returns JWT |
| GET | /users/me | Yes | Your profile |
| GET | /wallet/ | Yes | Your balance |
| POST | /wallet/add-money | Yes | Top up wallet |
| POST | /wallet/transfer | Yes | Send money (DB-locked) |
| GET | /transactions/ | Yes | All transactions (paginated) |
| POST | /messages/ | Yes | Send message (REST) |
| GET | /messages/history/{id} | Yes | Chat history |
| WS | /messages/ws?token= | JWT | Real-time messaging |
