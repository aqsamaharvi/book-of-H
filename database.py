from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional, List
from datetime import datetime
import uuid
from config import settings


class MongoDatabase:
    """MongoDB implementation for user and questionnaire storage"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.db = self.client[settings.DATABASE_NAME]
            # Test the connection
            await self.client.admin.command('ping')
            print(f"✅ Connected to MongoDB database: {settings.DATABASE_NAME}")
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")
    
    async def create_user(self, email: str, hashed_password: str) -> dict:
        """Create a new user"""
        user_id = str(uuid.uuid4())
        user_doc = {
            "id": user_id,
            "email": email,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow()
        }
        
        await self.db.users.insert_one(user_doc)
        return user_doc
    
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email"""
        user = await self.db.users.find_one({"email": email})
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID"""
        user = await self.db.users.find_one({"id": user_id})
        return user
    
    async def user_exists(self, email: str) -> bool:
        """Check if user exists"""
        count = await self.db.users.count_documents({"email": email})
        return count > 0
    
    async def save_questionnaire(self, user_id: str, answers: List[dict], score: int = 0, band: str = "", category_scores: dict = None) -> dict:
        """Save or update questionnaire for a user"""
        questionnaire_id = str(uuid.uuid4())
        
        # Check if questionnaire exists for user
        existing = await self.db.questionnaires.find_one({"user_id": user_id})
        
        if existing:
            # Update existing questionnaire
            await self.db.questionnaires.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "answers": answers,
                        "score": score,
                        "band": band,
                        "category_scores": category_scores,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            questionnaire_id = existing.get("id", questionnaire_id)
        else:
            # Create new questionnaire
            questionnaire_doc = {
                "id": questionnaire_id,
                "user_id": user_id,
                "answers": answers,
                "score": score,
                "band": band,
                "category_scores": category_scores,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await self.db.questionnaires.insert_one(questionnaire_doc)
        
        return {
            "id": questionnaire_id,
            "user_id": user_id,
            "answers": answers,
            "score": score,
            "band": band,
            "category_scores": category_scores
        }
    
    async def get_questionnaire_by_user_id(self, user_id: str) -> Optional[dict]:
        """Get questionnaire by user ID"""
        questionnaire = await self.db.questionnaires.find_one({"user_id": user_id})
        return questionnaire
    
    async def clear_all(self):
        """Clear all users and questionnaires (for testing only)"""
        await self.db.users.delete_many({})
        await self.db.questionnaires.delete_many({})


# Global database instance
db = MongoDatabase()


async def get_database() -> MongoDatabase:
    """Dependency injection for database"""
    return db

