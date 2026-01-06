from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db, AsyncSessionLocal
from auth import router as auth_router
from models import User
from sqlmodel import select
import os
from datetime import datetime

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()

    # Optionally ensure admin exists on startup
    if os.getenv("INIT_ADMIN", "true").lower() in ("1", "true", "yes"):  # default enabled
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(User).where(User.email == "admin@test.com"))
                admin = result.scalars().first()
                if not admin:
                    admin = User(
                        email="admin@test.com",
                        name="Admin User",
                        email_verified=int(datetime.now().timestamp() * 1000),
                    )
                    admin.set_password("123456")
                    session.add(admin)
                    await session.commit()
                    print("✅ Admin user auto-created: admin@test.com / 123456")
        except Exception as e:
            print(f"⚠️ Failed to ensure admin on startup: {e}")

    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router, prefix="/api", tags=["auth"])

@app.get("/")
def read_root():
    return {"Hello": "World"}