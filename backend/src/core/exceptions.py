"""애플리케이션 공통 예외"""


class AppException(Exception):
    """애플리케이션 예외 기본 클래스"""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

    def __repr__(self) -> str:
        return f"<AppException code={self.code} status={self.status_code} message={self.message}>"
