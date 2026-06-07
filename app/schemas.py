from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models import TransactionStatus


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── User ──────────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None


# ── Wallet ────────────────────────────────────────────────────────────────────

class WalletResponse(BaseModel):
    id: UUID
    user_id: UUID
    balance: Decimal
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class AddMoneyRequest(BaseModel):
    amount: Decimal = Field(..., ge=1, decimal_places=2)


class TransferRequest(BaseModel):
    receiver_id: UUID
    amount: Decimal = Field(..., ge=1, decimal_places=2)


# ── Transaction ───────────────────────────────────────────────────────────────

class TransactionResponse(BaseModel):
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    amount: Decimal
    status: TransactionStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedTransactions(BaseModel):
    total: int
    page: int
    page_size: int
    transactions: List[TransactionResponse]


# ── Message ───────────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    receiver_id: UUID
    message: str = Field(..., min_length=1, max_length=2000)


class ChatHistory(BaseModel):
    total: int
    messages: List[MessageResponse]
