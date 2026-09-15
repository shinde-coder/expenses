from rest_framework.test import APIClient

from catalogs.models import Category, CategoryType, PaymentMethod
from families.models import FamilyMember


def register(client=None, email="me@example.com", password="StrongPass123", name="Me"):
    client = client or APIClient()
    response = client.post(
        "/api/v1/auth/register/",
        {"email": email, "password": password, "name": name},
        format="json",
    )
    assert response.status_code == 201, response.data
    token = response.data["data"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client, response.data["data"]


def auth_client(email="me@example.com"):
    client, payload = register(email=email)
    return client, payload


def catalogs_for(family):
    groceries = Category.objects.get(family=None, name="Groceries", type=CategoryType.EXPENSE)
    salary = Category.objects.get(family=None, name="Salary", type=CategoryType.INCOME)
    sip = Category.objects.get(
        family=None, name="Savings & Investment", type=CategoryType.SAVING
    )
    upi = PaymentMethod.objects.get(family=None, name="UPI")
    member = FamilyMember.objects.get(family=family, relationship=FamilyMember.Relationship.SELF)
    return {
        "groceries": groceries,
        "salary": salary,
        "sip": sip,
        "upi": upi,
        "member": member,
        "kirana": groceries.subcategories.get(name="Kirana"),
    }
