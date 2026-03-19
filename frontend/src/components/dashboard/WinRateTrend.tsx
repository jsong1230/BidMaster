/**
 * 월별 낙찰률 추이 차트 (AreaChart)
 */
'use client';

import dynamic from 'next/dynamic';
import type { MonthlyStat } from '@/types/dashboard';
import { formatMonth } from '@/lib/utils/format';

// Recharts 동적 임포트 (SSR 비활성)
const AreaChart = dynamic(
  () => import('recharts').then((mod) => mod.AreaChart),
  { ssr: false }
);
const Area = dynamic(() => import('recharts').then((mod) => mod.Area), { ssr: false });
const XAxis = dynamic(() => import('recharts').then((mod) => mod.XAxis), { ssr: false });
const YAxis = dynamic(() => import('recharts').then((mod) => mod.YAxis), { ssr: false });
const CartesianGrid = dynamic(
  () => import('recharts').then((mod) => mod.CartesianGrid),
  { ssr: false }
);
const Tooltip = dynamic(() => import('recharts').then((mod) => mod.Tooltip), { ssr: false });
const ResponsiveContainer = dynamic(
  () => import('recharts').then((mod) => mod.ResponsiveContainer),
  { ssr: false }
);

interface WinRateTrendProps {
  data: MonthlyStat[];
  isLoading?: boolean;
}

/** 커스텀 Tooltip 내용 (타입 이슈 우회) */
interface TooltipPayload {
  name: string;
  value: number;
  color: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div
      style={{
        background: 'white',
        border: '1px solid #E0E0E0',
        borderRadius: 8,
        padding: '8px 12px',
        fontSize: 12,
      }}
    >
      <p style={{ color: '#212121', marginBottom: 4 }}>{label}</p>
      {payload.map((entry) => (
        <p key={entry.name} style={{ color: entry.color }}>
          낙찰률: {typeof entry.value === 'number' ? `${entry.value.toFixed(1)}%` : `${entry.value}%`}
        </p>
      ))}
    </div>
  );
}

function ChartSkeleton() {
  return <div className="h-48 bg-neutral-100 rounded animate-pulse" />;
}

export function WinRateTrend({ data, isLoading = false }: WinRateTrendProps) {
  const chartData = data.map((d) => ({
    month: formatMonth(d.month),
    낙찰률: d.winRate,
  }));

  return (
    <div className="bg-white border border-neutral-200 rounded-lg p-4 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
      {/* 헤더 */}
      <h3 className="text-sm font-semibold text-neutral-700 mb-4">월별 낙찰률 추이</h3>

      {isLoading ? (
        <ChartSkeleton />
      ) : data.length === 0 ? (
        <div className="h-48 flex items-center justify-center">
          <p className="text-xs text-neutral-400">데이터가 없습니다</p>
        </div>
      ) : (
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="winRateGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#78909C" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#78909C" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#E0E0E0" vertical={false} />
              <XAxis
                dataKey="month"
                tick={{ fontSize: 10, fill: '#9E9E9E' }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 10, fill: '#9E9E9E' }}
                tickLine={false}
                axisLine={false}
                domain={[0, 100]}
                tickFormatter={(v: number) => `${v}%`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="낙찰률"
                stroke="#78909C"
                strokeWidth={2}
                fill="url(#winRateGradient)"
                dot={{ fill: '#78909C', r: 3 }}
                activeDot={{ r: 5 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
