import React, { useState } from 'react';
import {
  ResponsiveContainer, ComposedChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Bar, Line, Cell
} from 'recharts';
import type { HistoryData } from '../../types';
import { CHART_COLORS } from '../../utils/colors';

interface Props {
  data: HistoryData[];
}

type ChartTab = 'sales_op' | 'margin' | 'eps' | 'fcf' | 'growth';

export function FundamentalChart({ data }: Props) {
  const [activeTab, setActiveTab] = useState<ChartTab>('sales_op');

  const chartData = data.map((d) => ({
    year: d.year,
    sales: d.sales_raw ? d.sales_raw / 100000000 : 0,
    op: d.op_raw ? d.op_raw / 100000000 : 0,
    op_margin: d.op_margin || 0,
    eps: d.eps_adjusted || 0, 
    fcf: d.fcf_raw ? d.fcf_raw / 100000000 : 0,
    fcf_margin: d.fcf_margin || 0,
    sales_yoy: d.sales_yoy || 0,
    op_yoy: d.op_yoy || 0,
    eps_yoy: d.eps_yoy || 0,
  }));

  const tabs: { id: ChartTab; label: string }[] = [
    { id: 'sales_op', label: '売上/営利' },
    { id: 'margin', label: '利益率' },
    { id: 'eps', label: 'EPS' },
    { id: 'fcf', label: 'FCF/Margin' },
    { id: 'growth', label: '成長率(QoQ/YoY)' },
  ];

  // Tooltipの数値をフォーマットし、小数を統一する関数
  const formatTooltipValue = (value: number, name: string) => {
    if (name.includes('%') || name.includes('率')) {
      return [`${value.toFixed(1)}%`, name];
    }
    if (name.includes('EPS')) {
      return [`${value.toFixed(1)}円`, name];
    }
    return [`${Math.round(value).toLocaleString()}`, name];
  };

  return (
    <div className="w-full flex flex-col gap-4">
      <div className="flex flex-wrap gap-2">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors border ${
              activeTab === t.id 
                ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' 
                : 'bg-white/5 text-slate-400 border-transparent hover:bg-white/10'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="w-full h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} vertical={false} />
            <XAxis dataKey="year" stroke={CHART_COLORS.text} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={{ stroke: CHART_COLORS.grid }} tickLine={false} />
            
            <Tooltip 
              contentStyle={{ backgroundColor: CHART_COLORS.tooltipBg, borderColor: CHART_COLORS.tooltipBorder, color: CHART_COLORS.tooltipText, borderRadius: '8px' }}
              itemStyle={{ color: CHART_COLORS.tooltipText }} // ← ★黒文字になるのを防ぐ
              formatter={formatTooltipValue} // ← ★小数を統一
            />
            <Legend wrapperStyle={{ paddingTop: '10px' }} />
            
            {activeTab === 'sales_op' && (
              <>
                <YAxis yAxisId="left" stroke={CHART_COLORS.text} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v.toLocaleString()}`} />
                <Bar yAxisId="left" dataKey="sales" name="売上高 (億円)" fill={CHART_COLORS.sales} radius={[4, 4, 0, 0]} />
                <Bar yAxisId="left" dataKey="op" name="営業利益 (億円)" fill={CHART_COLORS.op} radius={[4, 4, 0, 0]} />
              </>
            )}

            {activeTab === 'margin' && (
              <>
                <YAxis yAxisId="left" stroke={CHART_COLORS.text} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
                <Line yAxisId="left" type="monotone" dataKey="op_margin" name="営業利益率 (%)" stroke={CHART_COLORS.op} strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </>
            )}

            {activeTab === 'eps' && (
              <>
                <YAxis yAxisId="left" stroke={CHART_COLORS.text} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={false} tickLine={false} />
                <Bar yAxisId="left" dataKey="eps" name="EPS (円)" fill={CHART_COLORS.eps} radius={[4, 4, 0, 0]} />
              </>
            )}

            {activeTab === 'fcf' && (
              <>
                <YAxis yAxisId="left" stroke={CHART_COLORS.text} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="right" orientation="right" stroke={CHART_COLORS.eps} tick={{ fill: CHART_COLORS.eps, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
                
                {/* ★バーの文字色をツールチップで明示するため name を設定 */}
                <Bar yAxisId="left" dataKey="fcf" name="FCF (億円)">
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fcf >= 0 ? CHART_COLORS.op : CHART_COLORS.eps} />
                  ))}
                </Bar>
                <Line yAxisId="right" type="monotone" dataKey="fcf_margin" name="FCFマージン (%)" stroke="#fbbf24" strokeWidth={2} dot={{ r: 3 }} />
              </>
            )}

            {activeTab === 'growth' && (
              <>
                <YAxis yAxisId="left" stroke={CHART_COLORS.text} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
                <Line yAxisId="left" type="monotone" dataKey="sales_yoy" name="売上 増減率 (%)" stroke={CHART_COLORS.sales} strokeWidth={2} dot={false} />
                <Line yAxisId="left" type="monotone" dataKey="op_yoy" name="営利 増減率 (%)" stroke={CHART_COLORS.op} strokeWidth={2} dot={false} />
                <Line yAxisId="left" type="monotone" dataKey="eps_yoy" name="EPS 増減率 (%)" stroke={CHART_COLORS.eps} strokeWidth={2} dot={false} />
              </>
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}