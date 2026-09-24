from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.config import settings
from app.models.schemas import User
from app.models.enums import UserRole
from app.schemas.all_schemas import Token, LoginRequest, UserOut
from app.core.security import verify_password, create_access_token
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login-form")

user_repo = UserRepository()

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    user = user_repo.get_by_id(user_id)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")
    return user

def require_role(roles: List[UserRole]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {[r.value for r in roles]}"
            )
        return current_user
    return role_checker

@router.post("/login", response_model=Token)
def login(req: LoginRequest):
    user = user_repo.get_by_email(req.email)
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    user_out = UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        department=user.department,
        student_id_card=user.student_id_card,
        is_active=user.is_active
    )
    return Token(access_token=access_token, token_type="bearer", user=user_out)

@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        department=current_user.department,
        student_id_card=current_user.student_id_card,
        is_active=current_user.is_active
    )

@router.get("/staff", response_model=List[UserOut])
def list_staff_members(department: Optional[str] = None, current_user: User = Depends(get_current_user)):
    # Any authenticated user can view staff list for assignment or directory
    staff_list = user_repo.get_all(role=UserRole.STAFF, department=department)
    managers = user_repo.get_all(role=UserRole.MANAGER, department=department)
    combined = staff_list + managers
    return [
        UserOut(
            id=u.id,
            name=u.name,
            email=u.email,
            role=u.role,
            department=u.department,
            student_id_card=u.student_id_card,
            is_active=u.is_active
        )
        for u in combined
    ]
