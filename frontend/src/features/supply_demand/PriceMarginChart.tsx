import React from 'react';
import {
  ResponsiveContainer, ComposedChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Line, Area
} from 'recharts';
import type { PriceMarginData } from '../../types';
import { CHART_COLORS } from '../../utils/colors';

interface Props {
  data: PriceMarginData[];
}

export function PriceMarginChart({ data }: Props) {
  // 日付を見やすく整形 (例: "2024-05-01" -> "24/05/01")
  const formattedData = data.map((d) => ({
    ...d,
    displayDate: d.date ? d.date.substring(2).replace(/-/g, '/') : '',
  }));

  return (
    <div className="w-full h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={formattedData} margin={{ top: 20, right: 0, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} vertical={false} />
          
          <XAxis 
            dataKey="displayDate" 
            stroke={CHART_COLORS.text} 
            tick={{ fill: CHART_COLORS.text, fontSize: 12 }} 
            axisLine={{ stroke: CHART_COLORS.grid }} 
            tickLine={false}
            minTickGap={40} // ラベルが重ならないように間隔を空ける
          />
          
          {/* 左軸: 株価 (円) - 値動きが分かりやすいように auto で上下に余白を持たせる */}
          <YAxis 
            yAxisId="left" 
            stroke={CHART_COLORS.price} 
            tick={{ fill: CHART_COLORS.price, fontSize: 12 }} 
            axisLine={false} 
            tickLine={false} 
            domain={['auto', 'auto']}
            tickFormatter={(val) => `¥${val.toLocaleString()}`}
          />
          
          {/* 右軸: 信用残 (株) - 万株単位に変換 */}
          <YAxis 
            yAxisId="right" 
            orientation="right" 
            stroke={CHART_COLORS.marginBuy} 
            tick={{ fill: CHART_COLORS.text, fontSize: 12 }} 
            axisLine={false} 
            tickLine={false} 
            tickFormatter={(val) => `${(val / 10000).toFixed(0)}万`}
          />
          
          <Tooltip 
            contentStyle={{ backgroundColor: CHART_COLORS.tooltipBg, borderColor: CHART_COLORS.tooltipBorder, color: CHART_COLORS.tooltipText, borderRadius: '8px' }} 
            itemStyle={{ color: CHART_COLORS.tooltipText }} 
            labelStyle={{ color: CHART_COLORS.text, marginBottom: '4px' }}
          />
          
          <Legend wrapperStyle={{ paddingTop: '20px' }} />
          
          {/* 信用買い残 (紫・面グラフ) - 以前は週次だったため step 型で描画 */}
          <Area yAxisId="right" type="step" dataKey="margin_buy" name="信用買い残 (株)" fill={`${CHART_COLORS.marginBuy}33`} stroke={CHART_COLORS.marginBuy} strokeWidth={1.5} isAnimationActive={false} />
          
          {/* 信用売り残 (水色・面グラフ) */}
          <Area yAxisId="right" type="step" dataKey="margin_sell" name="信用売り残 (株)" fill={`${CHART_COLORS.marginSell}33`} stroke={CHART_COLORS.marginSell} strokeWidth={1.5} isAnimationActive={false} />

          {/* 株価 (黄・折れ線) - 上に重ねるため一番最後に記述 */}
          <Line yAxisId="left" type="monotone" dataKey="close" name="株価 (円)" stroke={CHART_COLORS.price} strokeWidth={2} dot={false} activeDot={{ r: 6 }} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}