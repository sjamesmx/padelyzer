import pytest
from datetime import datetime, UTC
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List
from enum import Enum

# --- Inline minimal models for schema validation ---

class UserRegistration(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=2, max_length=100)
    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        import re
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe contener al menos una minúscula')
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe contener al menos un número')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('La contraseña debe contener al menos un carácter especial')
        return v

class VideoType(str, Enum):
    TRAINING = "training"
    GAME = "game"

class VideoUpload(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    video_type: VideoType
    is_public: bool = False
    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('El título no puede estar vacío')
        return v

class MatchRequest(BaseModel):
    to_user_id: str
    message: Optional[str] = Field(None, max_length=500)
    preferred_date: Optional[datetime]
    preferred_location: Optional[str] = Field(None, max_length=200)
    @field_validator('message')
    @classmethod
    def message_not_empty_if_provided(cls, v):
        if v is not None and not v.strip():
            raise ValueError('El mensaje no puede estar vacío si se proporciona')
        return v

class MatchSearch(BaseModel):
    location: Optional[str] = Field(None, max_length=200)
    date: Optional[datetime]
    skill_level: Optional[str] = Field(None, pattern='^(beginner|intermediate|advanced|expert)$')
    max_distance: Optional[int] = Field(None, ge=1, le=100)
    @field_validator('max_distance')
    @classmethod
    def validate_distance(cls, v):
        if v is not None and (v < 1 or v > 100):
            raise ValueError('La distancia máxima debe estar entre 1 y 100 km')
        return v

class MatchRating(BaseModel):
    match_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=500)
    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError('La calificación debe estar entre 1 y 5')
        return v

# --- Tests ---

def test_user_registration_validation():
    valid_data = {
        "email": "test@example.com",
        "password": "Test123!@#",
        "name": "Test User"
    }
    user = UserRegistration(**valid_data)
    assert user.email == valid_data["email"]
    assert user.name == valid_data["name"]
    with pytest.raises(ValueError):
        UserRegistration(email="invalid-email", password="Test123!@#", name="Test User")
    with pytest.raises(ValueError):
        UserRegistration(email="test@example.com", password="weak", name="Test User")
    with pytest.raises(ValueError):
        UserRegistration(email="test@example.com", password="Test123!@#", name="A")

def test_video_upload_validation():
    valid_data = {
        "title": "Test Video",
        "description": "Test Description",
        "video_type": "training",
        "is_public": False
    }
    video = VideoUpload(**valid_data)
    assert video.title == valid_data["title"]
    assert video.video_type == valid_data["video_type"]
    with pytest.raises(ValueError):
        VideoUpload(title="", description="Test Description", video_type="training", is_public=False)
    with pytest.raises(ValueError):
        VideoUpload(title="Test Video", description="Test Description", video_type="invalid", is_public=False)

def test_match_request_validation():
    valid_data = {
        "to_user_id": "user123",
        "message": "Let's play!",
        "preferred_date": datetime.now(UTC),
        "preferred_location": "Court 1"
    }
    match = MatchRequest(**valid_data)
    assert match.to_user_id == valid_data["to_user_id"]
    assert match.message == valid_data["message"]
    with pytest.raises(ValueError):
        MatchRequest(to_user_id="user123", message="", preferred_date=datetime.now(UTC), preferred_location="Court 1")

def test_match_search_validation():
    valid_data = {
        "location": "Madrid",
        "date": datetime.now(UTC),
        "skill_level": "intermediate",
        "max_distance": 50
    }
    search = MatchSearch(**valid_data)
    assert search.location == valid_data["location"]
    assert search.max_distance == valid_data["max_distance"]
    with pytest.raises(ValueError):
        MatchSearch(location="Madrid", date=datetime.now(UTC), skill_level="invalid", max_distance=50)
    with pytest.raises(ValueError):
        MatchSearch(location="Madrid", date=datetime.now(UTC), skill_level="intermediate", max_distance=150)

def test_match_rating_validation():
    valid_data = {
        "match_id": "match123",
        "rating": 4,
        "comment": "Great match!"
    }
    rating = MatchRating(**valid_data)
    assert rating.match_id == valid_data["match_id"]
    assert rating.rating == valid_data["rating"]
    with pytest.raises(ValueError):
        MatchRating(match_id="match123", rating=6, comment="Great match!") 