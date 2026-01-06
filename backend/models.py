from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
import uuid
from passlib.context import CryptContext

# Base model for timestamps
class TimestampMixin(SQLModel):
    created_at: int = Field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    updated_at: int = Field(default_factory=lambda: int(datetime.now().timestamp() * 1000))

# Password hashing context - use sha256_crypt as fallback since bcrypt has issues
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# User model
class User(TimestampMixin, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: Optional[str] = None
    email: str = Field(index=True, unique=True)
    email_verified: Optional[int] = None  # timestamp in milliseconds
    image: Optional[str] = None
    password_hash: Optional[str] = None

    # Relationships
    accounts: List["Account"] = Relationship(back_populates="user")
    sessions: List["Session"] = Relationship(back_populates="user")
    subscriptions: List["Subscription"] = Relationship(back_populates="user")

    def set_password(self, password: str):
        """Set password by hashing it"""
        # Ensure password is not too long for bcrypt (max 72 bytes)
        if len(password.encode('utf-8')) > 72:
            password = password[:72]  # Truncate to 72 bytes
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        if self.password_hash is None:
            return False
        return pwd_context.verify(password, self.password_hash)

# Account model (for OAuth)
class Account(SQLModel, table=True):
    user_id: str = Field(foreign_key="user.id")
    type: str
    provider: str = Field(primary_key=True)
    provider_account_id: str = Field(primary_key=True)
    refresh_token: Optional[str] = None
    access_token: Optional[str] = None
    expires_at: Optional[int] = None  # timestamp in milliseconds
    token_type: Optional[str] = None
    scope: Optional[str] = None
    id_token: Optional[str] = None
    session_state: Optional[str] = None

    # Relationships
    user: User = Relationship(back_populates="accounts")

# Session model
class Session(SQLModel, table=True):
    session_token: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    expires: int  # timestamp in milliseconds

    # Relationships
    user: User = Relationship(back_populates="sessions")

# Verification token model
class VerificationToken(SQLModel, table=True):
    identifier: str = Field(primary_key=True)
    token: str = Field(primary_key=True)
    expires: int  # timestamp in milliseconds

# Subscription model (Lemon Squeezy)
class Subscription(TimestampMixin, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    lemon_squeezy_id: str = Field(unique=True)  # Lemon Squeezy subscription ID
    order_id: str  # Lemon Squeezy order ID
    name: str  # Subscription plan name
    email: str  # Customer email
    status: str  # on_trial, active, paused, past_due, unpaid, cancelled, expired
    status_formatted: str  # Human-readable status
    renews_at: Optional[int] = None  # Next renewal date (timestamp in milliseconds)
    ends_at: Optional[int] = None  # End date for cancelled subscriptions (timestamp in milliseconds)
    trial_ends_at: Optional[int] = None  # Trial end date (timestamp in milliseconds)
    price: str  # Price (as string to handle decimals)
    is_usage_based: bool = False
    is_paused: bool = False
    subscription_item_id: Optional[str] = None  # For usage-based billing

    # Relationships
    user: User = Relationship(back_populates="subscriptions")