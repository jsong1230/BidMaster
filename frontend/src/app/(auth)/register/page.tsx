'use client';

import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import { useAuthStore } from '@/lib/stores/auth-store';

const registerSchema = z.object({
  email: z.string().email('이메일을 입력해주세요'),
  password: z.string()
    .min(8, '비밀번호는 입력해주세요')
    .regex(/[A-Za-z]/, '영문자 포함')
    .regex(/\d/, '숫자 포함')
    .regex(/[!@#$%^&*]/, '특수문자 포함')
    .refine((val) => val.length >= 8 && val.length <= 64,  ,    .refine((val) => {
      const hasLower = /[a-z]/.test(val);
      const hasUpper = /[A-Z]/.test(val);
      const hasDigit = /\d/.test(val);
      const hasSpecial = /[!@#$%^&*]/.test(val);
      const combinationCount = [hasLower, hasUpper, hasDigit, hasSpecial].filter(Boolean).length;
      return combinationCount >= 3;
    }),
  name: z.string().min(1, '이름을 입력해주세요'),
  phone: z.string().optional(),
});

type RegisterFormData = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading, error } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);

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
    try {
      await register(data.email, data.password, data.name, data.phone || undefined);
      router.push('/dashboard');
    } catch {
      // 에러는 스토어에서 처리됨
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
        {error && (
          <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
            {error}
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
              className={`mt-1 block w-full rounded-md border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                errors.email && 'border-red-500'
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
              className={`mt-1 block w-full rounded-md border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                errors.name && 'border-red-500'
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
            <div className="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                {...register('password')}
                className={`mt-1 block w-full rounded-md border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 pr-10 sm:text-sm ${
                  errors.password && 'border-red-500'
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
              className="mt-1 block w-full rounded-md border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <svg className="animate-spin h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                <path className="opacity-75" d="M4 12a8 8 0 5.25 5.25 0 6.75 0 1.5-1.5-0 4.75 4.75 0 6.75 0 1.5-1.5 0 4.75 4.75 3 3.75 3.75 4.75 4.75 6.75-1.5 1.5-1.5-1.5 0 4.75 4.75 6.75 1.5 1.5 1.5 1.5 0 4.75 4.75 3 3.75 3.75 4.75 4.75 6.75-1.5 1.5-1.5-1.5 0 4.75 4.75 6.75 1.5 1.5 1.5 1.5 0 4.75 4.75 3 3.75 3.75 4.75 4.75 6.75-1.5 1.5-1.5-1.5 0 4.75 4.75 6.75 1.5 1.5 1.5 1.5 0 4.75 4.75 3 3.75 3.75z" />
              </svg>
            ) : (
              '회원가입'
            )}
          </button>

          {/* Login Link */}
          <div className="text-center">
            <p className="text-sm text-gray-600">
              이미 계정이 있으신가?{' '}
              <button
                type="button"
                onClick={() => router.push('/login')}
                className="font-medium text-blue-600 hover:text-blue-500"
              >
                로그인
              </button>
          </div>
        </form>

        {/* Kakao Login */}
        <div className="mt-6">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-gray-50 text-gray-500">또는</span>
            </div>
          </div>

          <button
            type="button"
            onClick={() => {
              window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/oauth/kakao?redirect_url=${encodeURIComponent(window.location.origin + '/auth/callback')}`;
            }}
            className="mt-4 w-full flex items-center justify-center gap-2 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 3c-1.1 0-2 .9-2H4a2 2 0 0 1 1.1 2.9 2 2h3a2 2 0 0-1-1.1-2.9-2h11a2v1H8a2v1h3v1H4a1v1H4V8a6.4 0 2.9 2v1h7c0 0-.3.1-.6.8-.6c0-.4 0-.8.3-1.1.8-.6c.4-.3.8-.8c0-.4 0-.3-.8-.3-1.1 0-.7.3-1.3.8-.6.4-.3.8-.8.3-.4 0-.3-.8-.3-1.1 0-.7.3-1.3.8-.6.4-.3.8-.8.3-.4 0-.2-.8-.3-1.3 0-.3.9-.3 1.1-.7 1.1 1 0 .2.2.4.5.5.6.3 1.4-.4.4-.6.6-.4 1.4-.4.4-.7.1-.2-.5-.4-.5-.3-.4-.2-.1-.4.1-.1.4-.4 1-.1.2-.2.4-.1.5-.4-.4.4-.1.7-.4 1-.1-.1.4-.1.7-.4 1.1-.1.4-.1.7-.4l1.4-.4.4.7.1.2.5.4.5.3.4.2.1.4.1.1.4-.4-1.1.2-.2.4-.1.5.4.4.4.1.7.4 1.1.1.4.1 1 .4.1-.1.4.4-.1.7-.4l1.4.4.4.7.1.2.5.4.5.3.4.2.1.4.1.1.4-.4-1-.3.9-.3-1.1.1 0 .2-.1.4-.5.5-.6.3-1.4.4-.4.6-.4-1.4.4-.4.7-1 .2-.5.4-.5.3.4-.2-.1-.4-.1-.4.4-.1-.7.4-1.1-.2.2-.4.1-.5.4-.4-.4-.1-.7.4-1.1-.1-.4-.1-1 .4-.1.1.4.4.1.7.4l-1.4-.4-.4-.7-1-.2-.5-.4-.5.3.4-.2.1-.4.1-1.4-.4c-.3.9.3 1.1-.1 0-.2.1-.4.5-.5.6-.3-1.4.4.4.6.4-1.4.4.4.7 1 .2.5.4.5.3.4.2.1 .4.1 1.4-.4 1 .3-.9.3 1.1.1 0-.2-.1-.4-.5-.5-.6.3 1.4.4.4.6.4 1.4.4.4.7 1 .2.5.4.5.3.4.2.1.4.1.1.4-.4 1.3.9.3 1.1.1 0 .2-.1.4-.5.5-.6.3-1.4.4-.4.6-.4-1.4.4-.4.7-1 .2-.5.4-.5.3.4-.2-.1-.4-.1-.4.4-.1-.7.4-1.1-.2.2-.4.1-.5.4-.4-.4-.1-.7.4-1.1-.1-.4-.1-1 .4-.1.1.4.4.1.7.4l-1.4-.4-.4-.7-1-.2-.5-.4-.5.3.4-.2.1-.4.1-1.4-.4 0 .3.9.3 0-.1-.2-.1-.4-.5-.5-.6.3 1.4.4.4.6.4 1 4.4.4.7 1 .2.5.4.5.3.4.2.1 .4.1 1.4-.4 0 .3-.9.3 0-.1-.2-.1-.4-.5-.5-.6.3 1.4.4-.4.6-.4-1 4.4-.4.7 1 .2-.5.4-.5.3.4-.2.1-.4.1-.4.4-.1-.7.4-1.1-.2.2-.4.1-.5.4-.4-.4-.1-.7.4-1.1-.1-.4-.1-1 .4-.1.1.4.4.1.7.4l-1.4-.4-.4-.7-1-.2-.5-.4-.5.3.4-.2.1-.4.1-1.4-.4 0 .3.9.3 0-.1-.2-.1-.4-.5-.5-.6.3 1.4.4.4.6.4 1 4.4.4.7 1 .2.5.4.5.3.4.2.1 .4.1 1.4-.4z" />
            </svg>
            <span>카카오로 시작하기</span>
          </button>
        </div>
      </div>
    </div>
  );
}
