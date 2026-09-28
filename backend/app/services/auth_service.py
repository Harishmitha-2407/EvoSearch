"""Authentication service for user registration and login."""
import re
import bcrypt
from sqlalchemy.orm import Session
from app.models import User


def validate_email(email: str) -> tuple[bool, str]:
    """Validate email format."""
    email = email.strip().lower()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    # Check byte length for bcrypt 72-byte limit
    if len(password.encode('utf-8')) > 72:
        return False, "Password cannot be longer than 72 bytes"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        return False, "Password must contain at least one special character (!@#$%^&* etc)"
    return True, ""


def hash_password(password: str) -> str:
    """Hash password using bcrypt with 72-byte limit."""
    # Bcrypt has a 72-byte limit. Truncate by byte length, not character length
    password_bytes = password.encode('utf-8')[:72]
    password = password_bytes.decode('utf-8', errors='ignore')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        # Bcrypt has a 72-byte limit. Truncate by byte length, not character length
        password_bytes = password.encode('utf-8')[:72]
        password = password_bytes.decode('utf-8', errors='ignore')
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


def register_user(db: Session, email: str, password: str) -> tuple[bool, str, User | None]:
    """Register a new user. Email is normalized to lowercase."""
    # Normalize email
    email = email.strip().lower()
    
    # Validate email
    valid, msg = validate_email(email)
    if not valid:
        return False, msg, None
    
    # Check if email already exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return False, "Email already registered", None
    
    # Validate password
    valid, msg = validate_password(password)
    if not valid:
        return False, msg, None
    
    # Create user
    password_hash = hash_password(password)
    user = User(email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return True, "User registered successfully", user


def login_user(db: Session, email: str, password: str) -> tuple[bool, str, User | None]:
    """Login a user. Email is normalized to lowercase."""
    # Normalize email
    email = email.strip().lower()
    
    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False, "Invalid email or password", None
    
    # Verify password
    if not verify_password(password, user.password_hash):
        return False, "Invalid email or password", None
    
    return True, "Login successful", user
