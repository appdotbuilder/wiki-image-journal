from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum


class ContactRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"


class MessageStatus(str, Enum):
    SENT = "sent"
    READ = "read"
    DELETED = "deleted"


class ModerationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


# Persistent models (stored in database)
class User(SQLModel, table=True):
    """Registered users who can create journal entries and interact with shared content."""

    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=50, unique=True, index=True)
    email: str = Field(unique=True, max_length=255, regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password_hash: str = Field(max_length=255)
    full_name: str = Field(max_length=100)
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)

    # Relationships
    journal_entries: List["JournalEntry"] = Relationship(back_populates="user")
    sent_likes: List["EntryLike"] = Relationship(back_populates="user")


class WikipediaImage(SQLModel, table=True):
    """Wikipedia Image of the Day cache to avoid repeated API calls."""

    __tablename__ = "wikipedia_images"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    image_date: date = Field(unique=True, index=True)
    title: str = Field(max_length=500)
    description: str = Field(max_length=2000)
    image_url: str = Field(max_length=1000)
    thumbnail_url: Optional[str] = Field(default=None, max_length=1000)
    source_url: str = Field(max_length=1000)
    license_info: str = Field(max_length=500)
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    journal_entries: List["JournalEntry"] = Relationship(back_populates="wikipedia_image")


class JournalEntry(SQLModel, table=True):
    """Daily journal entries written by users inspired by Wikipedia Image of the Day."""

    __tablename__ = "journal_entries"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    wikipedia_image_id: int = Field(foreign_key="wikipedia_images.id", index=True)
    entry_date: date = Field(index=True)
    title: str = Field(max_length=200)
    content: str = Field(max_length=5000)
    is_shared: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="journal_entries")
    wikipedia_image: WikipediaImage = Relationship(back_populates="journal_entries")
    shared_entry: Optional["SharedEntry"] = Relationship(back_populates="journal_entry")


class SharedEntry(SQLModel, table=True):
    """Shared journal entries that other users can view and like."""

    __tablename__ = "shared_entries"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    journal_entry_id: int = Field(foreign_key="journal_entries.id", unique=True, index=True)
    moderation_status: ModerationStatus = Field(default=ModerationStatus.PENDING, index=True)
    moderated_by: Optional[int] = Field(default=None, foreign_key="users.id")
    moderated_at: Optional[datetime] = Field(default=None)
    moderation_notes: Optional[str] = Field(default=None, max_length=1000)
    shared_at: datetime = Field(default_factory=datetime.utcnow)
    view_count: int = Field(default=0)
    like_count: int = Field(default=0)

    # Relationships
    journal_entry: JournalEntry = Relationship(back_populates="shared_entry")
    moderator: Optional[User] = Relationship()
    likes: List["EntryLike"] = Relationship(back_populates="shared_entry")


class EntryLike(SQLModel, table=True):
    """Likes given by users to shared journal entries."""

    __tablename__ = "entry_likes"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    shared_entry_id: int = Field(foreign_key="shared_entries.id", index=True)
    liked_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="sent_likes")
    shared_entry: SharedEntry = Relationship(back_populates="likes")


class ContactRequest(SQLModel, table=True):
    """Requests to contact authors of liked shared entries."""

    __tablename__ = "contact_requests"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    requester_id: int = Field(foreign_key="users.id", index=True)
    requested_id: int = Field(foreign_key="users.id", index=True)
    shared_entry_id: int = Field(foreign_key="shared_entries.id", index=True)
    status: ContactRequestStatus = Field(default=ContactRequestStatus.PENDING, index=True)
    message: Optional[str] = Field(default=None, max_length=500)
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    responded_at: Optional[datetime] = Field(default=None)
    response_message: Optional[str] = Field(default=None, max_length=500)

    # Relationships - we'll handle these without back_populates for now to avoid conflicts
    shared_entry: SharedEntry = Relationship()


class Message(SQLModel, table=True):
    """In-app messages between users who have established contact permission."""

    __tablename__ = "messages"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    sender_id: int = Field(foreign_key="users.id", index=True)
    recipient_id: int = Field(foreign_key="users.id", index=True)
    contact_request_id: int = Field(foreign_key="contact_requests.id", index=True)
    subject: str = Field(max_length=200)
    content: str = Field(max_length=2000)
    status: MessageStatus = Field(default=MessageStatus.SENT, index=True)
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = Field(default=None)
    deleted_by_sender: bool = Field(default=False)
    deleted_by_recipient: bool = Field(default=False)

    # Relationships - we'll handle these without back_populates for now to avoid conflicts
    contact_request: ContactRequest = Relationship()


class AdminLog(SQLModel, table=True):
    """Log of admin actions for moderation and system management."""

    __tablename__ = "admin_logs"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    admin_user_id: int = Field(foreign_key="users.id", index=True)
    action_type: str = Field(max_length=100, index=True)
    target_type: str = Field(max_length=100)  # e.g., "shared_entry", "user", "message"
    target_id: int = Field()
    description: str = Field(max_length=1000)
    log_metadata: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    admin_user: User = Relationship()


# Non-persistent schemas (for validation, forms, API requests/responses)
class UserCreate(SQLModel, table=False):
    """Schema for user registration."""

    username: str = Field(max_length=50)
    email: str = Field(max_length=255)
    password: str = Field(max_length=100)
    full_name: str = Field(max_length=100)


class UserLogin(SQLModel, table=False):
    """Schema for user authentication."""

    username: str = Field(max_length=50)
    password: str = Field(max_length=100)


class JournalEntryCreate(SQLModel, table=False):
    """Schema for creating a new journal entry."""

    title: str = Field(max_length=200)
    content: str = Field(max_length=5000)
    is_shared: bool = Field(default=False)


class JournalEntryUpdate(SQLModel, table=False):
    """Schema for updating an existing journal entry."""

    title: Optional[str] = Field(default=None, max_length=200)
    content: Optional[str] = Field(default=None, max_length=5000)
    is_shared: Optional[bool] = Field(default=None)


class ContactRequestCreate(SQLModel, table=False):
    """Schema for creating a contact request."""

    requested_id: int
    shared_entry_id: int
    message: Optional[str] = Field(default=None, max_length=500)


class ContactRequestResponse(SQLModel, table=False):
    """Schema for responding to a contact request."""

    status: ContactRequestStatus
    response_message: Optional[str] = Field(default=None, max_length=500)


class MessageCreate(SQLModel, table=False):
    """Schema for creating a new message."""

    recipient_id: int
    contact_request_id: int
    subject: str = Field(max_length=200)
    content: str = Field(max_length=2000)


class ModerationAction(SQLModel, table=False):
    """Schema for moderation actions."""

    status: ModerationStatus
    notes: Optional[str] = Field(default=None, max_length=1000)


class WikipediaImageResponse(SQLModel, table=False):
    """Schema for Wikipedia Image API response."""

    image_date: date
    title: str
    description: str
    image_url: str
    thumbnail_url: Optional[str] = Field(default=None)
    source_url: str
    license_info: str
