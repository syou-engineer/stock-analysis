// frontend/src/utils/formatters.ts

export const formatVal = (val: number | null | undefined, suffix: string = '', digits: number = 1): string => {
  if (val === null || val === undefined) return '-';
  return `${val > 0 ? '+' : ''}${val.toFixed(digits)}${suffix}`;
};

export const formatOku = (val: number | null | undefined): string => {
  if (val === null || val === undefined) return '-';
  const oku = val / 100_000_000;
  
  if (Math.abs(oku) < 1) {
    return `${(val / 1_000_000).toLocaleString(undefined, { maximumFractionDigits: 0 })} 百万円`;
  }
  if (Math.abs(oku) >= 10000) {
    return `${(oku / 10000).toFixed(1)} 兆円`;
  }
  return `${oku.toLocaleString(undefined, { maximumFractionDigits: 1 })} 億円`;
};

// export const formatMarketCap = (val: number | null | undefined): string => {
//   if (val === null || val === undefined) return '-';
//   return formatOku(val * 1_000_000); 
// };

// export const formatPct = (val: number | null | undefined): string => {
//   if (val === null || val === undefined) return '-';
//   const formatted = val.toFixed(1);
//   return val > 0 ? `+${formatted}%` : `${formatted}%`;
// };

// export const formatDate = (date: Date): string => {
//   const y = date.getFullYear();
//   const m = String(date.getMonth() + 1).padStart(2, '0');
//   const d = String(date.getDate()).padStart(2, '0');
//   return `${y}-${m}-${d}`;
// };


// frontend/src/utils/formatters.ts

/**
 * 証券コードをプロジェクト標準の4桁文字列に統一する
 */
export const normalizeCode = (code: string | number | undefined | null): string => {
  if (code == null) return '';
  const strCode = String(code).trim();
  return strCode.length >= 4 ? strCode.slice(0, 4) : strCode;
};

/**
 * 日付を YYYY-MM-DD 形式にフォーマットする
 */
export const formatDate = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

/**
 * パーセンテージを小数点第1位の文字列にフォーマットする
 */
export const formatPct = (val?: number | null): string => {
  if (val == null || !Number.isFinite(val)) return '-';
  return `${val.toFixed(1)}%`;
};

/**
 * 金額（百万円単位を想定）を億円・兆円表記にフォーマットする
 */
export const formatMarketCap = (val?: number | null): string => {
  if (val == null || !Number.isFinite(val)) return '-';
  
  // DBやAPIの単位に応じて調整（ここでは百万円が入力される想定で 100=1億円 とする）
  const oku = val / 100;
  if (Math.abs(oku) >= 10000) {
    return `${(oku / 10000).toFixed(1)}兆円`;
  }
  return `${Math.round(oku).toLocaleString()}億円`;
};