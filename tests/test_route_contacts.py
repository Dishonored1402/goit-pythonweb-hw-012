import pytest

def test_create_contact(client, token):
    response = client.post(
        "/api/contacts/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone_number": "1234567890",
            "birthday": "1990-01-01"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201

def test_get_contacts(client, token):
    response = client.get("/api/contacts/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_get_contact_not_found(client, token):
    response = client.get("/api/contacts/999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404

def test_search_contacts(client, token):
    response = client.get(
        "/api/contacts/?name=John",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)