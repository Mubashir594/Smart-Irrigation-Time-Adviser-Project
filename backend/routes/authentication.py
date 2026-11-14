from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserSettings
from schemas import UserRegister, UserLogin, TokenResponse, UserOut, MessageResponse
from auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(registration_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account with Full Name, Username, and Password.
    Hashes the password with bcrypt and creates default user settings.
    """
    # 1. Validate password confirmation
    if registration_data.password != registration_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match. Please verify both password entries."
        )

    # 2. Check if username is already taken
    clean_username = registration_data.username.strip()
    existing_user = db.query(User).filter(User.username == clean_username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{clean_username}' is already registered. Please choose another username."
        )

    # 3. Create user record with bcrypt hash
    hashed = hash_password(registration_data.password)
    new_user = User(
        full_name=registration_data.full_name.strip(),
        username=clean_username,
        password_hash=hashed
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 4. Initialize default user settings
    default_settings = UserSettings(
        user_id=new_user.id,
        sensor_frequency="Standard (15m)",
        autonomous_mode=True
    )
    db.add(default_settings)
    db.commit()

    return UserOut.model_validate(new_user)

@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, response: Response, db: Session = Depends(get_db)):
    """
    Authenticate an administrator or registered operator using username and password.
    Returns a JWT access token upon successful verification.
    """
    user = db.query(User).filter(User.username == credentials.username.strip()).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Username or Security Token. Access denied.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT token with user identity
    access_token = create_access_token(data={"sub": user.username, "user_id": user.id})

    # Set cookie for easy browser integration
    response.set_cookie(
        key="aura_token",
        value=access_token,
        httponly=False,
        max_age=86400,
        samesite="lax"
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(user)
    )

@router.post("/logout", response_model=MessageResponse)
def logout(response: Response, current_user: User = Depends(get_current_user)):
    """
    Log out the currently authenticated user and clear session cookies.
    """
    response.delete_cookie(key="aura_token")
    return MessageResponse(message=f"Session terminated successfully for {current_user.username}.")

@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get profile details of the currently authenticated operator.
    """
    return UserOut.model_validate(current_user)
