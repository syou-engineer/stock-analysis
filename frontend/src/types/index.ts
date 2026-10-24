// export interface StockDataResponse {
//   raw: any;
//   analysis: StockAnalysis;
// }

// export interface StockAnalysis {
//   basic: {
//     code: string;
//     company_name: string;
//     industry: string;
//     market: string;
//   };
//   period: {
//     current_type: string;
//     disclosure_date: string;
//   };
//   actual: {
//     sales?: number | null;
//     op?: number | null;
//     net_income?: number | null;
//     eps_raw?: number | null;
//     eps_adjusted?: number | null;
//     fcf?: number | null;
//     bps?: number | null;
//     dps?: number | null;
//     cfo?: number | null;
//     cfi?: number | null;
//     cff?: number | null;
//     cash_eq?: number | null;
//     cash_change?: number | null;
//   };
//   forecast: Record<string, any>;
//   growth: {
//     sales_yoy?: number | null;
//     op_yoy?: number | null;
//     eps_yoy?: number | null;
//     sales_cagr_3y?: number | null;
//     op_cagr_3y?: number | null;   // ★追加
//     eps_cagr_3y?: number | null;  // ★追加
//     progress_op?: number | null;
//     avg_eps_yoy_3y?: number | null;
//   };
//   profitability: {
//     op_margin?: number | null;
//     op_margin_change?: number | null;
//     roe?: number | null;
//     roa_estimate?: number | null;
//     equity_ratio?: number | null;
//     payout_ratio?: number | null;
//     cfo_to_np?: number | null;
//     treasury_ratio?: number | null;
//     dilution_rate?: number | null;
//     avg_op_margin_3y?: number | null;
//     eps_growth_factors?: {
//       eps_yoy: number | null;
//       np_yoy: number | null;
//       share_yoy: number | null;
//       share_effect: number | null;
//     } | null;
//     dupont?: {
//       current: { npm: number; at: number; fl: number; roe: number; } | null;
//       prev: { npm: number; at: number; fl: number; roe: number; } | null;
//     };
//   };
//   valuation: Record<string, any>;
//   market_perf: {
//     stock_1y?: number | null;
//     topix_1y?: number | null;
//   };
//   history: HistoryData[];
//   quarterly_history: HistoryData[];
//   price_margin_history: PriceMarginData[];
//   major_shareholders?: Array<{
//     rank: number;
//     name: string;
//     ratio: number | null;
//     diff: number | null;
//   }>;
//   large_volume?: any[];
//   cross_shareholdings?: any;
//   events?: {
//     revisions: Array<{
//       date: string;
//       fy: string;
//       prev_fop: number;
//       new_fop: number;
//       diff_pct: number;
//       is_up: boolean;
//       timing: string;
//     }>;
//     other: Array<{
//       date: string;
//       type: string;
//       title: string;
//       desc: string;
//     }>;
//     earnings?: Array<{  // ★追加
//       date: string;
//       title: string;
//       sales_str: string;
//       sales_yoy: number | null;
//       op_str: string;
//       op_yoy: number | null;
//     }>;
//   };
  
//   guidance_history?: Array<{
//     fy: string;
//     initial_sales: number | null;
//     final_sales: number | null;
//     initial_op: number | null;
//     final_op: number | null;
//     sales_achieve: number | null;
//     op_achieve: number | null;
//     sales_up: string[];
//     sales_down: string[];
//     op_up: string[];
//     op_down: string[];
//   }>;
// }

// export interface HistoryData {
//   year: string;
//   sales_str: string;
//   sales_raw: number | null;
//   sales_yoy: number | null;
//   op_str: string;
//   op_raw: number | null;
//   op_yoy: number | null;
//   odp_str?: string;
//   odp_raw?: number | null;
//   odp_yoy?: number | null;
//   np_str?: string;
//   np_raw?: number | null;
//   np_yoy?: number | null;
//   op_margin: number | null;
//   eps_raw: number | null;
//   eps_adjusted: number | null;
//   deps_adjusted?: number | null;
//   eps_yoy: number | null;
//   roe_raw: number | null;
//   fcf_raw: number | null;
//   fcf_margin: number | null;
//   out_shares?: number | null;
//   tr_shares?: number | null;
//   tr_ratio?: number | null;
//   out_shares_yoy?: number | null;
//   tr_shares_yoy?: number | null;
// }

// export interface PriceMarginData {
//   date: string;
//   open?: number | null;
//   high?: number | null;
//   low?: number | null;
//   close: number | null;
//   volume: number | null;
//   margin_buy: number | null;
//   margin_sell: number | null;
//   per?: number | null;
//   pbr?: number | null;
//   market_cap?: number | null;
//   eps?: number | null;
//   topix?: number | null;
// }

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
    net_income?: number | null;
    eps_raw?: number | null;
    eps_adjusted?: number | null;
    fcf?: number | null;
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
  };
  forecast: Record<string, any>;
  growth: {
    sales_yoy?: number | null;
    op_yoy?: number | null;
    eps_yoy?: number | null;
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
  valuation: Record<string, any>;
  market_perf: {
    stock_1y?: number | null;
    topix_1y?: number | null;
    sector_1y?: number | null;
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