// frontend/src/types.ts (または該当の型定義ファイル)

export interface StockDataResponse {
  raw: any;
  analysis: StockAnalysis;
}

export interface StockAnalysis {
  basic: {
    code: string;
    company_name: string;
    industry: string;
    market: string;
  };
  period: {
    current_type: string;
    disclosure_date: string;
  };
  actual: {
    sales?: number | null;
    op?: number | null;
    odp?: number | null;
    net_income?: number | null;
    eps_raw?: number | null;
    eps_adjusted?: number | null;
    fcf?: number | null;
    fcf_margin?: number | null;
    bps?: number | null;
    dps?: number | null;
    cfo?: number | null;
    cfi?: number | null;
    cff?: number | null;
    cash_eq?: number | null;
    cash_change?: number | null;
    out_sh?: number | null;
    tr_sh?: number | null;
    avg_sh?: number | null;
    deps_raw?: number | null;
    div_total_ann?: number | null; // ★ここが追加される
  };
  forecast: Record<string, any>;
  growth: {
    sales_yoy?: number | null;
    op_yoy?: number | null;
    eps_yoy?: number | null;
    np_yoy?: number | null;
    sales_cagr_3y?: number | null;
    op_cagr_3y?: number | null;
    eps_cagr_3y?: number | null;
    progress_op?: number | null;
    avg_eps_yoy_3y?: number | null;
  };
  profitability: {
    op_margin?: number | null;
    op_margin_change?: number | null;
    avg_op_margin_3y?: number | null;
    roe?: number | null;
    roa_estimate?: number | null;
    op_to_equity?: number | null;
    equity_ratio?: number | null;
    payout_ratio?: number | null;
    cfo_to_np?: number | null;
    treasury_ratio?: number | null;
    dilution_rate?: number | null;
    eps_growth_factors?: {
      eps_yoy: number | null;
      np_yoy: number | null;
      share_yoy: number | null;
      share_effect: number | null;
    } | null;
    dupont?: {
      current: { npm: number; at: number; fl: number; roe: number; } | null;
      prev: { npm: number; at: number; fl: number; roe: number; } | null;
    };
  };
  quality?: {
    cfo_yoy?: number | null;
    working_capital_change?: number | null;
    capex?: number | null;
    depreciation?: number | null;
  };
  momentum?: {
    ret_20d?: number | null;
    ret_25d?: number | null;
    ret_60d?: number | null;
    ret_75d?: number | null;
    ret_120d?: number | null;
    ret_200d?: number | null;
    ret_250d?: number | null;
    ma20_diff?: number | null;
    ma25_diff?: number | null;
    ma60_diff?: number | null;
    ma75_diff?: number | null;
    avg_val_20d?: number | null;
    avg_val_25d?: number | null;
    vol_spike?: number | null;
    dist_high?: number | null;
    dist_low?: number | null;
    short_interest_change?: number | null;
  };
  health?: {
    roic?: number | null;
    net_cash?: number | null;
    debt_ebitda?: number | null;
    icr?: number | null;
  };
  valuation: {
    market_cap?: number | null;
    forward_per?: number | null;
    pbr?: number | null;
    peg?: number | null;
    dividend_yield?: number | null;
    per_avg?: number | null;
    per_median?: number | null;
    pbr_avg?: number | null;
    pbr_median?: number | null;
  };
  market_perf: {
    stock_1y?: number | null;
    topix_1y?: number | null;
    sector_1y?: number | null;
    margin_buy?: number | null;
    margin_ratio?: number | null;
  };
  history: HistoryData[];
  quarterly_history: HistoryData[];
  price_margin_history: PriceMarginData[];
  major_shareholders?: Array<{
    rank: number;
    name: string;
    ratio: number | null;
    diff: number | null;
  }>;
  large_volume?: any[];
  cross_shareholdings?: any;
  events?: {
    revisions: Array<{
      date: string;
      fy: string;
      prev_fop: number;
      new_fop: number;
      diff_pct: number;
      is_up: boolean;
      timing: string;
    }>;
    other: Array<{
      date: string;
      type: string;
      title: string;
      desc: string;
    }>;
    earnings?: Array<{
      date: string;
      title: string;
      sales_str: string;
      sales_yoy: number | null;
      op_str: string;
      op_yoy: number | null;
    }>;
  };
  guidance_history?: Array<{
    fy: string;
    initial_sales: number | null;
    final_sales: number | null;
    initial_op: number | null;
    final_op: number | null;
    sales_achieve: number | null;
    op_achieve: number | null;
    sales_up: string[];
    sales_down: string[];
    op_up: string[];
    op_down: string[];
  }>;
}

export interface HistoryData {
  year: string;
  sales_str: string;
  sales_raw: number | null;
  sales_yoy: number | null;
  op_str: string;
  op_raw: number | null;
  op_yoy: number | null;
  odp_str?: string;
  odp_raw?: number | null;
  odp_yoy?: number | null;
  np_str?: string;
  np_raw?: number | null;
  np_yoy?: number | null;
  op_margin: number | null;
  eps_raw: number | null;
  eps_adjusted: number | null;
  deps_adjusted?: number | null;
  eps_yoy: number | null;
  roe_raw: number | null;
  fcf_raw: number | null;
  fcf_margin: number | null;
  out_shares?: number | null;
  tr_shares?: number | null;
  tr_ratio?: number | null;
  out_shares_yoy?: number | null;
  tr_shares_yoy?: number | null;
  calc_per?: number | null;
  calc_pbr?: number | null;
  payout_ratio_ann?: number | null; 
  div_total_ann?: number | null;
}

export interface PriceMarginData {
  date: string;
  open?: number | null;
  high?: number | null;
  low?: number | null;
  close: number | null;
  volume: number | null;
  margin_buy: number | null;
  margin_sell: number | null;
  per?: number | null;
  pbr?: number | null;
  market_cap?: number | null;
  eps?: number | null;
  topix?: number | null;
  sector?: number | null;
}