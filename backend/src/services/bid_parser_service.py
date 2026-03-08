"""공고 첨부파일 파싱 서비스 - PDF/HWP 텍스트 추출"""
import logging
import tempfile
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)

# HWP 파서 선택적 임포트
try:
    import hwp5  # type: ignore[import]
    HWP_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    HWP_AVAILABLE = False
    logger.warning("pyhwp가 설치되지 않았습니다. HWP 파싱이 비활성화됩니다.")


class BidParserService:
    """공고 첨부파일 파싱 서비스"""

    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client

    async def parse_attachment(self, attachment: Any) -> str | None:
        """
        첨부파일 파싱 메인 플로우

        1. file_url에서 파일 다운로드
        2. file_type에 따라 파서 선택
        3. 텍스트 추출
        4. attachment.extracted_text 갱신

        Returns:
            추출된 텍스트 (실패 또는 지원하지 않는 형식 시 None)
        """
        file_type = (attachment.file_type or "").upper()

        # 지원하지 않는 파일 형식
        if file_type not in ("PDF", "HWP"):
            logger.info(f"지원하지 않는 파일 형식입니다: {file_type}")
            return None

        # 파일 다운로드
        tmp_path = await self._download_file(attachment.file_url)
        if tmp_path is None:
            logger.warning(f"파일 다운로드 실패: {attachment.file_url}")
            return None

        # 파일 타입별 파싱
        extracted_text: str | None = None
        if file_type == "PDF":
            extracted_text = self._parse_pdf(tmp_path)
        elif file_type == "HWP":
            extracted_text = self._parse_hwp(tmp_path)

        # extracted_text 갱신
        if extracted_text is not None:
            attachment.extracted_text = extracted_text

        return extracted_text

    async def _download_file(self, url: str) -> Path | None:
        """
        파일 다운로드 -> 임시 경로 반환

        Returns:
            임시 파일 경로 (실패 시 None)
        """
        try:
            response = await self.http_client.get(url)
            if response.status_code != 200:
                logger.warning(f"파일 다운로드 실패 (HTTP {response.status_code}): {url}")
                return None

            # 임시 파일에 저장
            suffix = Path(url.split("?")[0]).suffix or ".tmp"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(response.content)
                return Path(tmp_file.name)

        except httpx.TimeoutException as e:
            logger.warning(f"파일 다운로드 타임아웃: {url}: {e}")
            return None
        except Exception as e:
            logger.warning(f"파일 다운로드 오류: {url}: {e}")
            return None

    def _parse_pdf(self, file_path: Path) -> str | None:
        """
        PDF 텍스트 추출 (pdfplumber)

        Returns:
            추출된 텍스트 (빈 PDF는 빈 문자열, 오류 시 None)
        """
        try:
            import pdfplumber  # type: ignore[import]

            with pdfplumber.open(file_path) as pdf:
                texts: list[str] = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        texts.append(page_text)
                return "\n".join(texts)

        except ImportError:
            logger.error("pdfplumber가 설치되지 않았습니다.")
            return None
        except Exception as e:
            logger.warning(f"PDF 파싱 오류: {file_path}: {e}")
            return None

    def _parse_hwp(self, file_path: Path) -> str | None:
        """
        HWP 텍스트 추출 (pyhwp)

        Returns:
            추출된 텍스트 (pyhwp 미설치 시 None, graceful degradation)
        """
        # sys.modules를 직접 확인하여 None이 등록된 경우도 처리
        import sys
        hwp5_module = sys.modules.get("hwp5")
        if hwp5_module is None:
            logger.warning("pyhwp(hwp5)가 설치되지 않았습니다. HWP 파싱을 건너뜁니다.")
            return None

        try:
            with hwp5_module.open(str(file_path)) as doc:
                text = getattr(doc, "text", None)
                if text is not None:
                    return str(text)
                return None
        except Exception as e:
            logger.warning(f"HWP 파싱 오류: {file_path}: {e}")
            return None

    async def parse_all_for_bid(
        self,
        bid_id: UUID | Any,
        attachments: list[Any],
    ) -> int:
        """
        공고의 모든 첨부파일 파싱

        Returns:
            성공적으로 파싱된 파일 수
        """
        success_count = 0
        for attachment in attachments:
            try:
                result = await self.parse_attachment(attachment)
                if result is not None:
                    success_count += 1
            except Exception as e:
                logger.warning(f"첨부파일 파싱 오류 (bid={bid_id}): {e}")

        return success_count
