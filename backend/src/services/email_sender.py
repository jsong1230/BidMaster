"""이메일 발송 서비스 (F-10)"""
import logging
from pathlib import Path
from typing import Any

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.config import get_settings

logger = logging.getLogger(__name__)

# 템플릿 디렉토리
TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "email"


class EmailSender:
    """이메일 발송 (aiosmtplib)"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._env: Environment | None = None

    @property
    def env(self) -> Environment:
        """Jinja2 환경 (지연 초기화)"""
        if self._env is None:
            self._env = Environment(
                loader=FileSystemLoader(str(TEMPLATE_DIR)),
                autoescape=select_autoescape(["html", "xml"]),
            )
        return self._env

    async def send(
        self,
        to_email: str,
        subject: str,
        body_html: str,
    ) -> bool:
        """
        이메일 발송

        Args:
            to_email: 수신자 이메일
            subject: 이메일 제목
            body_html: HTML 본문

        Returns:
            발송 성공 여부
        """
        if not self.settings.email_enabled:
            logger.info(f"[이메일] 발송 비활성화됨: {to_email}")
            return False

        if not self.settings.smtp_host:
            logger.warning("[이메일] SMTP 설정 없음 - 발송 스킵")
            return False

        try:
            message = self._build_message(to_email, subject, body_html)
            await aiosmtplib.send(
                message,
                hostname=self.settings.smtp_host,
                port=self.settings.smtp_port,
                username=self.settings.smtp_user or None,
                password=self.settings.smtp_password or None,
                start_tls=True,
            )
            logger.info(f"[이메일] 발송 성공: {to_email}")
            return True
        except Exception as e:
            logger.error(f"[이메일] 발송 실패: {to_email} - {e}")
            return False

    def _build_message(
        self,
        to_email: str,
        subject: str,
        body_html: str,
    ):
        """이메일 메시지 빌드"""
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        message = MIMEMultipart("alternative")
        message["From"] = f"{self.settings.smtp_from_name} <{self.settings.smtp_from_email}>"
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body_html, "html", "utf-8"))

        return message

    def render_template(
        self,
        template_name: str,
        context: dict[str, Any],
    ) -> str:
        """
        이메일 HTML 템플릿 렌더링

        Args:
            template_name: 템플릿 파일명 (예: bid_matched.html)
            context: 템플릿 컨텍스트

        Returns:
            렌더링된 HTML 문자열
        """
        template = self.env.get_template(template_name)
        return template.render(**context)

    async def send_with_template(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict[str, Any],
    ) -> bool:
        """
        템플릿을 사용한 이메일 발송

        Args:
            to_email: 수신자 이메일
            subject: 이메일 제목
            template_name: 템플릿 파일명
            context: 템플릿 컨텍스트

        Returns:
            발송 성공 여부
        """
        try:
            body_html = self.render_template(template_name, context)
            return await self.send(to_email, subject, body_html)
        except Exception as e:
            logger.error(f"[이메일] 템플릿 렌더링 실패: {template_name} - {e}")
            return False
