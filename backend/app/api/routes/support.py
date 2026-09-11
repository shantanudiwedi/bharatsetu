from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import SupportTicket, User
from app.schemas.schemas import SupportTicketCreate, SupportTicketSchema
from app.core.security import get_current_user

router = APIRouter(prefix="/support", tags=["Support"])

@router.post("", response_model=SupportTicketSchema)
def create_support_ticket(
    ticket: SupportTicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_ticket = SupportTicket(
        user_id=current_user.id,
        subject=ticket.subject,
        description=ticket.description,
        status="OPEN"
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

