'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import { useAuthStore } from '@/lib/stores/auth-store';

const loginSchema = z.object({
  email: z.string().email('이메일을 입력해주세요'),
  password: z.string().min(8, '비밀번호를 입력해주세요'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit: SubmitHandler<LoginFormData> = async (data) => {
    setFormError(null);
    try {
      await login(data.email, data.password);
      router.push('/dashboard');
    } catch {
      setFormError('로그인에 실패했습니다. 이메일과 비밀번호를 확인해주세요.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 bg-white p-8 rounded-xl shadow-lg">
        {/* 로고 */}
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">BidMaster</h1>
          <p className="text-gray-500 mt-2">로그인하여 계속하세요</p>
        </div>

        {/* 에러 메시지 */}
        {formError && (
          <div className="bg-red-50 text-red-500 p-4 rounded-lg text-sm">
            {formError}
          </div>
        )}

        {/* 로그인 폼 */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* 이메일 */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              이메일
            </label>
            <input
              {...register('email')}
              type="email"
              id="email"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="example@email.com"
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-500">{errors.email.message}</p>
            )}
          </div>

          {/* 비밀번호 */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              비밀번호
            </label>
            <div className="mt-1 relative">
              <input
                {...register('password')}
                type={showPassword ? 'text' : 'password'}
                id="password"
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 px-3 flex items-center text-gray-400 hover:text-gray-600"
              >
                {showPassword ? '숨기기' : '보기'}
              </button>
            </div>
            {errors.password && (
              <p className="mt-1 text-sm text-red-500">{errors.password.message}</p>
            )}
          </div>

          {/* 로그인 버튼 */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? '로그인 중...' : '로그인'}
          </button>
        </form>

        {/* 회원가입 링크 */}
        <p className="text-center text-sm text-gray-500">
          계정이 없으신가요?{' '}
          <a href="/register" className="font-medium text-blue-600 hover:text-blue-500">
            회원가입
          </a>
        </p>
      </div>
    </div>
  );
}
