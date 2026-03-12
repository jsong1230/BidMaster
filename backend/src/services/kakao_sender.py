"""카카오 알림톡 발송 서비스 (F-10, 스텁)"""
import logging
from typing import Any

from src.config import get_settings

logger = logging.getLogger(__name__)


class KakaoAlimtalkSender:
    """카카오 알림톡 발송 (환경변수로 제어, 기본 비활성)"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.enabled = self.settings.kakao_alimtalk_enabled

    async def send(
        self,
        phone: str,
        template_code: str,
        variables: dict[str, Any],
    ) -> bool:
        """
        카카오 알림톡 발송

        Args:
            phone: 수신자 전화번호 (하이픈 제외)
            template_code: 카카오 템플릿 코드
            variables: 템플릿 변수

        Returns:
            발송 성공 여부
        """
        if not self.enabled:
            logger.info(
                f"[카카오 알림톡] 비활성화됨: phone={phone}, template={template_code}"
            )
            return False

        # TODO: 카카오 비즈메시지 API 연동
        # https://business.kakao.com/docs/bizmessage/
        logger.warning(
            f"[카카오 알림톡] 미구현: phone={phone}, template={template_code}, "
            f"vars={variables}"
        )
        return False
