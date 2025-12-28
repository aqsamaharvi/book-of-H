import asyncio
from database import db

async def check_posts():
    await db.connect()
    posts = await db.db.posts.find().to_list(length=100)
    print(f"Total posts: {len(posts)}")
    for p in posts:
        print(f"ID: {p.get('id')} | Type: {p.get('post_type')} | Author: {p.get('author_name')} | Title: {p.get('title')}")
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(check_posts())

