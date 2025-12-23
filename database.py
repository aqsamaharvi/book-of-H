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
    
    async def create_user(self, email: str, hashed_password: str, first_name: str, last_name: str) -> dict:
        """Create a new user"""
        user_id = str(uuid.uuid4())
        
        # Generate unique username
        base_username = f"{first_name.lower()}{last_name.lower()}".replace(" ", "")
        username = base_username
        counter = 1
        while await self.username_exists(username):
            username = f"{base_username}{counter}"
            counter += 1
            
        user_doc = {
            "id": user_id,
            "email": email,
            "hashed_password": hashed_password,
            "name": f"{first_name} {last_name}",
            "username": username,
            "bio": "Welcome to hGram!",
            "location": "",
            "posts_count": 0,
            "followers_count": 0,
            "following_count": 0,
            "created_at": datetime.utcnow()
        }
        
        await self.db.users.insert_one(user_doc)
        user_doc["_id"] = str(user_doc["_id"])
        return user_doc

    async def update_user(self, user_id: str, update_data: dict) -> Optional[dict]:
        """Update user profile"""
        await self.db.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        return await self.get_user_by_id(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email"""
        user = await self.db.users.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID"""
        user = await self.db.users.find_one({"id": user_id})
        if user:
            user["_id"] = str(user["_id"])
        return user
    
    async def user_exists(self, email: str) -> bool:
        """Check if user exists"""
        count = await self.db.users.count_documents({"email": email})
        return count > 0

    async def username_exists(self, username: str, exclude_user_id: Optional[str] = None) -> bool:
        """Check if username already exists"""
        query = {"username": username}
        if exclude_user_id:
            query["id"] = {"$ne": exclude_user_id}
        count = await self.db.users.count_documents(query)
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
        if questionnaire:
            questionnaire["_id"] = str(questionnaire["_id"])
        return questionnaire
    
    async def clear_all(self):
        """Clear all users and questionnaires (for testing only)"""
        await self.db.users.delete_many({})
        await self.db.questionnaires.delete_many({})
        await self.db.posts.delete_many({})

    # MARK: - Posts
    async def create_post(self, user_id: str, content: str, image: Optional[str] = None, category: str = "Discussion") -> dict:
        """Create a new post"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise Exception("User not found")
            
        post_id = str(uuid.uuid4())
        post_doc = {
            "id": post_id,
            "author_id": user_id,
            "author_name": user.get("name", "User"),
            "author_avatar": "person.circle.fill",
            "content": content,
            "image": image,
            "category": category,
            "likes": 0,
            "comments": 0,
            "created_at": datetime.utcnow().isoformat()
        }
        
        await self.db.posts.insert_one(post_doc)
        post_doc["_id"] = str(post_doc["_id"])
        return post_doc

    async def get_posts(self, limit: int = 20) -> List[dict]:
        """Get latest posts"""
        cursor = self.db.posts.find().sort("created_at", -1).limit(limit)
        posts = await cursor.to_list(length=limit)
        for post in posts:
            post["_id"] = str(post["_id"])
        return posts

    async def get_user_posts(self, user_id: str) -> List[dict]:
        """Get posts by user ID"""
        cursor = self.db.posts.find({"author_id": user_id}).sort("created_at", -1)
        posts = await cursor.to_list(length=100)
        for post in posts:
            post["_id"] = str(post["_id"])
        return posts

    # MARK: - Shelves/Saved Posts
    async def save_post_to_shelf(self, user_id: str, post_id: str, category: str) -> dict:
        """Save a post to a user's shelf or update category if already saved"""
        update_doc = {
            "user_id": user_id,
            "post_id": post_id,
            "shelf_category": category,
            "saved_at": datetime.utcnow().isoformat()
        }
        
        # Use upsert to update if exists, or insert if new
        await self.db.saved_posts.update_one(
            {"user_id": user_id, "post_id": post_id},
            {"$set": update_doc},
            upsert=True
        )
        
        # Return the post with the shelf category added
        post = await self.db.posts.find_one({"id": post_id})
        if post:
            post["_id"] = str(post["_id"])
            post["shelf_category"] = category
            return post
        raise Exception("Post not found")

    async def get_saved_posts(self, user_id: str) -> List[dict]:
        """Get all saved posts for a user"""
        cursor = self.db.saved_posts.find({"user_id": user_id}).sort("saved_at", -1)
        saved_docs = await cursor.to_list(length=100)
        
        posts = []
        for doc in saved_docs:
            post = await self.db.posts.find_one({"id": doc["post_id"]})
            if post:
                post["_id"] = str(post["_id"])
                post["shelf_category"] = doc["shelf_category"]
                posts.append(post)
        return posts


# Global database instance
db = MongoDatabase()


async def get_database() -> MongoDatabase:
    """Dependency injection for database"""
    return db

