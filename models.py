from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Set
import re


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate password requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    email: str
    id: str
    name: Optional[str] = "New User"
    username: Optional[str] = "user"
    bio: Optional[str] = ""
    location: Optional[str] = ""
    posts_count: int = 0
    followers_count: int = 0
    following_count: int = 0
    score: Optional[int] = 0
    band: Optional[str] = "Beginner"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class MessageResponse(BaseModel):
    message: str


class RegistrationSuccessResponse(BaseModel):
    message: str
    user_id: str
    email: str


class ErrorResponse(BaseModel):
    detail: str


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None


class UsernameCheckResponse(BaseModel):
    is_available: bool
    message: str


class PostCreateRequest(BaseModel):
    content: str
    image: Optional[str] = None
    category: Optional[str] = "Discussion"


class CommentResponse(BaseModel):
    id: str
    post_id: str
    author_id: str
    author_name: str
    author_avatar: str
    content: str
    likes: int = 0
    is_liked: bool = False
    created_at: str

class PostResponse(BaseModel):
    id: str
    author_id: str
    author_name: str
    author_avatar: str
    content: str
    image: Optional[str] = None
    category: str
    likes: int = 0
    comments: int = 0
    created_at: str
    is_following: bool = False
    is_liked: bool = False
    shelf_category: Optional[str] = None
    recent_comments: List[CommentResponse] = []

class CommentCreateRequest(BaseModel):
    content: str


class QuestionnaireAnswer(BaseModel):
    """Single questionnaire answer"""
    question_id: str
    question_text: str
    selected_options: List[str]


class QuestionnaireRequest(BaseModel):
    """Request model for submitting questionnaire responses"""
    user_id: str
    answers: List[QuestionnaireAnswer]


class QuestionnaireResponse(BaseModel):
    """Response model after saving questionnaire"""
    message: str
    questionnaire_id: str
    score: Optional[int] = None
    band: Optional[str] = None
    category_scores: Optional[Dict[str, int]] = None


class QuestionnaireDataResponse(BaseModel):
    """Full questionnaire data including scores"""
    id: str
    user_id: str
    answers: List[QuestionnaireAnswer]
    score: int
    band: str
    category_scores: Optional[Dict[str, float]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

