// frontend/src/features/calendar/FundamentalsTab.tsx

import React, { useState } from 'react';
import type { StockAnalysis } from '../../types';
import { FundamentalChart } from './FundamentalChart';
import { formatVal ,formatOku} from '../../utils/formatters';

interface Props { analysis: StockAnalysis; }

// --- フォーマッタ ---
const formatMoney = (val: number | null | undefined) => {
  if (val === null || val === undefined) return '-';
  const oku = val / 100000000;
  if (Math.abs(oku) >= 10000) {
    return `${(oku / 10000).toFixed(1)}兆円`;
  }
  if (Math.abs(oku) < 1) {
    return `${(val / 1000000).toFixed(0)}百万円`;
  }
  return `${oku.toLocaleString(undefined, { maximumFractionDigits: 1 })}億円`;
};

// --- 共通コンポーネント ---
const ExpandableText = ({ text }: { text: string }) => {
  const [expanded, setExpanded] = useState(false);
  if (!text) return <span className="text-slate-500">-</span>;
  if (text.length <= 15) return <span className="text-slate-300">{text}</span>;
  return (
    <div onClick={() => setExpanded(!expanded)} className="cursor-pointer text-left w-full">
      {expanded ? (
        <span className="whitespace-normal text-slate-300 leading-relaxed block">{text}</span>
      ) : (
        <span className="truncate max-w-[150px] inline-block text-slate-300 hover:text-slate-100 underline decoration-dashed decoration-slate-600 underline-offset-2 transition-colors">
          {text}
        </span>
      )}
    </div>
  );
};

const Th = ({ children, className = '' }: { children: React.ReactNode, className?: string }) => (
  <th className={`bg-slate-800/80 p-2 text-slate-400 font-normal border border-slate-700 text-left align-middle whitespace-nowrap ${className}`}>
    {children}
  </th>
);

const Td = ({ children, className = '' }: { children: React.ReactNode, className?: string }) => (
  <td className={`p-2 text-slate-100 font-bold border border-slate-700 text-right align-middle whitespace-nowrap ${className}`} style={{ fontFamily: 'Inter, sans-serif' }}>
    {children}
  </td>
);

const SectionTitle = ({ title }: { title: string }) => (
  <h3 className="text-sm font-bold text-slate-200 mb-2 border-l-4 border-blue-500 pl-2 mt-6 first:mt-0" style={{ fontFamily: '"Noto Sans JP", sans-serif' }}>
    {title}
  </h3>
);

const Sub = ({ children }: { children: React.ReactNode }) => (
  <span className="text-[10px] text-slate-400 ml-1.5 font-normal" style={{ fontFamily: 'Inter, sans-serif' }}>{children}</span>
);

const Val = ({ val, suffix = '', digits = 1 }: { val: number | null | undefined, suffix?: string, digits?: number }) => {
  if (val === null || val === undefined) return <span className="text-slate-500 font-normal">-</span>;
  return <span style={{ fontFamily: 'Inter, sans-serif' }}>{val.toFixed(digits)}{suffix}</span>;
};

const DiffVal = ({ val, suffix = '', digits = 1, reverseColor = false, threshold = 5 }: { val: number | null | undefined, suffix?: string, digits?: number, reverseColor?: boolean, threshold?: number }) => {
  if (val === null || val === undefined) return <span className="text-slate-500 font-normal">-</span>;
  if (val === 0) return <span className="text-slate-300 font-normal">0.0{suffix}</span>;
  
  const isOverThreshold = Math.abs(val) >= threshold;
  const isPositive = val > 0;
  
  let colorClass = 'text-slate-300 font-normal';
  if (isOverThreshold) {
    colorClass = reverseColor ? (isPositive ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold') : (isPositive ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold');
  }

  return <span className={colorClass} style={{ fontFamily: 'Inter, sans-serif' }}>{val > 0 ? '+' : ''}{val.toFixed(digits)}{suffix}</span>;
};

// キャッシュフローをミニバー風に表示するコンポーネント
const CFBar = ({ cfo, cfi, cff, fcf }: { cfo: number|null|undefined, cfi: number|null|undefined, cff: number|null|undefined, fcf: number|null|undefined }) => {
  const cfFormat = (val: number | null | undefined) => {
    if (val == null) return '-';
    const v = val / 100000000;
    return `${v > 0 ? '+' : ''}${v.toFixed(1)} 億円`;
  };
  const cfColor = (val: number | null | undefined) => {
     if (val == null) return 'text-slate-500 font-normal';
     return val > 0 ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold';
  };
  
  return (
    <div className="flex flex-col gap-1.5 text-xs">
      <div className="flex justify-between items-center"><span className="text-slate-400">営業CF (本業の稼ぎ)</span><span className={cfColor(cfo)} style={{ fontFamily: 'Inter, sans-serif' }}>{cfFormat(cfo)}</span></div>
      <div className="flex justify-between items-center"><span className="text-slate-400">投資CF (将来の投資)</span><span className={cfColor(cfi)} style={{ fontFamily: 'Inter, sans-serif' }}>{cfFormat(cfi)}</span></div>
      <div className="flex justify-between items-center"><span className="text-slate-400">財務CF (資金の調整)</span><span className={cfColor(cff)} style={{ fontFamily: 'Inter, sans-serif' }}>{cfFormat(cff)}</span></div>
      <div className="flex justify-between items-center border-t border-slate-700/50 pt-1 mt-1">
        <span className="text-slate-300 font-bold">フリーCF (残る現金)</span>
        <span className={cfColor(fcf)} style={{ fontFamily: 'Inter, sans-serif' }}>{cfFormat(fcf)}</span>
      </div>
    </div>
  );
};

// hide={true} の場合は何も表示しない MetricRow
const MetricRow = ({ label, value, sub, hide = false }: { label: string, value: React.ReactNode, sub?: React.ReactNode, hide?: boolean }) => {
  if (hide) return null;
  return (
    <div className="flex justify-between items-center border-b border-slate-700/50 py-1.5 hover:bg-slate-800/30 transition-colors px-1">
      <span className="text-xs text-slate-300" style={{ fontFamily: '"Noto Sans JP", sans-serif' }}>{label}</span>
      <div className="text-right">
        <span className="text-sm font-bold text-slate-100">{value}</span>
        {sub && <div className="text-[10px] text-slate-400 mt-0.5" style={{ fontFamily: 'Inter, sans-serif' }}>{sub}</div>}
      </div>
    </div>
  );
};

export function FundamentalsTab({ analysis }: Props) {
  const [timeframe, setTimeframe] = useState<'annual' | 'quarterly'>('annual');
  const [tableMode, setTableMode] = useState<'performance' | 'capital'>('performance');

  const displayData = timeframe === 'annual' ? analysis.history : analysis.quarterly_history;
  
  // ★ 追加: 株式・株主情報のデータ取得
  const majorList = analysis.major_shareholders || [];
  const reportCross = analysis.cross_shareholdings?.Report || {};
  const specList: any[] = Array.isArray(reportCross.Spec) ? reportCross.Spec : [];

  const val = analysis.valuation || {};
  const prof = analysis.profitability || {};
  const gro = analysis.growth || {};
  const act = analysis.actual || {};
  const perf = analysis.market_perf || {};
  const epsFactors = prof.eps_growth_factors || {};
  
  const quality = (analysis as any).quality || {};
  const momentum = (analysis as any).momentum || {};
  const health = (analysis as any).health || {};

  // 乖離額の算出
  const opCfDiff = (act.cfo != null && act.op != null) ? act.cfo - act.op : null;
  const opCfLabel = opCfDiff != null ? (opCfDiff > 0 ? '現金創出 > 利益 (健全)' : '現金創出 < 利益 (要確認)') : undefined;
  const opCfColor = opCfDiff != null ? (opCfDiff > 0 ? 'text-emerald-400' : 'text-rose-400') : '';

  return (
    <div className="h-full w-full overflow-y-auto pr-3 pb-20 custom-scrollbar text-sm bg-slate-950" style={{ fontFamily: '"Noto Sans JP", sans-serif' }}>
      
      {/* 
        ★ 修正: 12カラムグリッドを使用し、左側を 7 (3.5 : 3.5)、右側を 5 の比率に設定
        これにより3分割の見た目を保ちつつ、右側のグラフが広くなります。
      */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* 左・中央カラム: リスト群 (幅 7/12) */}
        <div className="lg:col-span-7 space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
            
            {/* ② 利益の質 */}
            <div>
              <SectionTitle title="利益の質" />
              <div className="mb-3 bg-slate-900 border border-slate-700 rounded p-3 shadow-sm">
                 <CFBar cfo={act.cfo} cfi={act.cfi} cff={act.cff} fcf={act.fcf} />
              </div>
              <div className="space-y-1">
                <MetricRow label="FCFマージン" value={<Val val={act.fcf_margin} suffix=" %" />} hide={act.fcf_margin == null} />
                <MetricRow label="営業CF ÷ 純利益" value={<Val val={prof.cfo_to_np} suffix=" %" digits={0} />} sub={prof.cfo_to_np && prof.cfo_to_np < 100 ? "100%未満 (利益が現金を伴っていない)" : "100%超 (健全)"} hide={prof.cfo_to_np == null} />
                <MetricRow label="営業利益と営業CFの乖離" value={<span className={opCfColor}>{opCfDiff! > 0 ? '+' : ''}{formatMoney(opCfDiff)}</span>} sub={opCfLabel} hide={opCfDiff == null} />
                <MetricRow 
                   label="純利成長 vs 営業CF成長" 
                   value={
                     <div className="flex items-center justify-end gap-2 text-xs font-mono">
                        <span className="text-slate-400 font-normal" style={{ fontFamily: '"Noto Sans JP", sans-serif' }}>純益:</span> <DiffVal val={gro.np_yoy} suffix="%" />
                        <span className="text-slate-600">|</span>
                        <span className="text-slate-400 font-normal" style={{ fontFamily: '"Noto Sans JP", sans-serif' }}>営CF:</span> <DiffVal val={quality.cfo_yoy} suffix="%" />
                     </div>
                   } 
                   hide={gro.np_yoy == null || quality.cfo_yoy == null} 
                />
              </div>
            </div>

            {/* ④ 資本効率・財務健全性 */}
            <div>
              <SectionTitle title="資本効率・財務健全性" />
              <div className="space-y-1">
                <MetricRow label="ROIC" value={<Val val={health.roic} suffix=" %" />} hide={health.roic == null} />
                <MetricRow label="ROE / ROA" value={<><Val val={prof.roe} suffix=" %" /> / <Val val={prof.roa_estimate} suffix=" %" /></>} hide={prof.roe == null && prof.roa_estimate == null} />
                <MetricRow label="営業利益 ÷ 自己資本" value={<Val val={prof.op_to_equity} suffix=" %" />} hide={prof.op_to_equity == null} />
                <MetricRow label="営業利益率" value={<Val val={prof.op_margin} suffix=" %" />} sub={`3年平均: ${prof.avg_op_margin_3y?.toFixed(1) || '-'}%`} hide={prof.op_margin == null} />
                <MetricRow label="総資産回転率" value={<Val val={prof.dupont?.current?.at} suffix=" 回" digits={2} />} hide={prof.dupont?.current?.at == null} />
                <MetricRow label="財務レバレッジ" value={<Val val={prof.dupont?.current?.fl} suffix=" 倍" digits={2} />} hide={prof.dupont?.current?.fl == null} />
              </div>
            </div>

          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
            {/* ③ 株価モメンタムと需給 */}
            <div>
              <SectionTitle title="株価モメンタムと需給" />
              <div className="space-y-1">
                <MetricRow label="1年株価パフォーマンス" value={<DiffVal val={perf.stock_1y} suffix="%" />} sub={`vs TOPIX: ${perf.topix_1y ? (perf.stock_1y! - perf.topix_1y).toFixed(1) + 'pt' : '-'} / vs 業種: ${perf.sector_1y ? (perf.stock_1y! - perf.sector_1y).toFixed(1) + 'pt' : '-'}`} hide={perf.stock_1y == null} />
                <MetricRow label="25日・75日騰落率" value={<><DiffVal val={momentum.ret_25d} suffix="%" /> / <DiffVal val={momentum.ret_75d} suffix="%" /></>} hide={momentum.ret_25d == null && momentum.ret_75d == null} />
                <MetricRow label="200日騰落率" value={<DiffVal val={momentum.ret_200d} suffix="%" />} hide={momentum.ret_200d == null} />
                <MetricRow label="25日・75日移動平均乖離" value={<><DiffVal val={momentum.ma25_diff} suffix="%" /> / <DiffVal val={momentum.ma75_diff} suffix="%" /></>} hide={momentum.ma25_diff == null && momentum.ma75_diff == null} />
                <MetricRow label="平均売買代金 (25日)" value={momentum.avg_val_25d ? formatMoney(momentum.avg_val_25d) : '-'} hide={momentum.avg_val_25d == null} />
                <MetricRow label="出来高急増率 (vs 平均)" value={<Val val={momentum.vol_spike} suffix=" 倍" digits={1} />} hide={momentum.vol_spike == null} />
                <MetricRow label="高値・安値からの距離" value={<><Val val={momentum.dist_high} suffix="%" /> / <Val val={momentum.dist_low} suffix="%" /></>} hide={momentum.dist_high == null && momentum.dist_low == null} />
                <MetricRow label="信用買残 / 信用倍率" value={perf.margin_buy ? `${(perf.margin_buy/10000).toFixed(0)}万株` : '-'} sub={perf.margin_ratio ? `倍率: ${perf.margin_ratio.toFixed(2)}倍` : undefined} hide={perf.margin_buy == null} />
                <MetricRow label="空売り残高比率の変化" value={<DiffVal val={momentum.short_interest_change} suffix="pt" />} hide={momentum.short_interest_change == null} />
              </div>
            </div>

            {/* EPS成長要因と資本政策 */}
            <div>
              <SectionTitle title="成長性と資本政策" />
              <div className="space-y-1">
                <MetricRow label="売上高 3年CAGR" value={<Val val={gro.sales_cagr_3y} suffix=" %" />} hide={gro.sales_cagr_3y == null} />
                <MetricRow label="営業利益 3年CAGR" value={<Val val={gro.op_cagr_3y} suffix=" %" />} hide={gro.op_cagr_3y == null} />
                <MetricRow label="EPS 3年CAGR" value={<Val val={gro.eps_cagr_3y} suffix=" %" />} hide={gro.eps_cagr_3y == null} />
                <MetricRow label="EPS前年比 (要因分解)" value={<DiffVal val={epsFactors?.eps_yoy} suffix="%" />} sub={`純益成長: ${epsFactors?.np_yoy?.toFixed(1) || '-'}% / 株式数寄与: ${epsFactors?.share_effect?.toFixed(1) || '-'}pt`} hide={epsFactors?.eps_yoy == null} />
                <MetricRow label="自己株式比率" value={<Val val={prof.treasury_ratio} suffix=" %" />} hide={prof.treasury_ratio == null} />
                <MetricRow label="潜在希薄化率" value={<Val val={prof.dilution_rate} suffix=" %" />} hide={prof.dilution_rate == null} />
                <MetricRow label="BPS / 配当性向" value={<>{typeof act.bps === 'number' ? act.bps.toLocaleString() : '-'}円 <Sub>({prof.payout_ratio?.toFixed(1) || '-'}%)</Sub></>} hide={act.bps == null && prof.payout_ratio == null} />
              </div>
            </div>
          </div>
        </div>

        {/* 右カラム: グラフ類 (幅 5/12 で左・中央より広め) */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          <div>
            <SectionTitle title="業績トレンド" />
            <div className="border border-slate-700 bg-slate-900 p-2 rounded-sm mb-4">
               <FundamentalChart data={displayData} />
            </div>
          </div>
          
          <div>
            <SectionTitle title="ガイダンス・トラッキング (期初予想と修正)" />
            <div className="overflow-x-auto custom-scrollbar border border-slate-700 bg-slate-900">
              <table className="w-full text-xs text-right whitespace-nowrap border-collapse">
                <thead className="bg-slate-800 text-slate-400 font-normal">
                  <tr>
                    <th className="py-2 px-2 text-left border-b border-slate-700">年度</th>
                    <th className="py-2 px-2 border-b border-slate-700">期初<Sub>(売/営)</Sub></th>
                    <th className="py-2 px-2 border-b border-slate-700">最終<Sub>(売/営)</Sub></th>
                    <th className="py-2 px-2 border-b border-slate-700">達成率</th>
                    <th className="py-2 px-2 border-b border-slate-700 text-center">期中修正<Sub>(Q)</Sub></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700 text-slate-300">
                  {analysis.guidance_history && analysis.guidance_history.length > 0 ? [...analysis.guidance_history].reverse().map((g, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/50 transition-colors">
                      <td className="py-1.5 px-2 text-left font-medium">{g.fy.replace('年','.')}</td>
                      <td className="py-1.5 px-2 text-slate-400">
                        <div style={{ fontFamily: 'Inter, sans-serif' }}>{formatOku(g.initial_sales)}</div>
                        <div style={{ fontFamily: 'Inter, sans-serif' }}>{formatOku(g.initial_op)}</div>
                      </td>
                      <td className="py-1.5 px-2 font-bold text-slate-100">
                        <div style={{ fontFamily: 'Inter, sans-serif' }}>{g.final_sales ? formatOku(g.final_sales) : '-'}</div>
                        <div style={{ fontFamily: 'Inter, sans-serif' }}>{g.final_op ? formatOku(g.final_op) : '-'}</div>
                      </td>
                      <td className="py-1.5 px-2">
                        <div className={g.sales_achieve && g.sales_achieve >= 100 ? 'text-rose-400 font-bold' : 'text-slate-300'} style={{ fontFamily: 'Inter, sans-serif' }}>{g.sales_achieve ? `${g.sales_achieve.toFixed(1)}%` : '-'}</div>
                        <div className={g.op_achieve && g.op_achieve >= 100 ? 'text-rose-400 font-bold' : 'text-slate-300'} style={{ fontFamily: 'Inter, sans-serif' }}>{g.op_achieve ? `${g.op_achieve.toFixed(1)}%` : '-'}</div>
                      </td>
                      <td className="py-1.5 px-2 text-center align-middle">
                        <div className="flex flex-col gap-1 items-center text-[10px]" style={{ fontFamily: 'Inter, sans-serif' }}>
                          <div className="flex gap-1 h-3.5 items-center">
                            {g.sales_up.length > 0 && <span className="text-rose-400 font-bold bg-rose-500/10 px-1 rounded">↑ {g.sales_up.join(',')}</span>}
                            {g.sales_down.length > 0 && <span className="text-emerald-400 font-bold bg-emerald-500/10 px-1 rounded">↓ {g.sales_down.join(',')}</span>}
                            {g.sales_up.length === 0 && g.sales_down.length === 0 && <span className="text-slate-600 font-normal">-</span>}
                          </div>
                          <div className="flex gap-1 h-3.5 items-center">
                            {g.op_up.length > 0 && <span className="text-rose-400 font-bold bg-rose-500/10 px-1 rounded">↑ {g.op_up.join(',')}</span>}
                            {g.op_down.length > 0 && <span className="text-emerald-400 font-bold bg-emerald-500/10 px-1 rounded">↓ {g.op_down.join(',')}</span>}
                            {g.op_up.length === 0 && g.op_down.length === 0 && <span className="text-slate-600 font-normal">-</span>}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )) : <tr><td colSpan={5} className="py-4 text-center text-slate-500">予実データがありません</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* 業績推移表 */}
      <SectionTitle title="業績推移 (過去10期)" />
      <div className="flex gap-1 mb-2 text-xs">
        <button onClick={() => setTimeframe('annual')} className={`px-2 py-0.5 border ${timeframe === 'annual' ? 'bg-slate-700 text-white border-slate-500' : 'bg-slate-900 text-slate-400 border-slate-700 hover:bg-slate-800'}`}>通期</button>
        <button onClick={() => setTimeframe('quarterly')} className={`px-2 py-0.5 border ${timeframe === 'quarterly' ? 'bg-slate-700 text-white border-slate-500' : 'bg-slate-900 text-slate-400 border-slate-700 hover:bg-slate-800'}`}>四半期</button>
        <div className="w-2" />
        <button onClick={() => setTableMode('performance')} className={`px-2 py-0.5 border ${tableMode === 'performance' ? 'bg-slate-700 text-white border-slate-500' : 'bg-slate-900 text-slate-400 border-slate-700 hover:bg-slate-800'}`}>業績</button>
        <button onClick={() => setTableMode('capital')} className={`px-2 py-0.5 border ${tableMode === 'capital' ? 'bg-slate-700 text-white border-slate-500' : 'bg-slate-900 text-slate-400 border-slate-700 hover:bg-slate-800'}`}>資本</button>
      </div>
      
      <div className="overflow-x-auto max-h-[400px] overflow-y-auto custom-scrollbar border border-slate-700 bg-slate-900">
        <table className="w-full text-xs text-right whitespace-nowrap border-collapse font-inter">
          <thead className="bg-slate-800 text-slate-400 sticky top-0 z-10 font-noto">
            <tr>
              <th className="py-2 px-2 text-left font-normal border-b border-slate-700">決算期</th>
              {tableMode === 'performance' ? (
                <>
                  <th className="py-2 px-2 font-normal border-b border-slate-700">売上高 <Sub>YoY</Sub></th>
                  <th className="py-2 px-2 font-normal border-b border-slate-700">営業利益 <Sub>YoY</Sub></th>
                  <th className="py-2 px-2 font-normal border-b border-slate-700">経常利益 <Sub>YoY</Sub></th>
                  <th className="py-2 px-2 font-normal border-b border-slate-700">当期利益 <Sub>YoY</Sub></th>
                  <th className="py-2 px-2 font-normal border-b border-slate-700">営業利益率</th>
                  <th className="py-2 px-2 font-normal border-b border-slate-700">修正EPS <Sub>YoY</Sub></th>
                </>
              ) : (
                <>
                  <th className="py-2 px-2 font-normal border-b border-slate-700">株式数 <Sub>YoY</Sub></th>
                  <th className="py-2 px-2 font-normal border-b border-slate-700">自己株式数 <Sub>YoY</Sub></th>
                  <th className="py-2 px-2 font-normal border-b border-slate-700">自己株式比率</th>
                  <th className="py-2 px-2 font-normal border-b border-slate-700">修正EPS</th>
                  <th className="py-2 px-2 font-normal border-b border-slate-700">希薄化DEPS</th>
                  {timeframe === 'annual' && <th className="py-2 px-2 font-normal border-b border-slate-700">ROE</th>}
                </>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {[...displayData].reverse().map((h: any, i) => {
              const opMargin = typeof h.sales_raw === 'number' && typeof h.op_raw === 'number' && h.sales_raw !== 0 ? (h.op_raw / h.sales_raw) * 100 : null;
              const isForecast = h.year.includes('予');
              return (
                <tr key={i} className={`hover:bg-slate-800/80 transition-colors ${isForecast ? 'bg-blue-900/10' : ''}`}>
                  <td className={`py-2 px-2 text-left font-bold ${isForecast ? 'text-blue-300' : 'text-slate-300'}`}>{h.year}</td>
                  
                  {tableMode === 'performance' ? (
                    <>
                      <td className="py-2 px-2">
                        <span className="text-slate-100 font-bold mr-2">{h.sales_str}</span>
                        <DiffVal val={h.sales_yoy} suffix="%" />
                      </td>
                      <td className="py-2 px-2">
                        <span className={`font-bold mr-2 ${h.op_raw < 0 ? 'text-emerald-400' : 'text-slate-100'}`}>{h.op_str}</span>
                        <DiffVal val={h.op_yoy} suffix="%" />
                      </td>
                      <td className="py-2 px-2">
                        <span className={`font-bold mr-2 ${h.odp_raw < 0 ? 'text-emerald-400' : 'text-slate-100'}`}>{h.odp_str || '-'}</span>
                        <DiffVal val={h.odp_yoy} suffix="%" />
                      </td>
                      <td className="py-2 px-2">
                        <span className={`font-bold mr-2 ${h.np_raw < 0 ? 'text-emerald-400' : 'text-slate-100'}`}>{h.np_str || '-'}</span>
                        <DiffVal val={h.np_yoy} suffix="%" />
                      </td>
                      <td className="py-2 px-2 text-slate-300 font-bold">
                        {typeof opMargin === 'number' ? `${opMargin.toFixed(1)}%` : '-'}
                      </td>
                      <td className="py-2 px-2">
                        <span className="text-slate-300 font-bold mr-2">{typeof h.eps_adjusted === 'number' ? `${h.eps_adjusted.toFixed(1)}` : '-'}</span>
                        <DiffVal val={h.eps_yoy} suffix="%" />
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="py-2 px-2">
                        <span className="text-slate-300 font-bold mr-2">{typeof h.out_shares === 'number' ? `${(h.out_shares / 10000).toFixed(0)}万株` : '-'}</span>
                        <DiffVal val={h.out_shares_yoy} suffix="%" reverseColor threshold={1} />
                      </td>
                      <td className="py-2 px-2">
                        <span className="text-slate-400 font-bold mr-2">{typeof h.tr_shares === 'number' ? `${(h.tr_shares / 10000).toFixed(0)}万株` : '-'}</span>
                        <DiffVal val={h.tr_shares_yoy} suffix="%" threshold={1} />
                      </td>
                      <td className="py-2 px-2 text-slate-300 font-bold">{typeof h.tr_ratio === 'number' ? `${h.tr_ratio.toFixed(2)}%` : '-'}</td>
                      <td className="py-2 px-2 text-slate-100 font-bold">{typeof h.eps_adjusted === 'number' ? `${h.eps_adjusted.toFixed(1)}円` : '-'}</td>
                      <td className="py-2 px-2 text-slate-500 font-bold">{typeof h.deps_adjusted === 'number' ? `${h.deps_adjusted.toFixed(1)}円` : '-'}</td>
                      {timeframe === 'annual' && <td className="py-2 px-2 text-slate-300 font-bold">{typeof h.roe_raw === 'number' ? `${h.roe_raw.toFixed(1)}%` : '-'}</td>}
                    </>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* ★ 追加: 大株主、政策保有株式、株式数推移 */}
      <div className="mt-8 border-t border-slate-800 pt-6" />
      <SectionTitle title="株式・株主の状況" />
      
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        {/* 大株主 */}
        <div className="bg-slate-900 border border-slate-700 rounded-md p-4">
          <h4 className="text-xs font-bold text-slate-300 mb-3 border-b border-slate-700/50 pb-2">主要株主構成 (上位10名)</h4>
          {majorList.length > 0 ? (
            <div className="overflow-x-auto custom-scrollbar">
              <table className="w-full text-xs text-left whitespace-nowrap border-collapse">
                <thead className="bg-slate-800 text-slate-400 font-normal">
                  <tr>
                    <th className="py-2 px-2 text-center border-b border-slate-700 border-r">順位</th>
                    <th className="py-2 px-2 border-b border-slate-700 border-r">株主名</th>
                    <th className="py-2 px-2 text-right border-b border-slate-700">保有比率 <Sub>(増減)</Sub></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50 bg-slate-900/30">
                  {majorList.slice(0, 10).map((s: any, idx: number) => {
                    const ratio = parseFloat(s.ratio || s.ShsRatio || s.HoldingRatio || 0);
                    return (
                      <tr key={idx} className="hover:bg-slate-800/50 transition-colors">
                        <td className="py-2 px-2 text-center text-slate-500 border-r border-slate-700/50" style={{ fontFamily: 'Inter, sans-serif' }}>{s.rank || idx + 1}</td>
                        <td className="py-2 px-2 border-r border-slate-700/50 truncate max-w-[200px]">{s.name || s.HldrName || s.Name || '不明'}</td>
                        <td className="py-2 px-2 text-right">
                          <span className="text-slate-100 font-bold mr-2" style={{ fontFamily: 'Inter, sans-serif' }}>
                            {typeof ratio === 'number' ? `${ratio.toFixed(2)}%` : '-'}
                          </span>
                          <DiffVal val={s.diff} suffix="pt" digits={2} threshold={0.5} />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (<div className="text-xs text-slate-500 p-4 border border-slate-700 bg-slate-900/50">大株主データがありません</div>)}
        </div>

        {/* 政策保有株式 */}
        <div className="bg-slate-900 border border-slate-700 rounded-md p-4">
          <div className="flex justify-between items-end mb-3 border-b border-slate-700/50 pb-2">
            <h4 className="text-xs font-bold text-slate-300">政策保有株式の状況 (保有銘柄)</h4>
            <div className="flex gap-4 text-[10px]">
              <div><span className="text-slate-400">銘柄数: </span><span className="text-slate-200 font-bold">{reportCross.ListedIss ?? '-'}</span></div>
              <div><span className="text-slate-400">BS計上額: </span><span className="text-slate-200 font-bold">{formatOku(reportCross.ListedBookVal)}</span></div>
            </div>
          </div>
          {specList.length > 0 ? (
            <div className="overflow-x-auto custom-scrollbar">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-800 text-slate-400 font-normal sticky top-0">
                  <tr>
                    <th className="py-2 px-2 border-b border-slate-700 border-r">保有先銘柄</th>
                    <th className="py-2 px-2 text-right border-b border-slate-700 border-r">当期BS計上額</th>
                    <th className="py-2 px-2 text-left border-b border-slate-700">保有目的・理由</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50 bg-slate-900/30">
                  {specList.slice(0, 10).map((item: any, idx: number) => (
                    <tr key={idx} className="hover:bg-slate-800/50 transition-colors group">
                      <td className="py-2 px-2 border-r border-slate-700/50 whitespace-nowrap max-w-[140px] truncate">{item.IsrName || '-'}</td>
                      <td className="py-2 px-2 border-r border-slate-700/50 text-right font-bold text-emerald-400" style={{ fontFamily: 'Inter, sans-serif' }}>{formatOku(item.CurBookVal)}</td>
                      <td className="py-2 px-2 align-middle max-w-[200px]">
                        <ExpandableText text={item.HoldRat || '純投資・事業関係'} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (<div className="text-xs text-slate-500 p-4 border border-slate-700 bg-slate-900/50">開示データがありません</div>)}
        </div>
      </div>

      {/* 株式数推移テーブル */}
      <div className="bg-slate-900 border border-slate-700 rounded-md p-4">
        <h4 className="text-xs font-bold text-slate-300 mb-3 border-b border-slate-700/50 pb-2">発行済株式数・自己株式の推移 (過去10期)</h4>
        <div className="overflow-x-auto custom-scrollbar border border-slate-700 rounded-sm">
          <table className="w-full text-xs text-right whitespace-nowrap border-collapse font-inter">
            <thead className="bg-slate-800 text-slate-400 sticky top-0 font-noto">
              <tr>
                <th className="py-2 px-2 text-left font-normal border-b border-slate-700 border-r">決算期</th>
                <th className="py-2 px-2 font-normal border-b border-slate-700">発行済株式数 <Sub>YoY</Sub></th>
                <th className="py-2 px-2 font-normal border-b border-slate-700">自己株式数 <Sub>YoY</Sub></th>
                <th className="py-2 px-2 font-normal border-b border-slate-700 border-l">自己株式比率</th>
                <th className="py-2 px-2 font-normal border-b border-slate-700 border-l">修正EPS</th>
                <th className="py-2 px-2 font-normal border-b border-slate-700">希薄化DEPS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50 bg-slate-900/30">
              {[...displayData].reverse().map((h: any, i) => {
                const isForecast = h.year.includes('予');
                return (
                  <tr key={i} className={`hover:bg-slate-800/80 transition-colors ${isForecast ? 'bg-blue-900/10' : ''}`}>
                    <td className={`py-2 px-2 text-left font-bold border-r border-slate-700/50 ${isForecast ? 'text-blue-300' : 'text-slate-300'}`}>{h.year}</td>
                    <td className="py-2 px-2">
                      <span className="text-slate-300 font-bold mr-2">{typeof h.out_shares === 'number' ? `${(h.out_shares / 10000).toFixed(0)}万株` : '-'}</span>
                      <DiffVal val={h.out_shares_yoy} suffix="%" reverseColor threshold={1} />
                    </td>
                    <td className="py-2 px-2">
                      <span className="text-slate-400 font-bold mr-2">{typeof h.tr_shares === 'number' ? `${(h.tr_shares / 10000).toFixed(0)}万株` : '-'}</span>
                      <DiffVal val={h.tr_shares_yoy} suffix="%" threshold={1} />
                    </td>
                    <td className="py-2 px-2 text-slate-300 font-bold border-l border-slate-700/50">{typeof h.tr_ratio === 'number' ? `${h.tr_ratio.toFixed(2)}%` : '-'}</td>
                    <td className="py-2 px-2 text-slate-100 font-bold border-l border-slate-700/50">{typeof h.eps_adjusted === 'number' ? `${h.eps_adjusted.toFixed(1)}円` : '-'}</td>
                    <td className="py-2 px-2 text-slate-500 font-bold">{typeof h.deps_adjusted === 'number' ? `${h.deps_adjusted.toFixed(1)}円` : '-'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}