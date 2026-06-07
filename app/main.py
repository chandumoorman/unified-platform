from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import auth, users, wallet, transactions, messages

# Import models so Base.metadata knows about all tables
import app.models  # noqa: F401

app = FastAPI(
    title="Unified Transaction & Messaging Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(wallet.router)
app.include_router(transactions.router)
app.include_router(messages.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/", tags=["Health"])
def health():
    return {"status": "ok"}
