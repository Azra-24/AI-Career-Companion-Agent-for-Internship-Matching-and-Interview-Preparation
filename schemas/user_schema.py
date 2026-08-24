from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"name": "John Doe", "email": "john@example.com", "password": "StrongPass123", "phone": "9876543210"}})
    name: str = Field(..., min_length=2, max_length=128)
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone: str | None = None


class UserLogin(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"email": "john@example.com", "password": "StrongPass123"}})
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"email": "john@example.com"}})
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"email": "john@example.com", "reset_token": "demo-reset-token", "new_password": "NewStrongPass123"}})
    email: EmailStr
    reset_token: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"current_password": "StrongPass123", "new_password": "NewStrongPass123"}})
    current_password: str
    new_password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"access_token": "jwt-token", "token_type": "bearer"}})
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    phone: str | None = None
    created_at: str


class ProfileCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"full_name": "John Doe", "phone": "9876543210", "address": "Hyderabad", "bio": "Computer Science student"}})
    full_name: str | None = Field(default=None, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    address: str | None = Field(default=None, max_length=256)
    bio: str | None = Field(default=None, max_length=500)
    profile_picture: str | None = Field(default=None, max_length=512)


class ProfileUpdate(ProfileCreate):
    pass


class ProfileResponse(ProfileCreate):
    profile_id: int
    user_id: int
    created_at: str
    updated_at: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None


class UserRegisterRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"full_name": "John Doe", "email": "john@example.com", "password": "StrongPass123"}})
    full_name: str = Field(..., min_length=2, max_length=128)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLoginRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"email": "john@example.com", "password": "StrongPass123"}})
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": {"id": 1, "full_name": "John Doe", "email": "john@example.com", "phone": "9876543210"}})
    id: int
    full_name: str
    email: EmailStr
    phone: str | None = ""


class AuthTokenResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"access_token": "jwt-token", "token_type": "bearer", "user": {"id": 1, "full_name": "John Doe", "email": "john@example.com", "phone": "9876543210"}}})
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
