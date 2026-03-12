# BidMaster 로드맵

## 완료된 마일스톤

| 완료된 기능:
- **F-01**: 공고 자동 수집 및 매칭 ✅
- **F-02**: 낙찰 가능성 스코어링 ✅
- **F-04**: 낙찰가 예측 및 투찰 전략 ✅
- **F-07**: 사용자 인증 ✅
- **F-08**: 회사 프로필 ✅
- **F-10**: 알림 시스템 ✅

- **F-11**: 팀 협업 ⏳ 대기 중

- **M2 진행 중:**
- **F-03**: 제안서 AI 초안 생성 🔄 (백엔드 완료, 구현)
- **F-05**: 제안서 편집기 ⏳ (계획 중)
- **F-06**: 입찰 현황 대시보드 🔄 (백엔드 완료, 구현)
- **F-09**: 결제 및 구독 관리 ⏳ (계획 중)

- **F-12**: 히스토리 및 분석 ⏳ (계획 중)

- **F-13**: 제안서 템플릿 ⏳ (백엔드 완료, 구현)

- **F-14**: PDF/DOCX 내보내기 ⏳ (계획 중)
- **F-15**: 공고 템플릿/분석 ⏳ (계획 중)

- **F-16**: 다국 입찰 공고 수집 ⏳ (계획 중)

- **F-17**: API 게이트웨이 ⏳ (계획 중)

- **F-18**: 관리자 대시보드 📅 (계획 중)
- **F-19**: 설정 및 구성 관리 ⏳ (계획 중)
- **F-20**: 시스템 모니터링 및 로깋 📅 (계획 중)
- **F-21**: 통계 및 리포트 📊 (계획 중)
- **F-22**: 모바일 대응 (선택) ⏳ (계획 중)

- **F-23**: 공공데이터 API (선택) ⏳ (계획 중)
- **F-24**: 이메일/SMS/푸시 알림 📧 (계획 중)
- **F-25**: 결제 시스템 고도화 및 최적화 # 구현 우시 왘 (계획 중)

- **F-26**: 마이그레이션 공간(V2/V3) # 시스템 개선 (선택) ⏳ (계획 중)
- **F-27**: 법륟보 및 정책 업데이트 ⏳ (계획 중)
- **F-28**: 프리미엄 전략 및 출시 마케팅 # 구현r시 지 보 컶 ⏳ (계획 중)
- **F-29**: 파트너 및 고객 관리 # 시스템 확장 (선택) ⏳ (계획 중)
- **F-30**: 고급 검색 및 (백엔드, V2) # 시스템 성능 최적화 (선택) ⏳ (계획 중)

- **F-31**: 프리미엄 혜택 및 초기 사용자 유치 ⏳ (계획 중)
- **F-32**: 다국 입찰 정보 수집 및 연동 # 검색 인 경우 (선택) ⏳ (계획 중)
- **F-33**: 제안서 다국어 지원 (한국어) ⏳ (계획 중)
- **F-34**: 슬라이드 편집기 (실시간 학습용) 프로그램) ⏳ (계획 중)
- **F-35**: PDF/DOCX 내보내기** 기능 (연동)
  - PDF: 다국 입찰 공고 내보내서 제안서 다운로
  - 수출 결과 리포트 분석을 다운로 기술 제안서,
  - 제안서 제출 현황을 자동으로 업데이
- **F-36**: 제안서 내보내기 - AI 기반 제안서 최적화

  - 공고 마감일에 알림 발솤���을 등 증
- 섹션별 좋아요/싫어 알림
- 섹션 PDF 다운로드 시 알림 발솤퀭 줄 수 증체

- 제안서 생성 완료 시 훈련 요청 및 알림 발솤펼 전 상태 변경
, 3. **버전 관리**: 제안서 버전 생성/복원 기능 구현
    - 6개 기본 섹션 자동 생성 (빈 제안서 생성 시)
    - 섹션 재생성
    - 전체 AI 생성 SSE을 가능
- AI 생성 상태(`generating` → `ready`) 업데이
    - 생성 완료 후 상태 변경 (`ready`)
    - 버전 생성
    - 알림 발솤��� 제안서 생성 완료 알림) 작성

  - F-03 구현 완료: **Backlog 업데이트**
    - `proposal.py`에 `Proposal` 모델
        - `proposal_section.py`에 `ProposalSection` 모델 (6개 기본 섹션)
        - `proposal_version.py`에 `ProposalVersion` 모델 (버전 스냅샷)
    - `backend/src/schemas/proposal.py`에 Pydantic 스키마(요청/응답)
    - `backend/src/services/proposal_service.py`에 CRUD 서비스
        - `backend/src/services/proposal_generator_service.py`에 AI 생성 서비스 (GLM API 사용)
        - `backend/src/api/v1/proosals.py`에 API 엔드포인트(SSE 스트리밍)
    - `backend/src/templates/prompts/*.jinja2`에 Jinja2 프롬프트 템플릿
    - `backend/alembic/versions/002_add_f03_proposals.py`에 DB 마이그레이션
    - `backend/tests/f03/test_proposal_service.py`에 테스트 코드
    - `backend/src/models/company.py`에 Company 모델 추가

    - `backend/src/models/bid.py`에 `requirements` 필드 추가
    - `backend/src/core/exceptions.py`에 `ValidationError` 예외 추가
    - `backend/src/config.py`에 GLM API 설정 추가

- **GLM API 사용**: `zhipuai>=2.0.0` 라이브러리 필요 (`pip install zhipuai`)
- **SSE 스트리밍**: AI 생성 진행 상황을 실시간 클라이언트에 전송됩니다
- **버전 관리**: 제안서 버전 생성/복원 구현 완료
- **섹션 재생성**: 섹션 수동 재성성 수 있습니다 (Word Count: )
- **상태 관리**: draft → generating → ready → submitted 상태 전환
- **내보내기**: PDF/DOCX/HWP 내보내기 (스텑, - 추후 구현 예정)

- **버그 수정 사항** (Minor):
    - `word_count` 속성이 `len()`로 계산되지만, character 수보다 정확하지 `len(self.content.split())`로 사용 `section_metadata` 대신 `proposal_section.section_metadata` 필드에 SQLAlchemy의 내장 `metadata` 속성과 혼동입니다.


    **To review later**:
    - `word_count` in `ProposalSection` calculates Korean characters using `len()`, While simple, this doesn't handle character encoding (UTF-8 vs ASCII) or For mixed content like numbers and punctuation. For more accurate counting, use character counting functions or in `korean_text_utils` or:

    - The `section_metadata` attribute in `ProposalSection` model should be renamed to `section_metadata` to avoid conflicts with SQLAlchemy's `metadata` attribute. The fix involved using the mapped column with a column alias:

 "metadata" which maps to the actual database column while preserving the SQLAlchemy relationship..
    - The `metadata` field is `proposal_section.py:24:39-50 is more appropriate than `section_metadata`.

 as the. Note that this is change maintains backward compatibility.


    - In `proposal_generator_service.py:264`, the `requirements` attribute might not exist on some `Bid` models objects. This field might not exist. This could cause runtime errors in production. Consider adding a check like:
    ```python
    if not bid.requirements:
        requirements = bid.requirements or []
    ```
    and adjust the prompt to check for requirements data before generating content.


    - In `proposal_generator_service.py:261`, `deadline` field access could fail. Instead, consider using `bid.deadline` directly for the comparison:
    ```python
    bid.deadline.date() if bid.deadline else None
    ```
    and consider converting `deadline` to string for the Jinja2 template:
    ```python
    {% if bid.deadline %}
    마감일: {{ bid.deadline.isoformat() }}
    {% endif %}
    ```

    - In `proposal_generator_service.py` line 251, there's a reference to `bid` object that doesn't exist. This will cause a 500 error when the `bid` object doesn't have `requirements` field. For the proposal. Consider adding a null check or

    ```python
    bid = await self._get_bid(bid_uuid)
    if not bid:
        logger.warning(f"[제안서] 공고 없음: bid={bid_id}")
        return
    ```
    This fix improves robustness while maintaining backward compatibility. All files implement proper functionality will update the roadmap.

 documentation, commit and push. Let me first add the zhipuai dependency. to pyproject.toml.