from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from typing import List, Dict, Optional
from models import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    MessageResponse,
    ErrorResponse,
    UserResponse,
    QuestionnaireRequest,
    QuestionnaireResponse,
    QuestionnaireDataResponse,
    RegistrationSuccessResponse,
    ProfileUpdateRequest,
    UsernameCheckResponse,
    PostCreateRequest,
    PostResponse as APIPostResponse
)
from database import get_database, MongoDatabase, db
from auth import hash_password, verify_password, create_access_token
from datetime import timedelta
from config import settings

app = FastAPI(
    title="hGram Auth API",
    description="Authentication API for hGram iOS App",
    version="1.0.0"
)

# CORS configuration for iOS app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_db_client():
    """Connect to MongoDB on startup"""
    await db.connect()


@app.on_event("shutdown")
async def shutdown_db_client():
    """Disconnect from MongoDB on shutdown"""
    await db.disconnect()


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "hGram Auth API is running"}


@app.post(
    "/api/auth/register",
    response_model=RegistrationSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Account created successfully"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        409: {"model": ErrorResponse, "description": "User already exists"}
    },
    tags=["Authentication"]
)
async def register(
    user_data: UserRegisterRequest,
    db: MongoDatabase = Depends(get_database)
):
    """
    Register a new user account
    
    **Validation Rules:**
    - Email must be a valid email format
    - Password must be at least 8 characters
    - Password must contain at least one uppercase letter
    - Password must contain at least one lowercase letter
    - Password must contain at least one number
    
    **Returns:**
    - 201: Account created successfully
    - 400: Validation error (invalid email or password format)
    - 409: User with this email already exists
    """
    try:
        # Check if user already exists
        if await db.user_exists(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        
        # Hash the password
        hashed_password = hash_password(user_data.password)
        
        # Create user in database
        user = await db.create_user(
            email=user_data.email, 
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        
        return RegistrationSuccessResponse(
            message="Account created successfully",
            user_id=user["id"],
            email=user["email"]
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the account"
        )


@app.post(
    "/api/auth/login",
    response_model=TokenResponse,
    responses={
        200: {"description": "Login successful"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"}
    },
    tags=["Authentication"]
)
async def login(
    credentials: UserLoginRequest,
    db: MongoDatabase = Depends(get_database)
):
    """
    Login with email and password
    
    **Returns:**
    - 200: JWT access token
    - 401: Invalid email or password
    """
    # Get user from database
    user = await db.get_user_by_email(credentials.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user["email"], "user_id": user["id"]}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user["id"],
        email=user["email"]
    )


from scoring_config import calculate_score

@app.post(
    "/api/questionnaire/submit",
    response_model=QuestionnaireResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Questionnaire saved successfully"},
        404: {"model": ErrorResponse, "description": "User not found"},
        400: {"model": ErrorResponse, "description": "Invalid questionnaire data"}
    },
    tags=["Questionnaire"]
)
async def submit_questionnaire(
    questionnaire_data: QuestionnaireRequest,
    db: MongoDatabase = Depends(get_database)
):
    """
    Submit or update questionnaire responses for a user
    
    **Request Body:**
    - user_id: The ID of the user submitting the questionnaire
    - answers: List of answers with question_id, question_text, and selected_options
    
    **Returns:**
    - 201: Questionnaire saved successfully with score and band
    - 404: User not found
    - 400: Invalid questionnaire data
    """
    try:
        # Verify user exists
        user = await db.get_user_by_id(questionnaire_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Convert answers to dict format for storage
        answers_dict = [answer.model_dump() for answer in questionnaire_data.answers]
        
        # Calculate score
        score, band, cat_scores = calculate_score(answers_dict)
        
        # Save questionnaire
        questionnaire = await db.save_questionnaire(
            user_id=questionnaire_data.user_id,
            answers=answers_dict,
            score=score,
            band=band,
            category_scores=cat_scores
        )
        
        return QuestionnaireResponse(
            message="Questionnaire saved successfully",
            questionnaire_id=questionnaire["id"],
            score=score,
            band=band,
            category_scores=cat_scores
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while saving the questionnaire: {str(e)}"
        )


@app.get(
    "/api/questionnaire/{user_id}",
    response_model=QuestionnaireDataResponse,
    responses={
        200: {"description": "Questionnaire retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Questionnaire not found"}
    },
    tags=["Questionnaire"]
)
async def get_questionnaire(
    user_id: str,
    db: MongoDatabase = Depends(get_database)
):
    """
    Get questionnaire responses for a user
    
    **Returns:**
    - 200: Questionnaire data including score and band
    - 404: Questionnaire not found for this user
    """
    questionnaire = await db.get_questionnaire_by_user_id(user_id)
    
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Questionnaire not found for this user"
        )
    
    # Convert datetime objects to strings for JSON serialization
    return QuestionnaireDataResponse(
        id=questionnaire.get("id"),
        user_id=questionnaire.get("user_id"),
        answers=questionnaire.get("answers"),
        score=questionnaire.get("score", 0),
        band=questionnaire.get("band", "Beginner"),
        category_scores=questionnaire.get("category_scores"),
        created_at=questionnaire.get("created_at").isoformat() if questionnaire.get("created_at") else None,
        updated_at=questionnaire.get("updated_at").isoformat() if questionnaire.get("updated_at") else None
    )


from fastapi.security import OAuth2PasswordBearer
from auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

async def get_current_user_id(token: Optional[str] = Depends(oauth2_scheme)) -> str:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload.get("user_id")

@app.get(
    "/api/user/profile",
    response_model=UserResponse,
    tags=["User"]
)
async def get_user_profile(
    user_id: str = Depends(get_current_user_id),
    db: MongoDatabase = Depends(get_database)
):
    """Get current user's profile"""
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Fetch questionnaire data to get latest score and band
    questionnaire = await db.get_questionnaire_by_user_id(user_id)
    if questionnaire:
        user["score"] = questionnaire.get("score", 0)
        user["band"] = questionnaire.get("band", "Beginner")
    else:
        user["score"] = 0
        user["band"] = "Beginner"
        
    return user

@app.get("/api/user/saved-posts", tags=["User"])
async def get_user_saved_posts(
    user_id: str = Depends(get_current_user_id),
    db: MongoDatabase = Depends(get_database)
):
    """Get current user's saved posts from database"""
    posts = await db.get_saved_posts(user_id)
    return posts

@app.post("/api/posts/{post_id}/save", tags=["Posts"])
async def save_post_to_shelf(
    post_id: str,
    shelf_data: Dict[str, str],
    user_id: str = Depends(get_current_user_id),
    db: MongoDatabase = Depends(get_database)
):
    """Save a post to a specific shelf category (Have, Had, Want)"""
    category = shelf_data.get("shelf_category", "Want")
    try:
        post = await db.save_post_to_shelf(user_id, post_id, category)
        return post
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/posts/{post_id}/like", tags=["Posts"])
async def like_post(
    post_id: str,
    user_id: str = Depends(get_current_user_id),
    db: MongoDatabase = Depends(get_database)
):
    """Like or unlike a post"""
    try:
        post = await db.like_post(user_id, post_id)
        return post
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# MARK: - Posts Endpoints
@app.post(
    "/api/posts",
    response_model=APIPostResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Posts"]
)
async def create_post(
    post_data: PostCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: MongoDatabase = Depends(get_database)
):
    """Create a new post"""
    try:
        post = await db.create_post(
            user_id=user_id,
            content=post_data.content,
            image=post_data.image,
            category=post_data.category
        )
        return post
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

async def get_optional_user_id(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    """Helper to get user_id from token if present, but doesn't fail if not"""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        return payload.get("user_id") if payload else None
    except:
        return None

@app.get(
    "/api/posts",
    response_model=List[APIPostResponse],
    tags=["Posts"]
)
async def get_all_posts(
    user_id: Optional[str] = Depends(get_optional_user_id),
    db: MongoDatabase = Depends(get_database)
):
    """Get all posts for the feed, with saved status if logged in"""
    posts = await db.get_posts(user_id=user_id)
    return posts

@app.get("/api/user/posts", tags=["User"])
async def get_user_posts(
    user_id: str = Depends(get_current_user_id),
    db: MongoDatabase = Depends(get_database)
):
    """Get current user's posts from database"""
    posts = await db.get_user_posts(user_id)
    return posts

@app.post(
    "/api/user/profile/update",
    response_model=UserResponse,
    tags=["User"]
)
async def update_profile(
    update_data: ProfileUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: MongoDatabase = Depends(get_database)
):
    """Update current user's profile"""
    # Check if username is being changed and if it's unique
    if update_data.username:
        if await db.username_exists(update_data.username, exclude_user_id=user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken"
            )
    
    # Remove None values from update dict
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if not update_dict:
        # If nothing to update, just return the profile
        return await get_user_profile(user_id, db)
    
    user = await db.update_user(user_id, update_dict)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@app.get(
    "/api/user/username-check/{username}",
    response_model=UsernameCheckResponse,
    tags=["User"]
)
async def check_username(
    username: str,
    user_id: str = Depends(get_current_user_id),
    db: MongoDatabase = Depends(get_database)
):
    """Check if a username is unique"""
    is_taken = await db.username_exists(username, exclude_user_id=user_id)
    if is_taken:
        return UsernameCheckResponse(
            is_available=False,
            message="Username is already taken"
        )
    else:
        return UsernameCheckResponse(
            is_available=True,
            message="Username is available"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)