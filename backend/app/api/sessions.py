from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database.session import get_db


from app.models.database import ChatSessionModel, ChatMessageModel

router = APIRouter(prefix="/sessions", tags=["Chat Sessions"])


class SessionResponse(BaseModel):
    id: str
    title: Optional[str]
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)



class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    sources: Optional[List[dict]] = None
    created_at: str


@router.get("", response_model=List[SessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(ChatSessionModel).order_by(ChatSessionModel.updated_at.desc()).all()
    return [
        SessionResponse(
            id=s.id,
            title=s.title or "New Chat",
            created_at=s.created_at.isoformat() if s.created_at else "",
            updated_at=s.updated_at.isoformat() if s.updated_at else ""
        )
        for s in sessions
    ]


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(title: Optional[str] = "New Chat", db: Session = Depends(get_db)):
    session = ChatSessionModel(title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat()
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSessionModel).filter(ChatSessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return None


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    messages = (
        db.query(ChatMessageModel)
        .filter(ChatMessageModel.session_id == session_id)
        .order_by(ChatMessageModel.created_at.asc())
        .all()
    )
    res = []
    for m in messages:
        sources = None
        if m.msg_metadata and isinstance(m.msg_metadata, dict):
            sources = m.msg_metadata.get("sources")
        res.append(
            MessageResponse(
                id=m.id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                sources=sources,
                created_at=m.created_at.isoformat() if m.created_at else ""
            )
        )
    return res
