import re
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from sqlalchemy.orm import Session
import bcrypt
from datetime import datetime, timedelta
import jwt

from app.database import SessionLocal
from app.models import User
from app.config import settings
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

# JWT setup
SECRET_KEY = settings.SECRET_KEY if hasattr(settings, 'SECRET_KEY') else "your-secret-key-change-in-production"
ALGORITHM = "HS256"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_password_hash(password: str) -> str:
    # Bcrypt has a 72-byte limit. Truncate by byte length, not character length
    # Some characters (like special chars) may be multi-byte in UTF-8
    password_bytes = password.encode('utf-8')[:72]
    password = password_bytes.decode('utf-8', errors='ignore')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Bcrypt has a 72-byte limit. Truncate by byte length, not character length
    # Some characters (like special chars) may be multi-byte in UTF-8
    password_bytes = plain_password.encode('utf-8')[:72]
    plain_password = password_bytes.decode('utf-8', errors='ignore')
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def create_access_token(user_id: str, expires_delta: timedelta | None = None):
    if expires_delta is None:
        expires_delta = timedelta(days=7)
    
    expire = datetime.utcnow() + expires_delta
    payload = {"sub": user_id, "exp": expire}
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        return user_id
    except:
        return None


# ============================================================================
# Request/Response Models
# ============================================================================

class PasswordValidator(BaseModel):
    """Validate password strength"""
    password: str
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        # Check byte length instead of character length (bcrypt 72-byte limit)
        if len(v.encode('utf-8')) > 72:
            raise ValueError("Password cannot be longer than 72 bytes (bcrypt limitation)")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class SignupRequest(PasswordValidator):
    email: str
    
    @field_validator("email")
    @classmethod
    def normalize_email(cls, v):
        return v.lower().strip()


class LoginRequest(BaseModel):
    email: str
    password: str
    
    @field_validator("email")
    @classmethod
    def normalize_email(cls, v):
        return v.lower().strip()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    email: str
    created_at: datetime


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


class PasswordStrengthInfo(BaseModel):
    requires: list[str] = [
        "At least 8 characters long",
        "One uppercase letter (A-Z)",
        "One lowercase letter (a-z)",
        "One number (0-9)",
        "One special character (!@#$%^&*...)",
    ]


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/signup", response_model=AuthResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Create a new user account."""
    try:
        email = request.email.lower().strip()
        
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user = User(email=email, password_hash=get_password_hash(request.password))
        db.add(user)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database error: {str(e)}"
            )
        db.refresh(user)
        
        # Generate token
        token = create_access_token(user.id)
        
        return AuthResponse(
            token=token,
            user=UserResponse.model_validate(user)
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Signup error: {str(e)}"
        )


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password."""
    try:
        email = request.email.lower().strip()
        
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        token = create_access_token(user.id)
        return AuthResponse(
            token=token,
            user=UserResponse.model_validate(user)
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Login error: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Get current logged-in user info."""
    try:
        return UserResponse.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@router.get("/password-requirements", response_model=PasswordStrengthInfo)
def get_password_requirements():
    """Get password strength requirements."""
    return PasswordStrengthInfo()
