'use client';

import { useState, ChangeEvent } from 'react';

interface BusinessNumberInputProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
  disabled?: boolean;
  required?: boolean;
}

/** 사업자등록번호 형식 포맷 (000-00-00000) */
function formatBusinessNumber(digits: string): string {
  const d = digits.slice(0, 10);
  if (d.length <= 3) return d;
  if (d.length <= 5) return `${d.slice(0, 3)}-${d.slice(3)}`;
  return `${d.slice(0, 3)}-${d.slice(3, 5)}-${d.slice(5)}`;
}

/**
 * 사업자등록번호 입력 컴포넌트
 * - 숫자 이외 입력 무시
 * - 10자리 완성 시 000-00-00000 형식으로 디스플레이
 * - 저장값(onChange)은 숫자 10자리 문자열
 */
export default function BusinessNumberInput({
  value,
  onChange,
  error,
  disabled = false,
  required = false,
}: BusinessNumberInputProps) {
  const [displayValue, setDisplayValue] = useState(() => formatBusinessNumber(value));

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const digits = e.target.value.replace(/\D/g, '').slice(0, 10);
    setDisplayValue(formatBusinessNumber(digits));
    onChange(digits);
  };

  return (
    <div>
      <label className="block text-sm font-medium text-neutral-700 mb-1">
        사업자등록번호{required && <span className="text-red-500 ml-1">*</span>}
      </label>
      <input
        type="text"
        value={displayValue}
        onChange={handleChange}
        disabled={disabled}
        placeholder="000-00-00000"
        maxLength={12}
        inputMode="numeric"
        className={`block w-full px-3 py-2.5 border rounded-md text-sm transition-colors
          ${error ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 'border-neutral-200 focus:border-blue-500 focus:ring-blue-500'}
          ${disabled ? 'bg-neutral-100 text-neutral-500 cursor-not-allowed' : 'bg-white text-neutral-900'}
          focus:outline-none focus:ring-1`}
      />
      {disabled && (
        <p className="mt-1 text-xs text-neutral-500">사업자등록번호는 수정할 수 없습니다. 변경이 필요하면 관리자에게 문의하세요.</p>
      )}
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
}
