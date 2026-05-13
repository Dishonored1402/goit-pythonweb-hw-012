import pytest

@pytest.mark.asyncio
async def test_create_contact(client, token):
    response = client.post(
        "/api/contacts/",
        json={
            "first_name": "Bill", 
            "last_name": "Gates", 
            "email": "bill@ms.com", 
            "phone_number": "000111222", 
            "birthday": "1955-10-28"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_get_contacts(client, token):
    response = client.get(
        "/api/contacts/", 
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_birthdays(client, token):
    response = client.get(
        "/api/contacts/birthdays/", 
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 404:
        response = client.get(
            "/api/contacts/upcoming_birthdays/", 
            headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 200