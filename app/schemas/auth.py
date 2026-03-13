from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    password_repeat: str = Field(min_length=8, max_length=128)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "Ivan Ivanov",
                "email": "ivan@example.com",
                "password": "StrongPassword123",
                "password_repeat": "StrongPassword123",
            }
        }
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "ivan@example.com",
                "password": "StrongPassword123"            
            }
        }
    )


class RefreshRequest(BaseModel):
    refresh_token: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    )


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    )
