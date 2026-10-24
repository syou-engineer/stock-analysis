import React, { useState } from 'react';
import type { StockAnalysis } from '../../types';
import { FundamentalChart } from './FundamentalChart';
import { TrendingUp, Award, PieChart, Activity, RefreshCw, Calendar, Clock, ArrowRight, Target, Users, Shield, Layers, Wallet, BarChart2 } from 'lucide-react';
import { formatVal, formatOku } from '../../utils/formatters';

interface Props { analysis: StockAnalysis; }

const ExpandableText = ({ text }: { text: string }) => {
  const [expanded, setExpanded] = useState(false);
  if (!text) return <span>-</span>;
  if (text.length <= 15) return <span className="text-slate-400">{text}</span>;
  return (
    <div onClick={() => setExpanded(!expanded)} className="cursor-pointer text-left w-full">
      {expanded ? (
        <span className="whitespace-normal text-slate-300 text-[10px] leading-relaxed block bg-slate-800/80 p-1.5 rounded">{text}</span>
      ) : (
        <span className="truncate max-w-[120px] inline-block text-slate-400 hover:text-slate-300 text-[11px] underline decoration-dashed decoration-slate-600 underline-offset-2">
          {text}
        </span>
      )}
    </div>
  );
};

export function FundamentalsTab({ analysis }: Props) {
  const [timeframe, setTimeframe] = useState<'annual' | 'quarterly'>('annual');
  const [tableMode, setTableMode] = useState<'performance' | 'capital'>('performance');

  const displayData = timeframe === 'annual' ? analysis.history : analysis.quarterly_history;
  const guidance_history = analysis.guidance_history || [];

  const majorList = analysis.major_shareholders || [];
  const reportCross = analysis.cross_shareholdings?.Report || {};
  const specList: any[] = Array.isArray(reportCross.Spec) ? reportCross.Spec : [];

  // const formatVal = (val: number | null | undefined, suffix: string = '', digits: number = 1) => {
  //   if (val === null || val === undefined) return '-';
  //   return `${val > 0 ? '+' : ''}${val.toFixed(digits)}${suffix}`;
  // };

  // const formatOku = (val: number | null | undefined) => {
  //   if (val === null || val === undefined) return '-';
  //   const oku = val / 100000000;
  //   if (Math.abs(oku) < 1) {
  //     return `${(val / 1000000).toLocaleString(undefined, { maximumFractionDigits: 0 })} 百万円`;
  //   }
  //   return `${oku.toLocaleString(undefined, { maximumFractionDigits: 1 })} 億円`;
  // };

  const ColorVal = ({ val, suffix = '', digits = 1, reverseColor = false }: { val: number | null | undefined, suffix?: string, digits?: number, reverseColor?: boolean }) => {
    if (val === null || val === undefined) return <span>-</span>;
    const isPositive = val > 0;
    const colorClass = reverseColor ? (isPositive ? 'text-emerald-400' : 'text-rose-400') : (isPositive ? 'text-rose-400' : 'text-emerald-400');
    return <span className={`font-bold ${colorClass}`}>{formatVal(val, suffix, digits)}</span>;
  };

  // ★ 追加: 目立たせすぎない変化率表示（閾値を設定可能に）
  const SmartDiff = ({ val, suffix = '', digits = 1, threshold = 10, reverseColor = false }: { val: number | null | undefined, suffix?: string, digits?: number, threshold?: number, reverseColor?: boolean }) => {
    if (typeof val !== 'number') return <span className="text-transparent text-[10px]">(-0.0%)</span>;
    
    // 変化率が閾値(±10%など)未満ならグレーにして目立たせない
    if (Math.abs(val) < threshold) {
      return <span className="text-[10px] text-slate-500">({val > 0 ? '+' : ''}{val.toFixed(digits)}{suffix})</span>;
    }

    // 閾値以上の変化は色をつける
    const isPositive = val > 0;
    const colorClass = reverseColor ? (isPositive ? 'text-emerald-400' : 'text-rose-400') : (isPositive ? 'text-rose-400' : 'text-emerald-400');
    return <span className={`text-[10px] font-bold ${colorClass}`}>({val > 0 ? '+' : ''}{val.toFixed(digits)}{suffix})</span>;
  };

  const currentQ = analysis.period?.current_type || '';
  const currentYear = analysis.history?.length > 0 ? analysis.history[analysis.history.length - (analysis.history[analysis.history.length-1].year.includes('予') ? 2 : 1)]?.year : '';
  const periodLabel = currentQ === 'FY' ? `${currentYear}年度 (通期実績)` : `${currentYear}年度 ${currentQ} (累計実績)`;

  const dupont = analysis.profitability.dupont;
  const cf = analysis.actual;
  const epsFactors = analysis.profitability.eps_growth_factors;

  return (
    <div className="h-full w-full overflow-y-auto pr-2 space-y-4 animate-in fade-in duration-500 pb-20 custom-scrollbar">
      
      {/* 1. 企業価値の変容サマリー (過去平均との比較を強調) */}
      <div className="bg-gradient-to-br from-slate-900/90 to-slate-950 backdrop-blur-xl border border-white/10 p-5 rounded-xl shadow-lg relative overflow-hidden shrink-0">
        <div className="absolute top-0 left-0 w-1/2 h-full bg-gradient-to-r from-blue-500/5 to-transparent pointer-events-none" />
        <h2 className="text-sm font-bold text-white mb-4 flex items-center gap-2 relative z-10">
          <RefreshCw className="text-blue-400" size={16} /> 業績モメンタムとバリュエーションの現在地
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative z-10">
          
          {/* 左側: 成長と収益性のモメンタム */}
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-2">
              <span className="text-xs text-slate-400 font-medium">直近決算のモメンタム (vs 過去水準)</span>
              <span className="text-xs text-slate-300 bg-white/10 px-2 py-0.5 rounded border border-white/20">{periodLabel}</span>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white/5 rounded p-2">
                <p className="text-[10px] text-slate-400 mb-1">売上高 成長率</p>
                <div className="flex items-end gap-2">
                  <span className="text-lg"><ColorVal val={analysis.growth.sales_yoy} suffix="%" /></span>
                  {typeof analysis.growth.sales_cagr_3y === 'number' && typeof analysis.growth.sales_yoy === 'number' && (
                    <span className="text-[10px] text-slate-500 mb-1">
                      (過去3年: <span className={analysis.growth.sales_yoy > analysis.growth.sales_cagr_3y ? 'text-rose-400' : 'text-slate-400'}>{analysis.growth.sales_cagr_3y.toFixed(1)}%</span>)
                    </span>
                  )}
                </div>
              </div>

              <div className="bg-white/5 rounded p-2">
                <p className="text-[10px] text-slate-400 mb-1">営業利益率</p>
                <div className="flex items-end gap-2">
                  <span className="text-lg text-white font-bold">{typeof analysis.profitability.op_margin === 'number' ? `${analysis.profitability.op_margin.toFixed(1)}%` : '-'}</span>
                  {typeof analysis.profitability.avg_op_margin_3y === 'number' && typeof analysis.profitability.op_margin === 'number' && (
                    <span className="text-[10px] text-slate-500 mb-1">
                      (過去3年: <span className={analysis.profitability.op_margin > analysis.profitability.avg_op_margin_3y ? 'text-rose-400' : 'text-slate-400'}>{analysis.profitability.avg_op_margin_3y.toFixed(1)}%</span>)
                    </span>
                  )}
                </div>
              </div>

              <div className="bg-white/5 rounded p-2">
                <p className="text-[10px] text-slate-400 mb-1">EPS 成長率</p>
                <div className="flex items-end gap-2">
                  <span className="text-lg"><ColorVal val={analysis.growth.eps_yoy} suffix="%" /></span>
                  {typeof analysis.growth.avg_eps_yoy_3y === 'number' && typeof analysis.growth.eps_yoy === 'number' && (
                    <span className="text-[10px] text-slate-500 mb-1">
                      (過去3年: <span className={analysis.growth.eps_yoy > analysis.growth.avg_eps_yoy_3y ? 'text-rose-400' : 'text-slate-400'}>{analysis.growth.avg_eps_yoy_3y.toFixed(1)}%</span>)
                    </span>
                  )}
                </div>
              </div>

              <div className="bg-white/5 rounded p-2">
                <p className="text-[10px] text-slate-400 mb-1">利益の質 (CFO/NP)</p>
                <div className="flex items-end gap-2">
                  <span className="text-lg text-white font-bold">{typeof analysis.profitability.cfo_to_np === 'number' ? `${analysis.profitability.cfo_to_np.toFixed(0)}%` : '-'}</span>
                  <span className="text-[9px] text-slate-500 mb-1">※100%超で良質</span>
                </div>
              </div>
            </div>
          </div>

          {/* 右側: 市場の織り込み (バリュエーション) */}
          <div className="space-y-3 relative">
            <div className="hidden md:flex absolute -left-5 top-1/2 -translate-y-1/2 text-slate-600"><ArrowRight size={20} /></div>
            <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-2">
              <span className="text-xs text-slate-400 font-medium">市場の織り込み・バリュエーション水準</span>
              <span className="text-xs text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">現在値 vs 過去1年平均</span>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white/5 rounded p-3 flex flex-col justify-center">
                <p className="text-[10px] text-slate-400 mb-1">予想 PER (現在)</p>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl text-white font-bold">{typeof analysis.valuation.forward_per === 'number' ? analysis.valuation.forward_per.toFixed(1) : '-'}</span>
                  <span className="text-xs text-slate-500">倍</span>
                </div>
                {typeof analysis.valuation.per_avg === 'number' && typeof analysis.valuation.forward_per === 'number' && (
                  <div className="mt-1 flex flex-col gap-1 text-[10px]">
                    <div className="flex justify-between items-center text-slate-500">
                      <span>過去1年平均: {analysis.valuation.per_avg.toFixed(1)}倍</span>
                      <ColorVal val={((analysis.valuation.forward_per / analysis.valuation.per_avg) - 1) * 100} suffix="%" />
                    </div>
                    <div className="text-right">
                      <span className={`font-bold ${analysis.valuation.forward_per > analysis.valuation.per_avg ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {analysis.valuation.forward_per > analysis.valuation.per_avg ? '↑ 1年平均を上回る' : '↓ 1年平均を下回る'}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              <div className="bg-white/5 rounded p-3 flex flex-col justify-center">
                <p className="text-[10px] text-slate-400 mb-1">実績 PBR (現在)</p>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl text-white font-bold">{typeof analysis.valuation.pbr === 'number' ? analysis.valuation.pbr.toFixed(2) : '-'}</span>
                  <span className="text-xs text-slate-500">倍</span>
                </div>
                {typeof analysis.valuation.pbr_avg === 'number' && typeof analysis.valuation.pbr === 'number' && (
                  <div className="mt-1 flex flex-col gap-1 text-[10px]">
                    <div className="flex justify-between items-center text-slate-500">
                      <span>過去1年平均: {analysis.valuation.pbr_avg.toFixed(2)}倍</span>
                      <ColorVal val={((analysis.valuation.pbr / analysis.valuation.pbr_avg) - 1) * 100} suffix="%" />
                    </div>
                    <div className="text-right">
                      <span className={`font-bold ${analysis.valuation.pbr > analysis.valuation.pbr_avg ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {analysis.valuation.pbr > analysis.valuation.pbr_avg ? '↑ 1年平均を上回る' : '↓ 1年平均を下回る'}
                      </span>
                    </div>
                  </div>
                )}
              </div>
              
                <div className="col-span-2 flex flex-col gap-1.5 bg-slate-900/50 p-2.5 rounded text-xs border border-white/5">
                 <div className="flex items-center justify-between border-b border-white/10 pb-1.5">
                   <span className="text-slate-400 font-medium">直近1年間の株価パフォーマンス</span>
                   <ColorVal val={analysis.market_perf.stock_1y} suffix="%" digits={1} />
                 </div>
                 
                 <div className="flex items-center justify-between">
                   <span className="text-slate-400">vs TOPIX</span>
                   <div className="flex items-center gap-2">
                     <span className="text-slate-500 text-[10px] bg-slate-800 px-1 rounded">指数: {typeof analysis.market_perf.topix_1y === 'number' ? `${analysis.market_perf.topix_1y.toFixed(1)}%` : '-'}</span>
                     {typeof analysis.market_perf.stock_1y === 'number' && typeof analysis.market_perf.topix_1y === 'number' ? (
                        <span className={`font-bold ${analysis.market_perf.stock_1y - analysis.market_perf.topix_1y > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                          {(analysis.market_perf.stock_1y - analysis.market_perf.topix_1y) > 0 ? '+' : ''}{(analysis.market_perf.stock_1y - analysis.market_perf.topix_1y).toFixed(1)}pt
                        </span>
                     ) : <span className="text-slate-500">-</span>}
                   </div>
                 </div>

                 <div className="flex items-center justify-between">
                   <span className="text-slate-400">vs 業種別 ({analysis.basic.industry})</span>
                   <div className="flex items-center gap-2">
                     <span className="text-slate-500 text-[10px] bg-slate-800 px-1 rounded">指数: {typeof analysis.market_perf.sector_1y === 'number' ? `${analysis.market_perf.sector_1y.toFixed(1)}%` : '-'}</span>
                     {typeof analysis.market_perf.stock_1y === 'number' && typeof analysis.market_perf.sector_1y === 'number' ? (
                        <span className={`font-bold ${analysis.market_perf.stock_1y - analysis.market_perf.sector_1y > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                          {(analysis.market_perf.stock_1y - analysis.market_perf.sector_1y) > 0 ? '+' : ''}{(analysis.market_perf.stock_1y - analysis.market_perf.sector_1y).toFixed(1)}pt
                        </span>
                     ) : <span className="text-slate-500">-</span>}
                   </div>
                 </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. 4 Quadrants */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 shrink-0">
        <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 p-4 rounded-xl">
          <h3 className="text-sm font-bold text-blue-400 mb-3 flex items-center gap-2"><TrendingUp size={16}/> Growth (長期成長性)</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between items-center"><span className="text-slate-400">売上 3年CAGR</span><span className="text-white font-medium">{formatVal(analysis.growth.sales_cagr_3y, '%')}</span></div>
            <div className="flex justify-between items-center"><span className="text-slate-400">営利 3年CAGR</span><span className="text-white font-medium">{formatVal(analysis.growth.op_cagr_3y, '%')}</span></div>
            <div className="flex justify-between items-center"><span className="text-slate-400">EPS 3年CAGR</span><span className="text-white font-medium">{formatVal(analysis.growth.eps_cagr_3y, '%')}</span></div>
          </div>
        </div>
        
        <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 p-4 rounded-xl">
          <h3 className="text-sm font-bold text-emerald-400 mb-3 flex items-center gap-2"><Award size={16}/> Quality (収益・財務)</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-slate-400">営業利益率</span><span className="text-white font-medium">{typeof analysis.profitability.op_margin === 'number' ? `${analysis.profitability.op_margin.toFixed(1)}%` : '-'}</span></div>
            <div className="flex justify-between"><span className="text-slate-400">ROE (直近)</span><span className="text-white font-medium">{typeof analysis.profitability.roe === 'number' ? `${analysis.profitability.roe.toFixed(1)}%` : '-'}</span></div>
            <div className="flex justify-between"><span className="text-slate-400">自己資本比率</span><span className="text-white font-medium">{typeof analysis.profitability.equity_ratio === 'number' ? `${analysis.profitability.equity_ratio.toFixed(1)}%` : '-'}</span></div>
            <div className="flex justify-between" title="100%以上なら利益以上の現金を稼げている"><span className="text-slate-400 border-b border-dashed border-slate-500">利益の質 (CFO/NP)</span><span className="text-white font-medium">{typeof analysis.profitability.cfo_to_np === 'number' ? `${analysis.profitability.cfo_to_np.toFixed(0)}%` : '-'}</span></div>
          </div>
        </div>

        <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 p-4 rounded-xl">
          <h3 className="text-sm font-bold text-amber-400 mb-3 flex items-center gap-2"><PieChart size={16}/> Valuation (割安性)</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-slate-400">予想 PER</span><span className="text-white font-medium">{typeof analysis.valuation.forward_per === 'number' ? `${analysis.valuation.forward_per.toFixed(1)} 倍` : '-'}</span></div>
            <div className="flex justify-between"><span className="text-slate-400">実績 PBR</span><span className="text-white font-medium">{typeof analysis.valuation.pbr === 'number' ? `${analysis.valuation.pbr.toFixed(2)} 倍` : '-'}</span></div>
            <div className="flex justify-between">
              <span className="text-slate-400">BPS / 配当性向</span>
              <span className="text-white font-medium">{typeof analysis.actual.bps === 'number' ? analysis.actual.bps.toLocaleString() : '-'} 円 <span className="text-slate-500 text-[10px]">({typeof analysis.profitability.payout_ratio === 'number' ? `${analysis.profitability.payout_ratio.toFixed(1)}%` : '-'})</span></span>
            </div>
            <div className="flex justify-between"><span className="text-slate-400 border-b border-dashed border-slate-500">PEGレシオ</span><span className="text-white font-medium">{typeof analysis.valuation.peg === 'number' ? analysis.valuation.peg.toFixed(2) : '-'}</span></div>
          </div>
        </div>

        <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 p-4 rounded-xl">
          <h3 className="text-sm font-bold text-rose-400 mb-3 flex items-center gap-2"><Activity size={16}/> Capital Policy</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-slate-400">自己株式比率</span><span className="text-blue-400 font-bold">{typeof analysis.profitability.treasury_ratio === 'number' ? `${analysis.profitability.treasury_ratio.toFixed(1)}%` : '-'}</span></div>
            <div className="flex justify-between"><span className="text-slate-400">潜在希薄化率</span><span className={`font-bold ${typeof analysis.profitability.dilution_rate === 'number' && analysis.profitability.dilution_rate > 3 ? 'text-rose-400' : 'text-white'}`}>{typeof analysis.profitability.dilution_rate === 'number' ? `${analysis.profitability.dilution_rate.toFixed(1)}%` : '-'}</span></div>
          </div>
        </div>
      </div>

      {/* 3. デュポン分析 ＆ 資本・EPSの要因分解 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 shrink-0">
        <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 p-5 rounded-xl shadow-md">
          <h2 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
            <Layers className="text-blue-400" size={16} /> ROEの変化要因 (デュポン分析) 
          </h2>
          <div className="space-y-4">
            <div className="flex justify-between items-end border-b border-white/10 pb-2">
              <span className="text-xs text-slate-400">ROE (自己資本利益率)</span>
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-500">{typeof dupont?.prev?.roe === 'number' ? `${dupont.prev.roe.toFixed(1)}%` : '-'}</span>
                <ArrowRight size={12} className="text-slate-500" />
                <span className={`text-xl font-bold ${typeof dupont?.current?.roe === 'number' && typeof dupont?.prev?.roe === 'number' && dupont.current.roe > dupont.prev.roe ? 'text-rose-400' : 'text-white'}`}>{typeof dupont?.current?.roe === 'number' ? `${dupont.current.roe.toFixed(1)}%` : '-'}</span>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="bg-white/5 p-2 rounded">
                <p className="text-[10px] text-slate-400 mb-1">純利益率 <br/><span className="text-[8px] text-slate-600">(収益性)</span></p>
                <div className="flex flex-col">
                  <span className="text-slate-500">{typeof dupont?.prev?.npm === 'number' ? `${dupont.prev.npm.toFixed(1)}%` : '-'}</span>
                  <span className="font-bold text-white">{typeof dupont?.current?.npm === 'number' ? `${dupont.current.npm.toFixed(1)}%` : '-'}</span>
                </div>
              </div>
              <div className="bg-white/5 p-2 rounded text-center">
                <p className="text-[10px] text-slate-400 mb-1">総資産回転率 <br/><span className="text-[8px] text-slate-600">(資産効率)</span></p>
                <div className="flex flex-col">
                  <span className="text-slate-500">{typeof dupont?.prev?.at === 'number' ? `${dupont.prev.at.toFixed(2)}x` : '-'}</span>
                  <span className="font-bold text-white">{typeof dupont?.current?.at === 'number' ? `${dupont.current.at.toFixed(2)}x` : '-'}</span>
                </div>
              </div>
              <div className="bg-white/5 p-2 rounded text-right">
                <p className="text-[10px] text-slate-400 mb-1">財務レバレッジ <br/><span className="text-[8px] text-slate-600">(借入依存度)</span></p>
                <div className="flex flex-col items-end">
                  <span className="text-slate-500">{typeof dupont?.prev?.fl === 'number' ? `${dupont.prev.fl.toFixed(2)}x` : '-'}</span>
                  <span className={`font-bold ${typeof dupont?.current?.fl === 'number' && typeof dupont?.prev?.fl === 'number' && dupont.current.fl > dupont.prev.fl ? 'text-emerald-400' : 'text-white'}`}>{typeof dupont?.current?.fl === 'number' ? `${dupont.current.fl.toFixed(2)}x` : '-'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 p-5 rounded-xl shadow-md">
          <h2 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
            <BarChart2 className="text-emerald-400" size={16} /> 資本政策とEPS成長の要因分解
          </h2>
          {epsFactors ? (
            <div className="space-y-4">
              <div className="flex justify-between items-end border-b border-white/10 pb-2">
                <span className="text-xs text-slate-400">EPS成長率 (前年比)</span>
                <ColorVal val={epsFactors.eps_yoy} suffix="%" digits={1} />
              </div>
              <div className="space-y-3 pt-1">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-400">① 本業の稼ぎ (純利益の成長)</span>
                  <ColorVal val={epsFactors.np_yoy} suffix="%" digits={1} />
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-400">② 平均株式数の変化による寄与</span> 
                  <ColorVal val={epsFactors.share_effect} suffix="pt" digits={1} />
                </div>
              </div>
              <div className="bg-slate-900/50 rounded p-2 text-[10px] text-slate-500 mt-2">
                平均株式数の増減: <span className="font-bold text-white">{typeof epsFactors.share_yoy === 'number' ? `${epsFactors.share_yoy.toFixed(1)}%` : '-'}</span> 
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-500 py-4 text-center">要因分解データがありません</p>
          )}
        </div>
      </div>

      {/* 4. 会社予想の癖 */}
      <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 p-5 rounded-xl shadow-md shrink-0">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-4 gap-2">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Target className="text-purple-400" size={18} />
            期初予想と修正履歴 (ガイダンス・トラッキング)
          </h2>
          <span className="text-[10px] text-slate-400 bg-slate-800 px-2 py-1 rounded">※ 達成率は最終着地ベース</span>
        </div>

        {guidance_history && guidance_history.length > 0 ? (
          <div className="overflow-x-auto flex justify-center">
            <table className="w-full md:w-auto md:min-w-[85%] text-sm text-left whitespace-nowrap">
              <thead className="bg-white/5 text-slate-400 font-medium border-b border-white/10 text-xs">
                <tr>
                  <th className="py-2.5 px-4 rounded-tl-lg">年度</th>
                  <th className="py-2.5 px-4 text-right">期初予想 (売上 / 営利)</th>
                  <th className="py-2.5 px-4 text-right">最終着地 (売上 / 営利)</th>
                  <th className="py-2.5 px-4 text-center">期初予想 達成率</th>
                  <th className="py-2.5 px-4 text-center rounded-tr-lg">期中修正のタイミング・回数</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-slate-200">
                {[...guidance_history].reverse().map((g, idx) => {
                  const isCurrent = g.final_op === null && g.final_sales === null;
                  return (
                    <tr key={idx} className="hover:bg-white/5 transition-colors">
                      <td className="py-2.5 px-4 font-mono text-slate-300 align-middle">{g.fy}</td>
                      <td className="py-2.5 px-4 text-right">
                        <div className="text-slate-300 mb-0.5">{formatOku(g.initial_sales)}</div>
                        <div className="text-slate-400">{formatOku(g.initial_op)}</div>
                      </td>
                      <td className="py-2.5 px-4 text-right">
                        {isCurrent ? (
                          <div className="text-slate-500 h-full flex items-center justify-end">-</div>
                        ) : (
                          <>
                            <div className="text-white font-bold mb-0.5">{formatOku(g.final_sales)}</div>
                            <div className="text-white font-bold">{formatOku(g.final_op)}</div>
                          </>
                        )}
                      </td>
                      <td className="py-2.5 px-4 text-center align-middle">
                        <div className="text-xs mb-1">
                           <span className="text-slate-500 mr-1">売上</span>
                           {g.sales_achieve !== null && g.sales_achieve !== undefined ? (
                             <span className={`font-bold ${g.sales_achieve >= 100 ? 'text-rose-400' : 'text-emerald-400'}`}>
                               {g.sales_achieve.toFixed(1)}%
                             </span>
                           ) : '-'}
                        </div>
                        <div className="text-xs">
                           <span className="text-slate-500 mr-1">営利</span>
                           {g.op_achieve !== null && g.op_achieve !== undefined ? (
                             <span className={`font-bold ${g.op_achieve >= 100 ? 'text-rose-400' : 'text-emerald-400'}`}>
                               {g.op_achieve.toFixed(1)}%
                             </span>
                           ) : '-'}
                        </div>
                      </td>
                      <td className="py-2.5 px-4 text-center align-middle">
                        <div className="text-[10px] flex items-center justify-center gap-1 mb-1">
                          <span className="text-slate-500 mr-1 w-6">売上</span>
                          {g.sales_up.length > 0 && <span className="text-rose-400 font-bold bg-rose-500/10 px-1 rounded">↑ {g.sales_up.join(',')}</span>}
                          {g.sales_down.length > 0 && <span className="text-emerald-400 font-bold bg-emerald-500/10 px-1 rounded">↓ {g.sales_down.join(',')}</span>}
                          {g.sales_up.length === 0 && g.sales_down.length === 0 && <span className="text-slate-600">-</span>}
                        </div>
                        <div className="text-[10px] flex items-center justify-center gap-1">
                          <span className="text-slate-500 mr-1 w-6">営利</span>
                          {g.op_up.length > 0 && <span className="text-rose-400 font-bold bg-rose-500/10 px-1 rounded">↑ {g.op_up.join(',')}</span>}
                          {g.op_down.length > 0 && <span className="text-emerald-400 font-bold bg-emerald-500/10 px-1 rounded">↓ {g.op_down.join(',')}</span>}
                          {g.op_up.length === 0 && g.op_down.length === 0 && <span className="text-slate-600">-</span>}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-slate-500 text-center py-4">予実データがありません</p>
        )}
      </div>

      {/* 5. 業績推移グラフ */}
      <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 p-5 rounded-xl shadow-md shrink-0">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-3">
             <h2 className="text-base font-bold text-white">業績推移と収益構造の分析</h2>
             {timeframe === 'quarterly' && <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">単独四半期ベース</span>}
          </div>
          <div className="flex bg-slate-800/50 p-1 rounded-md border border-white/10 w-fit">
            <button onClick={() => setTimeframe('annual')} className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-all ${timeframe === 'annual' ? 'bg-slate-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'}`}><Calendar size={14} /> 年次</button>
            <button onClick={() => setTimeframe('quarterly')} className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-all ${timeframe === 'quarterly' ? 'bg-slate-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'}`}><Clock size={14} /> 四半期 (単独)</button>
          </div>
        </div>
        <FundamentalChart data={displayData} />
      </div>

      {/* 6. 詳細テーブル (業績 ⇔ 資本政策のタブ切り替え) */}
      <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 p-4 rounded-xl shadow-md shrink-0">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-3 gap-2">
          <h2 className="text-sm font-bold text-white">
            {timeframe === 'annual' ? '10年間の詳細データ' : '直近40四半期の詳細データ (単独四半期)'}
          </h2>
          <div className="flex bg-slate-800/50 p-1 rounded-md border border-white/10 w-fit">
            <button onClick={() => setTableMode('performance')} className={`px-3 py-1 rounded text-xs font-medium transition-all ${tableMode === 'performance' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'}`}>業績・収益性</button>
            <button onClick={() => setTableMode('capital')} className={`px-3 py-1 rounded text-xs font-medium transition-all ${tableMode === 'capital' ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'}`}>資本政策・株式数</button>
          </div>
        </div>
        
        <div className="overflow-x-auto max-h-[500px] overflow-y-auto custom-scrollbar">
          <table className="w-full text-xs text-right whitespace-nowrap relative">
            <thead className="bg-slate-900 text-slate-400 font-medium border-b border-white/10 sticky top-0 z-10">
              <tr>
                <th className="py-2 px-1.5 text-left">期間</th>
                {tableMode === 'performance' ? (
                  <>
                    <th className="py-2 px-1.5">売上高 <span className="text-[9px] text-slate-500 font-normal ml-0.5">(前期比)</span></th>
                    <th className="py-2 px-1.5">営業利益 <span className="text-[9px] text-slate-500 font-normal ml-0.5">(前期比)</span></th>
                    <th className="py-2 px-1.5">経常利益 <span className="text-[9px] text-slate-500 font-normal ml-0.5">(前期比)</span></th>
                    <th className="py-2 px-1.5">当期利益 <span className="text-[9px] text-slate-500 font-normal ml-0.5">(前期比)</span></th>
                    <th className="py-2 px-1.5">営業利益率</th>
                    <th className="py-2 px-1.5">EPS (※累計)</th>
                    {timeframe === 'annual' && <th className="py-2 px-1.5">FCF</th>}
                  </>
                ) : (
                  <>
                    <th className="py-2 px-1.5">発行済株式総数 <span className="text-[9px] text-slate-500 font-normal ml-0.5">(前期比)</span></th>
                    <th className="py-2 px-1.5">自己株式数 <span className="text-[9px] text-slate-500 font-normal ml-0.5">(前期比)</span></th>
                    <th className="py-2 px-1.5">自己株式比率</th>
                    <th className="py-2 px-1.5">EPS (調整後)</th>
                    <th className="py-2 px-1.5">潜在希薄化後 DEPS</th>
                    {timeframe === 'annual' && <th className="py-2 px-1.5">ROE</th>}
                  </>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[...displayData].reverse().map((h: any, i) => {
                const opMargin = typeof h.sales_raw === 'number' && typeof h.op_raw === 'number' && h.sales_raw !== 0 ? (h.op_raw / h.sales_raw) * 100 : null;
                
                let rowBgClass = 'hover:bg-white/5';
                if (timeframe === 'quarterly') {
                  if (h.year.includes('1Q')) rowBgClass = 'bg-blue-500/5 hover:bg-blue-500/10';
                  else if (h.year.includes('2Q')) rowBgClass = 'bg-emerald-500/5 hover:bg-emerald-500/10';
                  else if (h.year.includes('3Q')) rowBgClass = 'bg-amber-500/5 hover:bg-amber-500/10';
                  else if (h.year.includes('4Q')) rowBgClass = 'bg-purple-500/5 hover:bg-purple-500/10';
                }

                return (
                  <tr key={i} className={`${rowBgClass} transition-colors`}>
                    <td className="py-2 px-1.5 text-left font-medium text-slate-300">{h.year}</td>
                    
                    {tableMode === 'performance' ? (
                      <>
                        <td className="py-2 px-1.5">
                          <div className="flex items-center justify-end gap-1 font-mono">
                            <span className="w-14 text-right text-slate-200">{h.sales_str}</span>
                            {/* ★変更: SmartDiffを適用。10%未満のブレは色を消す */}
                            <span className="w-14 text-left"><SmartDiff val={h.sales_yoy} suffix="%" threshold={10} /></span>
                          </div>
                        </td>
                        <td className="py-2 px-1.5">
                          <div className="flex items-center justify-end gap-1 font-mono">
                            <span className={`w-14 text-right ${typeof h.op_raw === 'number' && h.op_raw < 0 ? 'text-emerald-400' : 'text-slate-200'}`}>{h.op_str}</span>
                            {/* ★変更: 利益はブレやすいので閾値を20%に */}
                            <span className="w-14 text-left"><SmartDiff val={h.op_yoy} suffix="%" threshold={20} /></span>
                          </div>
                        </td>
                        <td className="py-2 px-1.5">
                          <div className="flex items-center justify-end gap-1 font-mono">
                            <span className={`w-14 text-right ${typeof h.odp_raw === 'number' && h.odp_raw < 0 ? 'text-emerald-400' : 'text-slate-200'}`}>{h.odp_str || '-'}</span>
                            <span className="w-14 text-left"><SmartDiff val={h.odp_yoy} suffix="%" threshold={20} /></span>
                          </div>
                        </td>
                        <td className="py-2 px-1.5">
                          <div className="flex items-center justify-end gap-1 font-mono">
                            <span className={`w-14 text-right ${typeof h.np_raw === 'number' && h.np_raw < 0 ? 'text-emerald-400' : 'text-slate-200'}`}>{h.np_str || '-'}</span>
                            <span className="w-14 text-left"><SmartDiff val={h.np_yoy} suffix="%" threshold={20} /></span>
                          </div>
                        </td>
                        <td className={`py-2 px-1.5 font-mono ${typeof opMargin === 'number' && opMargin >= 10 ? 'text-rose-400 font-bold' : 'text-slate-400'}`}>
                          {typeof opMargin === 'number' ? `${opMargin.toFixed(1)}%` : '-'}
                        </td>
                        <td className="py-2 px-1.5 font-mono text-slate-500">
                          {typeof h.eps_adjusted === 'number' ? `${h.eps_adjusted.toFixed(1)}円` : '-'}
                        </td>
                        {timeframe === 'annual' && (
                          <td className={`py-2 px-1.5 font-mono ${typeof h.fcf_raw === 'number' && h.fcf_raw < 0 ? 'text-emerald-400' : 'text-slate-200'}`}>
                            {typeof h.fcf_raw === 'number' ? `${(h.fcf_raw / 100000000).toFixed(0)}億円` : '-'}
                          </td>
                        )}
                      </>
                    ) : (
                      <>
                        <td className="py-2 px-1.5">
                          <div className="flex items-center justify-end gap-1 font-mono">
                            <span className="w-14 text-right text-slate-300">
                              {typeof h.out_shares === 'number' ? `${(h.out_shares / 10000).toFixed(0)}万株` : '-'}
                            </span>
                            <span className="w-14 text-left"><SmartDiff val={h.out_shares_yoy} suffix="%" threshold={1} reverseColor /></span>
                          </div>
                        </td>
                        <td className="py-2 px-1.5">
                          <div className="flex items-center justify-end gap-1 font-mono">
                            <span className="w-14 text-right text-slate-400">
                              {typeof h.tr_shares === 'number' ? `${(h.tr_shares / 10000).toFixed(0)}万株` : '-'}
                            </span>
                            <span className="w-14 text-left"><SmartDiff val={h.tr_shares_yoy} suffix="%" threshold={1} /></span>
                          </div>
                        </td>
                        <td className="py-2 px-1.5 font-mono text-blue-400 font-bold">{typeof h.tr_ratio === 'number' ? `${h.tr_ratio.toFixed(2)}%` : '-'}</td>
                        <td className="py-2 px-1.5 font-mono text-slate-200">{typeof h.eps_adjusted === 'number' ? `${h.eps_adjusted.toFixed(1)}円` : '-'}</td>
                        <td className="py-2 px-1.5 font-mono text-slate-500">{typeof h.deps_adjusted === 'number' ? `${h.deps_adjusted.toFixed(1)}円` : '-'}</td>
                        {timeframe === 'annual' && <td className="py-2 px-1.5 font-mono text-white font-medium">{typeof h.roe_raw === 'number' ? `${h.roe_raw.toFixed(1)}%` : '-'}</td>}
                      </>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 8. 大株主 ＆ 政策保有株式 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 shrink-0">
        <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 p-5 rounded-xl shadow-md">
          <h2 className="text-base font-bold text-white mb-3 flex items-center gap-2"><Users className="text-blue-400" size={18} /> 主要株主構成 (上位10名)</h2>
          {majorList.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left whitespace-nowrap">
                <thead className="bg-white/5 text-slate-400 font-medium border-b border-white/10">
                  <tr>
                    <th className="py-2 px-2 text-center">順位</th>
                    <th className="py-2 px-2">株主名</th>
                    <th className="py-2 px-2 text-right">保有比率 <span className="text-[9px] font-normal text-slate-500 ml-1">(増減)</span></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-slate-200">
                  {majorList.slice(0, 10).map((s: any, idx: number) => {
                    const ratio = parseFloat(s.ratio || s.ShsRatio || s.HoldingRatio || 0);
                    return (
                      <tr key={idx} className="hover:bg-white/5 transition-colors">
                        <td className="py-2 px-2 text-center text-slate-500">{s.rank || idx + 1}</td>
                        <td className="py-2 px-2 font-medium truncate max-w-[180px]">{s.name || s.HldrName || s.Name || '不明'}</td>
                        <td className="py-2 px-2">
                          <div className="flex items-center justify-end gap-1 font-mono">
                            <span className="w-12 text-right text-blue-400 font-bold">
                              {typeof ratio === 'number' ? `${ratio.toFixed(2)}%` : '-'}
                            </span>
                            {/* ★変更: 大株主の増減も、0.5%以上動いた時だけ色付け */}
                            <span className="w-14 text-left"><SmartDiff val={s.diff} suffix="pt" digits={2} threshold={0.5} /></span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (<p className="text-xs text-slate-500 py-4 text-center">大株主データがありません</p>)}
        </div>

        <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 p-5 rounded-xl shadow-md">
          <h2 className="text-base font-bold text-white mb-3 flex items-center gap-2"><Shield className="text-purple-400" size={18} /> 政策保有株式の状況 (保有銘柄)</h2>
          <div className="grid grid-cols-2 gap-2 mb-3 bg-white/5 p-2 rounded border border-white/10 text-xs">
            <div><span className="text-slate-400">上場銘柄数: </span><span className="font-bold text-white">{reportCross.ListedIss ?? '-'} 銘柄</span></div>
            <div><span className="text-slate-400">貸借対照表計上額: </span><span className="font-bold text-white">{formatOku(reportCross.ListedBookVal)}</span></div>
          </div>
          {specList.length > 0 ? (
            <div className="overflow-x-auto custom-scrollbar relative">
              <table className="w-full text-left">
                <thead className="bg-white/5 text-slate-400 font-medium border-b border-white/10 sticky top-0 bg-slate-900 text-xs whitespace-nowrap">
                  <tr><th className="py-1.5 px-2">保有先銘柄</th><th className="py-1.5 px-2 text-right">当期BS計上額</th><th className="py-1.5 px-2 text-left">保有目的・理由</th></tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-slate-200">
                  {specList.slice(0, 10).map((item: any, idx: number) => (
                    <tr key={idx} className="hover:bg-white/5 transition-colors group">
                      <td className="py-2 px-2 text-xs font-medium whitespace-nowrap max-w-[140px] truncate">{item.IsrName || '-'}</td>
                      <td className="py-2 px-2 text-xs text-right font-bold text-purple-300 whitespace-nowrap">{formatOku(item.CurBookVal)}</td>
                      <td className="py-2 px-2 align-middle">
                        <ExpandableText text={item.HoldRat || '純投資・事業関係'} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (<p className="text-xs text-slate-500 py-4 text-center">開示データがありません</p>)}
        </div>
      </div>

    </div>
  );
}