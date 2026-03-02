"""보안 관련 유틸리티"""
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
from passlib.context import CryptContext

from src.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 토큰 만료 설정
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1시간
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30일


class AuthError(Exception):
    """인증 관련 에러"""
    def __init__(self, code: str, message: str, status_code: int = 401):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ValidationError(Exception):
    """유효성 검사 에러"""
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    if not plain_password or not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """비밀번호 해싱 (bcrypt cost factor 12)"""
    return pwd_context.hash(password)


def validate_password(password: str, email: str | None = None) -> bool:
    """
    비밀번호 유효성 검사

    규칙:
    - 최소 8자, 최대 64자
    - 영문 대소문자, 숫자, 특수문자, 한글 중 3가지 이상 조합
    - 이메일과 유사하지 않아야 함
    """
    if not password:
        raise ValidationError("VALIDATION_002", "필수 입력값 누락", 400)

    # 길이 검사
    if len(password) < 8:
        raise ValidationError("VALIDATION_001", "비밀번호는 최소 8자 이상이어야 합니다.", 400)
    if len(password) > 64:
        raise ValidationError("VALIDATION_003", "비밀번호는 최대 64자까지 가능합니다.", 400)

    # 문자 조합 검사 (한글 추가)
    has_lower = bool(re.search(r'[a-z]', password))
    has_upper = bool(re.search(r'[A-Z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    has_korean = bool(re.search(r'[가-힣]', password))

    combination_count = sum([has_lower, has_upper, has_digit, has_special, has_korean])
    if combination_count < 3:
        raise ValidationError("VALIDATION_001", "비밀번호는 영문 대소문자, 숫자, 특수문자, 한글 중 3가지 이상을 조합해야 합니다.", 400)

    # 이메일 유사성 검사
    if email and email.lower() in password.lower():
        raise ValidationError("VALIDATION_001", "비밀번호에 이메일을 포함할 수 없습니다.", 400)

    return True


def create_access_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
    extra_data: dict | None = None
) -> str:
    """JWT 액세스 토큰 생성 (1시간 만료)"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(timezone.utc)
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
    }

    if extra_data:
        to_encode.update(extra_data)

    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(subject: str | Any) -> str:
    """리프레시 토큰 생성 (30일 만료, jti 포함)"""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    now = datetime.now(timezone.utc)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),  # 고유 토큰 ID
    }

    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    JWT 토큰 디코딩

    Raises:
        AuthError: 토큰 없음, 만료, 변조 등
    """
    if not token:
        raise AuthError("AUTH_002", "인증 토큰이 필요합니다.", 401)

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except ExpiredSignatureError:
        raise AuthError("AUTH_003", "토큰이 만료되었습니다.", 401)
    except JWTError:
        raise AuthError("AUTH_004", "유효하지 않은 토큰입니다.", 401)
