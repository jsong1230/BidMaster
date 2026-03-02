'use client';

import { useState, ChangeEvent, FocusEvent } from 'react';

interface AmountInputProps {
  value: number | '';
  onChange: (value: number | '') => void;
  error?: string;
  disabled?: boolean;
  required?: boolean;
  label?: string;
  placeholder?: string;
}

function formatAmount(num: number): string {
  return num.toLocaleString('ko-KR');
}

function parseAmount(str: string): number | '' {
  const digits = str.replace(/,/g, '').replace(/[^\d]/g, '');
  if (!digits) return '';
  const num = parseInt(digits, 10);
  return isNaN(num) ? '' : num;
}

/**
 * 금액 입력 컴포넌트
 * - blur 시 천 단위 콤마 포맷 적용
 * - 양수 값만 허용
 */
export default function AmountInput({
  value,
  onChange,
  error,
  disabled = false,
  required = false,
  label = '계약 금액',
  placeholder = '0',
}: AmountInputProps) {
  const [displayValue, setDisplayValue] = useState<string>(
    value !== '' ? formatAmount(value) : ''
  );
  const [isFocused, setIsFocused] = useState(false);

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/,/g, '').replace(/[^\d]/g, '');
    setDisplayValue(raw);
    const parsed = parseAmount(raw);
    onChange(parsed);
  };

  const handleFocus = () => {
    setIsFocused(true);
    // 포커스 시 콤마 제거
    if (displayValue) {
      setDisplayValue(displayValue.replace(/,/g, ''));
    }
  };

  const handleBlur = (e: FocusEvent<HTMLInputElement>) => {
    setIsFocused(false);
    const parsed = parseAmount(e.target.value);
    if (parsed !== '') {
      setDisplayValue(formatAmount(parsed));
      onChange(parsed);
    } else {
      setDisplayValue('');
      onChange('');
    }
  };

  return (
    <div>
      <label className="block text-sm font-medium text-neutral-700 mb-1">
        {label}{required && <span className="text-red-500 ml-1">*</span>}
      </label>
      <div className="relative flex items-center">
        <input
          type="text"
          value={isFocused ? displayValue.replace(/,/g, '') : displayValue}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          disabled={disabled}
          placeholder={placeholder}
          inputMode="numeric"
          className={`block w-full px-3 py-2.5 pr-8 border rounded-md text-sm transition-colors
            ${error ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 'border-neutral-200 focus:border-blue-500 focus:ring-blue-500'}
            ${disabled ? 'bg-neutral-100 text-neutral-500 cursor-not-allowed' : 'bg-white text-neutral-900'}
            focus:outline-none focus:ring-1`}
        />
        <span className="absolute right-3 text-sm text-neutral-500 pointer-events-none">원</span>
      </div>
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
}
