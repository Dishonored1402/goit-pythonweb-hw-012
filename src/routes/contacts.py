from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from src.database.db import get_db
from src.database.models import User
from src.schemas import ContactCreate, ContactUpdate, ContactResponse
from src.repository import contacts as repository_contacts
from src.services.auth import auth_service

router = APIRouter(prefix='/contacts', tags=["contacts"])


@router.get("/", response_model=list[ContactResponse])
async def read_contacts(skip: int = 0, limit: int = 100, name: str = None, last_name: str = None, email: str = None,
                        db: Session = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user)):
    """Return contacts that belong to the current authenticated user.

    Supports pagination and optional filtering by first name, last name and email.

    :param skip: Number of records to skip.
    :param limit: Maximum number of contacts to return.
    :param name: Optional first name filter.
    :param last_name: Optional last name filter.
    :param email: Optional email filter.
    :param db: Database session.
    :param current_user: Current authenticated user.
    :return: List of contacts.
    """
    contacts = await repository_contacts.get_contacts(skip, limit, name, last_name, email, current_user, db)
    return contacts


@router.get("/birthdays", response_model=list[ContactResponse])
async def read_upcoming_birthdays(db: Session = Depends(get_db),
                                  current_user: User = Depends(auth_service.get_current_user)):
    """Return contacts with birthdays in the next seven days.

    :param db: Database session.
    :param current_user: Current authenticated user.
    :return: List of contacts with upcoming birthdays.
    """
    return await repository_contacts.get_upcoming_birthdays(current_user, db)


@router.get("/search/", response_model=list[ContactResponse])
async def search_contacts(
    query: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """Search contacts by first name, last name or email.

    :param query: Search string.
    :param db: Database session.
    :param current_user: Current authenticated user.
    :return: List of matching contacts.
    """
    contacts = await repository_contacts.search_contacts(query, current_user, db)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def read_contact(contact_id: int, db: Session = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user)):
    """Return one contact by ID for the current authenticated user.

    :param contact_id: Contact ID.
    :param db: Database session.
    :param current_user: Current authenticated user.
    :return: Contact object.
    :raises HTTPException: If the contact does not exist.
    """
    contact = await repository_contacts.get_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(body: ContactCreate, db: Session = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    """Create a new contact for the current authenticated user.

    :param body: Contact creation data.
    :param db: Database session.
    :param current_user: Current authenticated user.
    :return: Created contact object.
    """
    return await repository_contacts.create_contact(body, current_user, db)


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: int, body: ContactUpdate, db: Session = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    """Update an existing contact by ID.

    :param contact_id: Contact ID.
    :param body: Contact update data.
    :param db: Database session.
    :param current_user: Current authenticated user.
    :return: Updated contact object.
    :raises HTTPException: If the contact does not exist.
    """
    contact = await repository_contacts.update_contact(contact_id, body, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_contact(contact_id: int, db: Session = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    """Delete a contact by ID.

    :param contact_id: Contact ID.
    :param db: Database session.
    :param current_user: Current authenticated user.
    :return: None.
    :raises HTTPException: If the contact does not exist.
    """
    contact = await repository_contacts.remove_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return None
