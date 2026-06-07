from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, Wallet, Transaction, TransactionStatus
from app.schemas import WalletResponse, AddMoneyRequest, TransferRequest, TransactionResponse

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("/", response_model=WalletResponse)
def get_wallet(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Wallet).filter(Wallet.user_id == current_user.id).first()


@router.post("/add-money", response_model=WalletResponse)
def add_money(
    data: AddMoneyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    wallet.balance += data.amount
    db.commit()
    db.refresh(wallet)
    return wallet


@router.post("/transfer", response_model=TransactionResponse, status_code=201)
def transfer(
    data: TransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id == data.receiver_id:
        raise HTTPException(status_code=400, detail="Cannot transfer to yourself")

    receiver = db.query(User).filter(User.id == data.receiver_id, User.is_active == True).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    # Lock both wallets to prevent race conditions (SELECT FOR UPDATE)
    wallets = (
        db.query(Wallet)
        .filter(Wallet.user_id.in_([current_user.id, data.receiver_id]))
        .with_for_update()
        .all()
    )
    wallet_map = {str(w.user_id): w for w in wallets}
    sender_wallet = wallet_map.get(str(current_user.id))
    receiver_wallet = wallet_map.get(str(data.receiver_id))

    if sender_wallet.balance < data.amount:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. Available: {sender_wallet.balance}")

    sender_wallet.balance -= data.amount
    receiver_wallet.balance += data.amount

    txn = Transaction(
        sender_id=current_user.id,
        receiver_id=data.receiver_id,
        amount=data.amount,
        status=TransactionStatus.COMPLETED,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn
