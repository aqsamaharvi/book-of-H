from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from models import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    MessageResponse,
    ErrorResponse,
    UserResponse,
    QuestionnaireRequest,
    QuestionnaireResponse,
    RegistrationSuccessResponse
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
        user = await db.create_user(email=user_data.email, hashed_password=hashed_password)
        
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
    - 201: Questionnaire saved successfully
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
        
        # Save questionnaire
        questionnaire = await db.save_questionnaire(
            user_id=questionnaire_data.user_id,
            answers=answers_dict
        )
        
        return QuestionnaireResponse(
            message="Questionnaire saved successfully",
            questionnaire_id=questionnaire["id"]
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
    - 200: Questionnaire data
    - 404: Questionnaire not found for this user
    """
    questionnaire = await db.get_questionnaire_by_user_id(user_id)
    
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Questionnaire not found for this user"
        )
    
    # Convert datetime objects to strings for JSON serialization
    result = {
        "id": questionnaire.get("id"),
        "user_id": questionnaire.get("user_id"),
        "answers": questionnaire.get("answers"),
        "created_at": questionnaire.get("created_at").isoformat() if questionnaire.get("created_at") else None,
        "updated_at": questionnaire.get("updated_at").isoformat() if questionnaire.get("updated_at") else None
    }
    
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)