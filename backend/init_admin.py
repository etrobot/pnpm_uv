#!/usr/bin/env python3
"""
Admin initialization script.
This script creates an admin user with the specified credentials.
"""

import asyncio
from models import User
from database import AsyncSessionLocal
from sqlmodel import select
from datetime import datetime

async def create_admin_user():
    email = "admin@test.com"
    password = "123456"
    name = "Admin User"

    async with AsyncSessionLocal() as session:
        # Check if admin user already exists
        result = await session.execute(select(User).where(User.email == email))
        existing_user = result.scalars().first()

        if existing_user:
            print(f"⚠️  Admin user already exists: {existing_user.email}")
            return

        # Create new admin user
        admin_user = User(
            email=email,
            name=name,
            email_verified=int(datetime.now().timestamp() * 1000)
        )
        admin_user.set_password(password)

        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)

        print(f"✅ Admin user created successfully!")
        print(f"   Email: {admin_user.email}")
        print(f"   Password: {password}")
        print(f"   User ID: {admin_user.id}")

if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(create_admin_user())