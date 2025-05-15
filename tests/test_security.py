import pytest
from datetime import timedelta, datetime
from jose import jwt, JWTError

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token
)
from app.core.config import settings

def test_get_password_hash_and_verify():
    password = "supersecret"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)

def test_create_access_token_default_expiry():
    data = {"sub": "user@example.com"}
    token = create_access_token(data)
    assert isinstance(token, str)
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == "user@example.com"
    assert "exp" in decoded

def test_create_access_token_with_expiry():
    data = {"sub": "user2@example.com"}
    expires = timedelta(minutes=1)
    token = create_access_token(data, expires_delta=expires)
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == "user2@example.com"
    assert "exp" in decoded
    # La expiración debe estar cerca de ahora + 1 minuto
    exp = datetime.utcfromtimestamp(decoded["exp"])
    now = datetime.utcnow()
    assert 0 <= (exp - now).total_seconds() <= 70  # margen de error

def test_create_access_token_invalid_secret():
    data = {"sub": "user3@example.com"}
    token = create_access_token(data)
    # Decodificar con clave incorrecta debe fallar
    with pytest.raises(JWTError):
        jwt.decode(token, "wrongsecret", algorithms=[settings.ALGORITHM]) 