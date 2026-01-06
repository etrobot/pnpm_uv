#!/usr/bin/env python3
"""
Database initialization script.
This script creates the database tables and can be used to reset the database.
"""

import asyncio
from sqlmodel import SQLModel
from sqlmodel.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

async def create_database():
    # Use a synchronous engine for initialization
    sync_engine = create_async_engine(
        "sqlite+aiosqlite:///./database.db",
        echo=True,
        poolclass=StaticPool,
    )

    async with sync_engine.begin() as conn:
        # Import all models to register them
        from models import User, Account, Session, VerificationToken, Subscription
        await conn.run_sync(SQLModel.metadata.create_all)
        print("✅ Database tables created successfully!")

async def reset_database():
    """Drop all tables and recreate them"""
    sync_engine = create_async_engine(
        "sqlite+aiosqlite:///./database.db",
        echo=True,
        poolclass=StaticPool,
    )

    async with sync_engine.begin() as conn:
        # Import all models to register them
        from models import User, Account, Session, VerificationToken, Subscription
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
        print("✅ Database reset successfully!")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database initialization tool")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables")

    args = parser.parse_args()

    if args.reset:
        print("🔄 Resetting database...")
        asyncio.run(reset_database())
    else:
        print("🚀 Creating database tables...")
        asyncio.run(create_database())