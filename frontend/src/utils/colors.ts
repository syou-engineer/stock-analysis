export const CHART_COLORS = {
  // 業績 (Fundamentals)
  sales: '#3b82f688',     // 淡いブルー
  op: '#10b981',          // エメラルド
  eps: '#f43f5e',         // ローズ
  
  // 市場・需給 (Market & Supply/Demand)
  price: '#fbbf24',       // アンバー/ゴールド (株価)
  marginBuy: '#8b5cf6',   // パープル (信用買い残)
  marginSell: '#0ea5e9',  // スカイブルー (信用売り残)
  
  // 共通設定
  text: '#64748b',        // 軸テキスト
  grid: '#1e293b',        // グリッド線
  tooltipBg: '#0f172a',
  tooltipBorder: '#1e293b',
  tooltipText: '#f8fafc',
};

export const UI_COLORS = {
  // バッジやテキストのステータスカラー (Tailwindクラス群)
  positive: 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/20',
  negative: 'text-rose-400 bg-rose-500/10 border border-rose-500/20',
  warning: 'text-amber-400 bg-amber-500/10 border border-amber-500/20',
  neutral: 'text-slate-300 bg-white/5 border border-white/10',
};