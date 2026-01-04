"""
User API endpoints (Django Ninja).
"""
from ninja import Router, Schema
from ninja.security import HttpBearer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from typing import Optional
from uuid import UUID

router = Router()


class LoginIn(Schema):
    email: str
    password: str


class TokenOut(Schema):
    access: str
    refresh: str
    user_id: UUID
    email: str
    nombre: str
    rol: str


class UserOut(Schema):
    id: UUID
    email: str
    first_name: str
    last_name: str
    rol: str
    telefono: Optional[str]


class ErrorOut(Schema):
    detail: str


@router.post('/login', response={200: TokenOut, 401: ErrorOut}, auth=None)
def login(request, data: LoginIn):
    """Authenticate user and return JWT tokens."""
    user = authenticate(request, email=data.email, password=data.password)

    if user is None:
        return 401, {'detail': 'Credenciales inválidas'}

    if not user.is_active:
        return 401, {'detail': 'Usuario inactivo'}

    refresh = RefreshToken.for_user(user)

    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user_id': user.id,
        'email': user.email,
        'nombre': user.get_full_name(),
        'rol': user.rol,
    }


@router.post('/refresh', response={200: dict, 401: ErrorOut}, auth=None)
def refresh_token(request, refresh: str):
    """Refresh access token."""
    try:
        token = RefreshToken(refresh)
        return {
            'access': str(token.access_token),
            'refresh': str(token),
        }
    except Exception:
        return 401, {'detail': 'Token inválido o expirado'}


@router.get('/me', response=UserOut)
def get_current_user(request):
    """Get current authenticated user."""
    user = request.auth
    return user
