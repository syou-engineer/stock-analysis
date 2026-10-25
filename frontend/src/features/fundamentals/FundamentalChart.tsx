// frontend/src/features/calendar/FundamentalChart.tsx

import React, { useState } from 'react';
import {
  ResponsiveContainer, ComposedChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Bar, Line, Cell, ReferenceLine
} from 'recharts';
import type { HistoryData } from '../../types';
import { CHART_COLORS } from '../../utils/colors';

interface Props {
  data: HistoryData[];
}

type ChartTab = 'sales_op_margin' | 'eps' | 'roe_roa' | 'cf' | 'fcf' | 'equity_ratio' | 'valuation';
// type RangeTab = 'recent' | 'all';

export function FundamentalChart({ data }: Props) {
  const [activeTab, setActiveTab] = useState<ChartTab>('sales_op_margin');
  const [range, setRange] = useState<'recent' | 'all'>('all');

  const isQuarterly = data.length > 0 && (data[0].year.includes('Q') || data[0].year.includes('四半期'));
  const limit = isQuarterly ? 12 : 10;
  
  const sortedData = [...data].sort((a, b) => a.year.localeCompare(b.year));
  const limitedData = range === 'recent' ? sortedData.slice(-limit) : sortedData;

  const chartData = limitedData.map((d) => {
    const isForecast = d.year.includes('予');
    const anyD = d as any;
    return {
      year: d.year.replace('年度', '').replace('年', ''),
      isForecast,
      
      sales: d.sales_raw ? d.sales_raw / 100000000 : 0,
      op: d.op_raw ? d.op_raw / 100000000 : 0,
      op_margin: d.op_margin || 0,
      
      eps_actual: !isForecast ? (d.eps_adjusted || 0) : null,
      eps_forecast: isForecast ? (d.eps_adjusted || 0) : null,
      eps_yoy: d.eps_yoy || null,
      
      roe: d.roe_raw || null,
      roa: anyD.roa_estimate || null,
      
      cfo: anyD.cfo ? anyD.cfo / 100000000 : null,
      cfi: anyD.cfi ? anyD.cfi / 100000000 : null,
      cff: anyD.cff ? anyD.cff / 100000000 : null,
      fcf: d.fcf_raw ? d.fcf_raw / 100000000 : null,
      fcf_margin: d.fcf_margin || null,
      
      equity_ratio: anyD.equity_ratio || null,
      
      // バリュエーション追加
      calc_per: anyD.calc_per || null,
      calc_pbr: anyD.calc_pbr || null,
    };
  });

  const tabs: { id: ChartTab; label: string }[] = [
    { id: 'sales_op_margin', label: '売上/営利/率' },
    { id: 'eps', label: 'EPS' },
    { id: 'roe_roa', label: 'ROE/ROA' },
    { id: 'cf', label: '営/投/財CF' },
    { id: 'fcf', label: 'FCF' },
    { id: 'equity_ratio', label: '自己資本比率' },
    { id: 'valuation', label: 'PER/PBR' },
  ];

  const formatTooltipValue = (value: number, name: string) => {
    if (value === null || value === undefined) return ['-', name];
    if (name.includes('%') || name.includes('率') || name.includes('ROE') || name.includes('ROA') || name.includes('比率')) {
      return [`${value.toFixed(1)}%`, name];
    }
    if (name.includes('EPS')) {
      return [`${value.toFixed(1)}円`, name];
    }
    if (name.includes('PER') || name.includes('PBR')) {
      return [`${value.toFixed(1)}倍`, name];
    }
    return [`${Math.round(value).toLocaleString()}`, name];
  };

  return (
    <div className="w-full flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-2">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors border ${
                activeTab === t.id 
                  ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' 
                  : 'bg-slate-800 text-slate-400 border-transparent hover:bg-slate-700'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        
        {/* <div className="flex gap-1 text-xs">
          <button 
            onClick={() => setRange('recent')} 
            className={`px-3 py-1 font-medium rounded-md transition-colors border ${
              range === 'recent' ? 'bg-slate-700 text-white border-slate-500' : 'bg-slate-900 text-slate-400 border-slate-700 hover:bg-slate-800'
            }`}
          >
            {isQuarterly ? '直近3年(12Q)' : '直近10年'}
          </button>
          <button 
            onClick={() => setRange('all')} 
            className={`px-3 py-1 font-medium rounded-md transition-colors border ${
              range === 'all' ? 'bg-slate-700 text-white border-slate-500' : 'bg-slate-900 text-slate-400 border-slate-700 hover:bg-slate-800'
            }`}
          >
            全期間表示
          </button>
        </div> */}
      </div>

      <div className="w-full h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} vertical={false} />
            <XAxis dataKey="year" stroke={CHART_COLORS.text} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={{ stroke: CHART_COLORS.grid }} tickLine={false} minTickGap={20} />
            
            <Tooltip 
              contentStyle={{ backgroundColor: CHART_COLORS.tooltipBg, borderColor: CHART_COLORS.tooltipBorder, color: CHART_COLORS.tooltipText, borderRadius: '8px' }}
              itemStyle={{ color: CHART_COLORS.tooltipText }}
              formatter={formatTooltipValue}
            />
            <Legend wrapperStyle={{ paddingTop: '10px' }} />
            
            {activeTab === 'sales_op_margin' && (
              <>
                <YAxis yAxisId="left" stroke={CHART_COLORS.text} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v.toLocaleString()}`} />
                <YAxis yAxisId="right" orientation="right" stroke={CHART_COLORS.text} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
                <ReferenceLine yAxisId="left" y={0} stroke={CHART_COLORS.grid} />
                
                <Bar yAxisId="left" dataKey="sales" name="売上高 (億円)" fill={CHART_COLORS.sales} radius={[2, 2, 0, 0]} />
                <Bar yAxisId="left" dataKey="op" name="営業利益 (億円)" fill={CHART_COLORS.op} radius={[2, 2, 0, 0]} />
                <Line yAxisId="right" type="monotone" dataKey="op_margin" name="営業利益率 (%)" stroke="#f59e0b" strokeWidth={3} dot={{ r: 3 }} activeDot={{ r: 5 }} connectNulls />
              </>
            )}

            {activeTab === 'eps' && (
              <>
                <YAxis yAxisId="left" stroke={CHART_COLORS.text} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="right" orientation="right" stroke={CHART_COLORS.text} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
                <ReferenceLine yAxisId="left" y={0} stroke={CHART_COLORS.grid} />
                <ReferenceLine yAxisId="right" y={0} stroke={CHART_COLORS.grid} strokeDasharray="3 3" />

                <Bar yAxisId="left" dataKey="eps_actual" name="実績EPS" fill={CHART_COLORS.eps} radius={[2, 2, 0, 0]} barSize={range === 'all' ? 12 : 32} />
                <Bar yAxisId="left" dataKey="eps_forecast" name="予想EPS" fill={`${CHART_COLORS.eps}80`} radius={[2, 2, 0, 0]} barSize={range === 'all' ? 12 : 32} />
                
                <Line 
                  yAxisId="right" 
                  type="monotone" 
                  dataKey={(d) => (d.eps_yoy && d.eps_yoy < 500 && d.eps_yoy > -500) ? d.eps_yoy : null} 
                  name="EPS成長率 (YoY)" 
                  stroke="#fb7185" 
                  strokeWidth={2} 
                  dot={{ r: 2, fill: '#fb7185' }} 
                  connectNulls
                />
              </>
            )}

            {activeTab === 'roe_roa' && (
              <>
                <YAxis yAxisId="left" stroke={CHART_COLORS.text} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
                <ReferenceLine yAxisId="left" y={0} stroke={CHART_COLORS.grid} />
                
                <Line yAxisId="left" type="monotone" dataKey="roe" name="ROE (%)" stroke="#ec4899" strokeWidth={3} dot={{ r: 3 }} connectNulls={true} />
                <Line yAxisId="left" type="monotone" dataKey="roa" name="ROA (%)" stroke="#8b5cf6" strokeWidth={3} dot={{ r: 3 }} connectNulls={true} />
              </>
            )}

            {activeTab === 'cf' && (
              <>
                <YAxis yAxisId="left" stroke={CHART_COLORS.text} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={false} tickLine={false} />
                <ReferenceLine yAxisId="left" y={0} stroke={CHART_COLORS.grid} />
                
                <Bar yAxisId="left" dataKey="cfo" name="営業CF (億円)" fill={CHART_COLORS.op} radius={[2, 2, 0, 0]} />
                <Bar yAxisId="left" dataKey="cfi" name="投資CF (億円)" fill="#fbbf24" radius={[2, 2, 0, 0]} />
                <Bar yAxisId="left" dataKey="cff" name="財務CF (億円)" fill="#64748b" radius={[2, 2, 0, 0]} />
              </>
            )}

            {activeTab === 'fcf' && (
              <>
                <YAxis yAxisId="left" stroke={CHART_COLORS.text} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="right" orientation="right" stroke={CHART_COLORS.text} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
                <ReferenceLine yAxisId="left" y={0} stroke={CHART_COLORS.grid} strokeDasharray="3 3" />

                <Bar yAxisId="left" dataKey="fcf" name="FCF (億円)">
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fcf && entry.fcf >= 0 ? CHART_COLORS.op : CHART_COLORS.eps} />
                  ))}
                </Bar>
                <Line yAxisId="right" type="monotone" dataKey="fcf_margin" name="FCFマージン (%)" stroke="#fbbf24" strokeWidth={2} dot={{ r: 3 }} connectNulls={true} />
              </>
            )}

            {activeTab === 'equity_ratio' && (
              <>
                <YAxis yAxisId="left" stroke={CHART_COLORS.text} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
                <ReferenceLine yAxisId="left" y={0} stroke={CHART_COLORS.grid} />
                
                <Line yAxisId="left" type="monotone" dataKey="equity_ratio" name="自己資本比率 (%)" stroke="#0ea5e9" strokeWidth={3} dot={{ r: 3 }} connectNulls={true} />
              </>
            )}

            {/* バリュエーション (PER / PBR) */}
            {activeTab === 'valuation' && (
              <>
                <YAxis yAxisId="left" stroke={CHART_COLORS.text} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}倍`} />
                <YAxis yAxisId="right" orientation="right" stroke={CHART_COLORS.text} tick={{ fill: CHART_COLORS.text, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}倍`} />
                <ReferenceLine yAxisId="left" y={0} stroke={CHART_COLORS.grid} />

                <Line yAxisId="left" type="monotone" dataKey="calc_per" name="PER (倍)" stroke="#14b8a6" strokeWidth={3} dot={{ r: 4 }} connectNulls={true} />
                <Line yAxisId="right" type="monotone" dataKey="calc_pbr" name="PBR (倍)" stroke="#f43f5e" strokeWidth={3} dot={{ r: 4 }} connectNulls={true} />
              </>
            )}

          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}