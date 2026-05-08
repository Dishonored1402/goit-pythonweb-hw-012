from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.database.models import Contact, User
from src.schemas import ContactCreate, ContactUpdate

async def get_contacts(skip: int, limit: int, name: str, last_name: str, email: str, user: User, db: Session):
    query = db.query(Contact).filter(Contact.user_id == user.id)
    if name:
        query = query.filter(Contact.first_name.ilike(f"%{name}%"))
    if last_name:
        query = query.filter(Contact.last_name.ilike(f"%{last_name}%"))
    if email:
        query = query.filter(Contact.email.ilike(f"%{email}%"))
    return query.offset(skip).limit(limit).all()

async def create_contact(body: ContactCreate, user: User, db: Session):
    existing_contact = db.query(Contact).filter(Contact.email == body.email, Contact.user_id == user.id).first()
    if existing_contact:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists in your contacts")
    
    contact = Contact(**body.model_dump(), user_id=user.id)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact

async def update_contact(contact_id: int, body: ContactUpdate, user: User, db: Session):
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).first()
    if contact:
        update_data = body.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(contact, key, value)
        db.commit()
        db.refresh(contact)
    return contact

async def get_upcoming_birthdays(user: User, db: Session):
    today = datetime.today().date()
    next_week = today + timedelta(days=7)
    
    contacts = db.query(Contact).filter(Contact.user_id == user.id).all()
    upcoming = []
    for contact in contacts:
        if contact.birthday:
            try:
                bday_this_year = contact.birthday.replace(year=today.year)
            except ValueError:
                bday_this_year = contact.birthday.replace(year=today.year, day=28)
                
            if today <= bday_this_year <= next_week:
                upcoming.append(contact)
    return upcoming

async def get_contact(contact_id: int, user: User, db: Session):
    return db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).first()

async def remove_contact(contact_id: int, user: User, db: Session):
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).first()
    if contact:
        db.delete(contact)
        db.commit()
    return contact