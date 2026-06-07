import json
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.deps import get_current_user
from app.models import User, Message
from app.schemas import SendMessageRequest, MessageResponse, ChatHistory
from app.security import decode_token

router = APIRouter(prefix="/messages", tags=["Messages"])

# In-memory WebSocket connection store: {user_id: WebSocket}
# Limitation: single process only. Use Redis pub/sub for multi-instance scaling.
active_connections: Dict[str, WebSocket] = {}


# ── REST ──────────────────────────────────────────────────────────────────────

@router.post("/", response_model=MessageResponse, status_code=201)
def send_message(
    data: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id == data.receiver_id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")

    receiver = db.query(User).filter(User.id == data.receiver_id, User.is_active == True).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    msg = Message(sender_id=current_user.id, receiver_id=data.receiver_id, message=data.message)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


@router.get("/history/{other_user_id}", response_model=ChatHistory)
def chat_history(
    other_user_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Mark incoming messages as read
    db.query(Message).filter(
        Message.sender_id == other_user_id,
        Message.receiver_id == current_user.id,
        Message.is_read == False,
    ).update({"is_read": True})
    db.commit()

    query = db.query(Message).filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other_user_id))
        | ((Message.sender_id == other_user_id) & (Message.receiver_id == current_user.id))
    )
    total = query.count()
    messages = query.order_by(Message.created_at.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return ChatHistory(total=total, messages=messages)


# ── WebSocket ─────────────────────────────────────────────────────────────────

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    Connect: ws://host/messages/ws?token=YOUR_JWT
    Send:    {"receiver_id": "<uuid>", "message": "<text>"}
    Receive: {"type": "message", "sender_id": "...", "receiver_id": "...", "message": "...", "created_at": "..."}
    """
    user_id = decode_token(token)
    if not user_id:
        await websocket.close(code=4001)
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            await websocket.close(code=4001)
            return
    finally:
        db.close()

    await websocket.accept()
    active_connections[user_id] = websocket

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
                receiver_id = data.get("receiver_id", "").strip()
                text = data.get("message", "").strip()

                if not receiver_id or not text:
                    await websocket.send_text(json.dumps({"type": "error", "detail": "receiver_id and message required"}))
                    continue

                db = SessionLocal()
                try:
                    receiver = db.query(User).filter(User.id == receiver_id, User.is_active == True).first()
                    if not receiver:
                        await websocket.send_text(json.dumps({"type": "error", "detail": "Receiver not found"}))
                        continue

                    msg = Message(sender_id=UUID(user_id), receiver_id=UUID(receiver_id), message=text)
                    db.add(msg)
                    db.commit()
                    db.refresh(msg)

                    payload = {
                        "type": "message",
                        "id": str(msg.id),
                        "sender_id": str(msg.sender_id),
                        "receiver_id": str(msg.receiver_id),
                        "message": msg.message,
                        "created_at": msg.created_at.isoformat(),
                    }

                    # Deliver to receiver if online, always echo back to sender
                    if receiver_id in active_connections:
                        try:
                            await active_connections[receiver_id].send_text(json.dumps(payload))
                        except Exception:
                            active_connections.pop(receiver_id, None)

                    await websocket.send_text(json.dumps(payload))

                finally:
                    db.close()

            except (json.JSONDecodeError, ValueError):
                await websocket.send_text(json.dumps({"type": "error", "detail": "Invalid JSON"}))

    except WebSocketDisconnect:
        active_connections.pop(user_id, None)
