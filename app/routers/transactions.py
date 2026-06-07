from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, Transaction
from app.schemas import TransactionResponse, PaginatedTransactions

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def paginate(query, page: int, page_size: int):
    total = query.count()
    items = query.order_by(Transaction.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


@router.get("/", response_model=PaginatedTransactions)
def all_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Transaction).filter(
        (Transaction.sender_id == current_user.id) | (Transaction.receiver_id == current_user.id)
    )
    txns, total = paginate(query, page, page_size)
    return PaginatedTransactions(total=total, page=page, page_size=page_size, transactions=txns)


@router.get("/sent", response_model=PaginatedTransactions)
def sent_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Transaction).filter(Transaction.sender_id == current_user.id)
    txns, total = paginate(query, page, page_size)
    return PaginatedTransactions(total=total, page=page, page_size=page_size, transactions=txns)


@router.get("/received", response_model=PaginatedTransactions)
def received_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Transaction).filter(Transaction.receiver_id == current_user.id)
    txns, total = paginate(query, page, page_size)
    return PaginatedTransactions(total=total, page=page, page_size=page_size, transactions=txns)


@router.get("/{txn_id}", response_model=TransactionResponse)
def get_transaction(
    txn_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if str(txn.sender_id) != str(current_user.id) and str(txn.receiver_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    return txn
