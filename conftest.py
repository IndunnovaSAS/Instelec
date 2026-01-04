"""Pytest configuration and fixtures for TransMaint."""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user_password():
    """Return a common password for test users."""
    return "testpass123!"


@pytest.fixture
def admin_user(db, user_password):
    """Create and return an admin user."""
    return User.objects.create_user(
        email="admin@test.com",
        password=user_password,
        first_name="Admin",
        last_name="User",
        rol="admin",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def coordinador_user(db, user_password):
    """Create and return a coordinator user."""
    return User.objects.create_user(
        email="coordinador@test.com",
        password=user_password,
        first_name="Coordinador",
        last_name="Test",
        rol="coordinador",
    )


@pytest.fixture
def ingeniero_user(db, user_password):
    """Create and return an engineer user."""
    return User.objects.create_user(
        email="ingeniero@test.com",
        password=user_password,
        first_name="Ingeniero",
        last_name="Residente",
        rol="ing_residente",
    )


@pytest.fixture
def liniero_user(db, user_password):
    """Create and return a lineman user."""
    return User.objects.create_user(
        email="liniero@test.com",
        password=user_password,
        first_name="Liniero",
        last_name="Campo",
        rol="liniero",
    )


@pytest.fixture
def api_client():
    """Return a Django Ninja test client."""
    from ninja.testing import TestClient

    from apps.api.router import api

    return TestClient(api)


@pytest.fixture
def authenticated_client(client, admin_user, user_password):
    """Return an authenticated Django test client."""
    client.login(email=admin_user.email, password=user_password)
    return client
