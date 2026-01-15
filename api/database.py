"""
Database connection and SQLAlchemy models for Epitome.
Connects to Supabase PostgreSQL using async SQLAlchemy.
"""
import os
from datetime import datetime
from typing import AsyncGenerator
import uuid

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, ForeignKey, Numeric, Boolean, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from dotenv import load_dotenv

load_dotenv()

# Get database URLs - prefer DIRECT_URL for asyncpg (avoids pgbouncer issues)
DIRECT_URL = os.getenv("DIRECT_URL", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Use DIRECT_URL if available (bypasses pgbouncer), otherwise fall back to DATABASE_URL
db_url = DIRECT_URL or DATABASE_URL

if db_url:
    # Convert to async format
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    # Remove pgbouncer params if present
    if "?pgbouncer=true" in db_url:
        db_url = db_url.replace("?pgbouncer=true", "")

# Create async engine with statement cache disabled (for pgbouncer compatibility)
engine = create_async_engine(
    db_url,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,
    connect_args={
        "statement_cache_size": 0,  # Disable prepared statement caching for pgbouncer
    } if db_url else {},
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


def generate_cuid() -> str:
    """Generate a CUID-like ID."""
    return str(uuid.uuid4())


# =============================================================================
# PostgreSQL Enums (matching Prisma schema exactly)
# =============================================================================

# Department enum
DepartmentEnum = PgEnum(
    'PRODUCTION', 'CAMERA', 'GRIP_ELECTRIC', 'ART', 'WARDROBE',
    'HAIR_MAKEUP', 'SOUND', 'LOCATIONS', 'TRANSPORTATION',
    'CATERING', 'POST_PRODUCTION', 'OTHER',
    name='Department',
    create_type=False
)

# UnionStatus enum - matches Prisma: NON_UNION, IATSE, TEAMSTERS, SAG_AFTRA, DGA
UnionStatusEnum = PgEnum(
    'NON_UNION', 'IATSE', 'TEAMSTERS', 'SAG_AFTRA', 'DGA',
    name='UnionStatus',
    create_type=False
)

# ProjectStatus enum - matches Prisma: BID, AWARDED, ACTIVE, WRAPPED, CLOSED
ProjectStatusEnum = PgEnum(
    'BID', 'AWARDED', 'ACTIVE', 'WRAPPED', 'CLOSED',
    name='ProjectStatus',
    create_type=False
)

# CallSheetStatus enum - matches Prisma: DRAFT, REVIEW, APPROVED, DISTRIBUTED
CallSheetStatusEnum = PgEnum(
    'DRAFT', 'REVIEW', 'APPROVED', 'DISTRIBUTED',
    name='CallSheetStatus',
    create_type=False
)

# DealType enum - matches Prisma: DAY_RATE, WEEKLY_RATE, FLAT_FEE, HOURLY
DealTypeEnum = PgEnum(
    'DAY_RATE', 'WEEKLY_RATE', 'FLAT_FEE', 'HOURLY',
    name='DealType',
    create_type=False
)

# CrewStatus enum - matches Prisma: HOLD, CONFIRMED, CANCELLED, WRAPPED
CrewStatusEnum = PgEnum(
    'HOLD', 'CONFIRMED', 'CANCELLED', 'WRAPPED',
    name='CrewStatus',
    create_type=False
)

# RSVPStatus enum - matches Prisma (note: RSVPStatus not RsvpStatus)
RSVPStatusEnum = PgEnum(
    'PENDING', 'SENT', 'VIEWED', 'CONFIRMED', 'DECLINED',
    name='RSVPStatus',
    create_type=False
)

# ScheduleEventType enum - matches Prisma (note: not EventType)
ScheduleEventTypeEnum = PgEnum(
    'CREW_CALL', 'TALENT_CALL', 'MEAL', 'SHOOT', 'COMPANY_MOVE', 'GENERAL',
    name='ScheduleEventType',
    create_type=False
)


# =============================================================================
# SQLAlchemy Models (matching Prisma schema)
# =============================================================================

class Organization(Base):
    """Multi-tenant organization."""
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    defaultInsuranceRate: Mapped[float] = mapped_column(Numeric(5, 4), default=0.03)
    defaultPayrollTaxRate: Mapped[float] = mapped_column(Numeric(5, 4), default=0.23)
    defaultWorkersCompRate: Mapped[float] = mapped_column(Numeric(5, 4), default=0.02)
    defaultAgencyFeeRate: Mapped[float] = mapped_column(Numeric(5, 4), default=0.17)

    # Relationships
    projects: Mapped[list["Project"]] = relationship(back_populates="organization")
    crew_members: Mapped[list["CrewMember"]] = relationship(back_populates="organization")
    clients: Mapped[list["Client"]] = relationship(back_populates="organization")


class Project(Base):
    """Production project."""
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    status: Mapped[str] = mapped_column(ProjectStatusEnum, default="ACTIVE")
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    jobNumber: Mapped[str] = mapped_column(String, nullable=False)
    jobName: Mapped[str] = mapped_column(String, nullable=False)
    client: Mapped[str] = mapped_column(String, nullable=False)  # Legacy field for backward compatibility
    clientId: Mapped[str | None] = mapped_column(String, ForeignKey("clients.id"), nullable=True)
    agency: Mapped[str | None] = mapped_column(String, nullable=True)
    brand: Mapped[str | None] = mapped_column(String, nullable=True)
    bidDate: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    awardDate: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    prepStartDate: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    shootStartDate: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    shootEndDate: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    wrapDate: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    organizationId: Mapped[str] = mapped_column(String, ForeignKey("organizations.id"), nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="projects")
    client_relation: Mapped["Client | None"] = relationship("Client", foreign_keys=[clientId])
    call_sheets: Mapped[list["CallSheet"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    project_crew: Mapped[list["ProjectCrew"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    locations: Mapped[list["Location"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class CallSheet(Base):
    """Daily call sheet for a project."""
    __tablename__ = "call_sheets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    dayNumber: Mapped[int] = mapped_column(Integer, nullable=False)
    shootDate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(CallSheetStatusEnum, default="DRAFT")
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    generalCrewCall: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    firstShot: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    estimatedWrap: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    weatherHigh: Mapped[str | None] = mapped_column(String, nullable=True)
    weatherLow: Mapped[str | None] = mapped_column(String, nullable=True)
    weatherSummary: Mapped[str | None] = mapped_column(String, nullable=True)
    sunrise: Mapped[str | None] = mapped_column(String, nullable=True)
    sunset: Mapped[str | None] = mapped_column(String, nullable=True)
    nearestHospital: Mapped[str | None] = mapped_column(String, nullable=True)
    hospitalAddress: Mapped[str | None] = mapped_column(String, nullable=True)
    emergencyContact: Mapped[str | None] = mapped_column(String, nullable=True)
    emergencyPhone: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    projectId: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="call_sheets")
    rsvps: Mapped[list["CallSheetRsvp"]] = relationship(back_populates="call_sheet", cascade="all, delete-orphan")
    schedule_events: Mapped[list["ScheduleEvent"]] = relationship(back_populates="call_sheet", cascade="all, delete-orphan")


class CrewMember(Base):
    """Master crew database (the Rolodex)."""
    __tablename__ = "crew_members"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    firstName: Mapped[str] = mapped_column(String, nullable=False)
    lastName: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    department: Mapped[str | None] = mapped_column(DepartmentEnum, nullable=True)
    primaryRole: Mapped[str | None] = mapped_column(String, nullable=True)
    defaultRate: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    unionStatus: Mapped[str] = mapped_column(UnionStatusEnum, default="NON_UNION")
    organizationId: Mapped[str] = mapped_column(String, ForeignKey("organizations.id"), nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="crew_members")
    project_assignments: Mapped[list["ProjectCrew"]] = relationship(back_populates="crew_member")


class ProjectCrew(Base):
    """Crew assignment to a specific project."""
    __tablename__ = "project_crew"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    role: Mapped[str] = mapped_column(String, nullable=False)
    department: Mapped[str] = mapped_column(DepartmentEnum, nullable=False)
    dealRate: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    dealType: Mapped[str] = mapped_column(DealTypeEnum, default="DAY_RATE")
    status: Mapped[str] = mapped_column(CrewStatusEnum, default="HOLD")
    projectId: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    crewMemberId: Mapped[str | None] = mapped_column(String, ForeignKey("crew_members.id"), nullable=True)
    budgetLineId: Mapped[str | None] = mapped_column(String, nullable=True)

    # Logistics fields
    dietaryRestrictions: Mapped[str | None] = mapped_column(String, nullable=True)
    shirtSize: Mapped[str | None] = mapped_column(String, nullable=True)
    vehicleInfo: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="project_crew")
    crew_member: Mapped["CrewMember | None"] = relationship(back_populates="project_assignments")
    rsvps: Mapped[list["CallSheetRsvp"]] = relationship(back_populates="project_crew", cascade="all, delete-orphan")


class CallSheetRsvp(Base):
    """Per-day crew confirmation and call time."""
    __tablename__ = "call_sheet_rsvps"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status: Mapped[str] = mapped_column(RSVPStatusEnum, default="PENDING")
    sentAt: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    viewedAt: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    confirmedAt: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    personalizedCallTime: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    personalizedNotes: Mapped[str | None] = mapped_column(String, nullable=True)  # Used for location
    callSheetId: Mapped[str] = mapped_column(String, ForeignKey("call_sheets.id"), nullable=False)
    projectCrewId: Mapped[str] = mapped_column(String, ForeignKey("project_crew.id"), nullable=False)

    # Relationships
    call_sheet: Mapped["CallSheet"] = relationship(back_populates="rsvps")
    project_crew: Mapped["ProjectCrew"] = relationship(back_populates="rsvps")


class Location(Base):
    """Project location."""
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    state: Mapped[str | None] = mapped_column(String, nullable=True)
    zip: Mapped[str | None] = mapped_column(String, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 8), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(11, 8), nullable=True)
    mapLink: Mapped[str | None] = mapped_column(String, nullable=True)
    contactName: Mapped[str | None] = mapped_column(String, nullable=True)
    contactPhone: Mapped[str | None] = mapped_column(String, nullable=True)
    parkingNotes: Mapped[str | None] = mapped_column(String, nullable=True)
    parkingAddress: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    projectId: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="locations")


class ScheduleEvent(Base):
    """Daily schedule event."""
    __tablename__ = "schedule_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    sortOrder: Mapped[int] = mapped_column(Integer, nullable=False)
    time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    endTime: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    scene: Mapped[str | None] = mapped_column(String, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    eventType: Mapped[str] = mapped_column(ScheduleEventTypeEnum, default="GENERAL")
    callSheetId: Mapped[str] = mapped_column(String, ForeignKey("call_sheets.id"), nullable=False)

    # Relationships
    call_sheet: Mapped["CallSheet"] = relationship(back_populates="schedule_events")


class Client(Base):
    """Client organization."""
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_cuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    contactName: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    state: Mapped[str | None] = mapped_column(String, nullable=True)
    zip: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    isActive: Mapped[bool] = mapped_column(Boolean, default=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    organizationId: Mapped[str] = mapped_column(String, ForeignKey("organizations.id"), nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="clients")
    projects: Mapped[list["Project"]] = relationship(back_populates="client_relation")


# =============================================================================
# FastAPI Dependency
# =============================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
