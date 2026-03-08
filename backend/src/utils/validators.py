"""검증 유틸리티"""
from src.core.security import ValidationError


def validate_business_number(number: str) -> bool:
    """
    사업자등록번호 형식 및 체크섬 검증

    체크섬 알고리즘:
    - 가중치: [1, 3, 7, 1, 3, 7, 1, 3, 5]
    - 각 자리 * 가중치 합산
    - 9번째 자리(index 8): (가중치 * 자리수) / 10의 몫도 더함
    - (10 - (합산 % 10)) % 10 == 마지막 자리

    Raises:
        ValidationError: 사업자등록번호 형식 또는 체크섬 검증 실패 (COMPANY_003)

    Returns:
        True: 유효한 사업자등록번호
    """
    if not isinstance(number, str) or not number:
        raise ValidationError("COMPANY_003", "사업자등록번호 검증 실패", 400)

    if not number.isdigit() or len(number) != 10:
        raise ValidationError("COMPANY_003", "사업자등록번호 검증 실패", 400)

    # 모두 0인 경우 무효
    if number == "0" * 10:
        raise ValidationError("COMPANY_003", "사업자등록번호 검증 실패", 400)

    digits = [int(c) for c in number]
    weights = [1, 3, 7, 1, 3, 7, 1, 3, 5]

    total = sum(w * d for w, d in zip(weights, digits[:9]))
    total += (5 * digits[8]) // 10
    checksum = (10 - (total % 10)) % 10

    if checksum != digits[9]:
        raise ValidationError("COMPANY_003", "사업자등록번호 검증 실패", 400)

    return True
