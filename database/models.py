from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(128), nullable=False)
    email = Column(String(256), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    phone = Column(String(32), nullable=True, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    reset_token_hash = Column(String(256), nullable=True)
    reset_token_expires_at = Column(DateTime, nullable=True)

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")

    # Compatibility properties
    @property
    def user_id(self):
        return self.id

    @user_id.setter
    def user_id(self, value):
        self.id = value

    @property
    def name(self):
        return self.full_name

    @name.setter
    def name(self, value):
        self.full_name = value

    @property
    def password_hash(self):
        return self.hashed_password

    @password_hash.setter
    def password_hash(self, value):
        self.hashed_password = value


class UserProfile(Base):
    __tablename__ = "user_profiles"

    profile_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    full_name = Column(String(128), nullable=True)
    phone = Column(String(32), nullable=True)
    address = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    profile_picture = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")


class Resume(Base):
    __tablename__ = "resumes"

    resume_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String(256), nullable=False)
    file_path = Column(String(512), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="resumes")
    parsed_resume = relationship("ParsedResume", back_populates="resume", uselist=False, cascade="all, delete-orphan")


class ParsedResume(Base):
    __tablename__ = "parsed_resumes"

    parsed_id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.resume_id"), nullable=False)
    full_name = Column(String(256), nullable=True)
    email = Column(String(256), nullable=True)
    phone = Column(String(64), nullable=True)
    address = Column(Text, nullable=True)
    linkedin = Column(String(256), nullable=True)
    github = Column(String(256), nullable=True)
    professional_summary = Column(Text, nullable=True)
    skills = Column(JSON, nullable=True)
    technical_skills = Column(JSON, nullable=True)
    soft_skills = Column(JSON, nullable=True)
    education = Column(JSON, nullable=True)
    experience = Column(JSON, nullable=True)
    projects = Column(JSON, nullable=True)
    certifications = Column(JSON, nullable=True)
    internships = Column(JSON, nullable=True)
    languages = Column(JSON, nullable=True)
    achievements = Column(JSON, nullable=True)
    publications = Column(JSON, nullable=True)

    resume = relationship("Resume", back_populates="parsed_resume")
