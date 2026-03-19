/**
 * 월별 통계 차트 (BarChart + LineChart)
 */
'use client';

import dynamic from 'next/dynamic';
import type { MonthlyStat } from '@/types/dashboard';
import { formatMonth } from '@/lib/utils/format';

// Recharts 동적 임포트
const BarChart = dynamic(() => import('recharts').then((m) => m.BarChart), { ssr: false });
const Bar = dynamic(() => import('recharts').then((m) => m.Bar), { ssr: false });
const XAxis = dynamic(() => import('recharts').then((m) => m.XAxis), { ssr: false });
const YAxis = dynamic(() => import('recharts').then((m) => m.YAxis), { ssr: false });
const CartesianGrid = dynamic(() => import('recharts').then((m) => m.CartesianGrid), { ssr: false });
const Tooltip = dynamic(() => import('recharts').then((m) => m.Tooltip), { ssr: false });
const Legend = dynamic(() => import('recharts').then((m) => m.Legend), { ssr: false });
const ResponsiveContainer = dynamic(
  () => import('recharts').then((m) => m.ResponsiveContainer),
  { ssr: false }
);

interface StatisticsChartProps {
  data: MonthlyStat[];
  isLoading?: boolean;
}

function ChartSkeleton() {
  return <div className="h-56 bg-neutral-100 rounded animate-pulse" />;
}

export function StatisticsChart({ data, isLoading = false }: StatisticsChartProps) {
  const chartData = data.map((d) => ({
    month: formatMonth(d.month),
    참여: d.participationCount,
    낙찰: d.wonCount,
    낙찰률: d.winRate,
  }));

  return (
    <div className="bg-white border border-neutral-200 rounded-lg p-4 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
      <h3 className="text-sm font-semibold text-neutral-700 mb-4">월별 참여/낙찰 현황</h3>

      {isLoading ? (
        <ChartSkeleton />
      ) : data.length === 0 ? (
        <div className="h-56 flex items-center justify-center">
          <p className="text-xs text-neutral-400">데이터가 없습니다</p>
        </div>
      ) : (
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
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
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  border: '1px solid #E0E0E0',
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
              <Legend
                wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
                iconType="square"
                iconSize={10}
              />
              <Bar dataKey="참여" fill="#90A4AE" radius={[3, 3, 0, 0]} maxBarSize={40} />
              <Bar dataKey="낙찰" fill="#4CAF50" radius={[3, 3, 0, 0]} maxBarSize={40} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
