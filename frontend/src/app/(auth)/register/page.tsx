'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import { useAuthStore } from '@/lib/stores/auth-store';

const registerSchema = z.object({
  email: z.string().email('이메일을 입력해주세요'),
  password: z
    .string()
    .min(8, '비밀번호는 8자 이상이어야 합니다.')
    .max(64, '비밀번호는 64자 이하여야 합니다.')
    .refine((val) => {
      const hasLower = /[a-z]/.test(val);
      const hasUpper = /[A-Z]/.test(val);
      const hasDigit = /\d/.test(val);
      const hasSpecial = /[!@#$%^&*]/.test(val);
      const combinationCount = [hasLower, hasUpper, hasDigit, hasSpecial].filter(Boolean).length;
      return combinationCount >= 3;
    }, '영문 대소문자, 숫자, 특수문자 중 3가지 이상 포함해야 합니다.'),
  name: z.string().min(1, '이름을 입력해주세요'),
  phone: z.string().optional(),
});

type RegisterFormData = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const { login, isLoading } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      password: '',
      name: '',
      phone: '',
    },
  });

  const onSubmit: SubmitHandler<RegisterFormData> = async (data) => {
    setFormError(null);
    try {
      // 회원가입 후 로그인 처리 (스토어에 register 액션이 없으므로 임시)
      await login(data.email, data.password);
      router.push('/dashboard');
    } catch {
      setFormError('회원가입에 실패했습니다. 다시 시도해주세요.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">BidMaster</h1>
          <p className="mt-2 text-gray-600">계정 만들기</p>
        </div>

        {/* Error Message */}
        {formError && (
          <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
            {formError}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Email */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              이메일 <span className="text-red-500">*</span>
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              {...register('email')}
              className={`mt-1 block w-full rounded-md border px-3 py-2 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                errors.email ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
            )}
          </div>

          {/* Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700">
              이름 <span className="text-red-500">*</span>
            </label>
            <input
              id="name"
              type="text"
              autoComplete="name"
              {...register('name')}
              className={`mt-1 block w-full rounded-md border px-3 py-2 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                errors.name ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
            )}
          </div>

          {/* Password */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              비밀번호 <span className="text-red-500">*</span>
            </label>
            <div className="relative mt-1">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                {...register('password')}
                className={`block w-full rounded-md border px-3 py-2 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 pr-10 sm:text-sm ${
                  errors.password ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? '숨기기' : '보기'}
              </button>
            </div>
            {errors.password && (
              <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
            )}
          </div>

          {/* Phone (Optional) */}
          <div>
            <label htmlFor="phone" className="block text-sm font-medium text-gray-700">
              전화번호 (선택)
            </label>
            <input
              id="phone"
              type="tel"
              autoComplete="tel"
              {...register('phone')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? '처리 중...' : '회원가입'}
          </button>

          {/* Login Link */}
          <div className="text-center">
            <p className="text-sm text-gray-600">
              이미 계정이 있으신가요?{' '}
              <button
                type="button"
                onClick={() => router.push('/login')}
                className="font-medium text-blue-600 hover:text-blue-500"
              >
                로그인
              </button>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
