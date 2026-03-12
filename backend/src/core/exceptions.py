"""애플리케이션 공통 예외"""


class AppException(Exception):
    """애플리케이션 예외 기본 클래스"""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

    def __repr__(self) -> str:
        return f"<AppException code={self.code}>"


class ValidationError(AppException):
    """유효성 검사 에러"""

    def __init__(self, code: str = "VALIDATION_001", message: str = "유효하지 않은 요청입니다."):
        super().__init__(code=code, message=message, status_code=422)


class NotFoundError(AppException):
    """리소스 없음 예외"""

    def __init__(self, code: str = "NOT_FOUND", message: str = "리소스를 찾을 수 없습니다."):
        super().__init__(code=code, message=message, status_code=404)


class PermissionError(AppException):
    """권한 없음 예외"""

    def __init__(self, code: str = "PERMISSION_DENIED", message: str = "접근 권한이 없습니다."):
        super().__init__(code=code, message=message, status_code=403)


class AuthenticationError(AppException):
    """인증 에러"""

    def __init__(self, code: str = "AUTH_001", message: str = "인증에 실패했습니다."):
        super().__init__(code=code, message=message, status_code=401)
