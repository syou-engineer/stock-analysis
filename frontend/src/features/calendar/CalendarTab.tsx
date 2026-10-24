import React, { useState, useEffect, useMemo } from 'react';
import { Calendar, ChevronLeft, ChevronRight, ArrowUpDown, ArrowUp, ArrowDown, Zap } from 'lucide-react';
import { formatDate, formatPct, formatMarketCap } from '../../utils/formatters';
import Holidays from 'date-holidays';


const japaneseHolidays = new Holidays('JP');

const toDateString = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  return `${year}-${month}-${day}`;
};

const isBusinessDay = (date: Date): boolean => {
  const day = date.getDay();

  // 土曜日・日曜日を除外
  if (day === 0 || day === 6) {
    return false;
  }

  // 日本の祝日・振替休日・国民の休日を除外
  return !japaneseHolidays.isHoliday(date);
};

// 指定日が休業日なら、直前の営業日へ移動
const normalizeBusinessDate = (date: Date): Date => {
  const result = new Date(date);
  result.setHours(12, 0, 0, 0);

  while (!isBusinessDay(result)) {
    result.setDate(result.getDate() - 1);
  }

  return result;
};

// 前後の営業日へ移動
const shiftBusinessDate = (
  date: Date,
  offset: number,
): Date => {
  const result = new Date(date);
  const direction = offset >= 0 ? 1 : -1;

  for (let i = 0; i < Math.abs(offset); ) {
    result.setDate(result.getDate() + direction);

    if (isBusinessDay(result)) {
      i++;
    }
  }

  return result;
};


interface EarningsItem {
  code: string;
  name: string;
  period_type: string;
  industry?: string | null;
  prior_year_revision?: string;
  prior_year_revision_metric?: string | null;
  prior_year_revision_previous?: number | null;
  prior_year_revision_current?: number | null;
  industry_33?: string;
  industry_17?: string;
  market_cap?: number;
  sales_yoy?: number;
  op_yoy?: number;
  sales_yoy_change?: number;
  op_margin?: number;
  op_margin_change?: number;
  progress_rate?: number;
  progress_diff?: number;
  flag_growth_accel?: boolean;
  flag_margin_imp?: boolean;
  flag_turnaround?: boolean;
  flag_rapid_recover?: boolean;
}

interface Props {
  onSelectStock?: (code: string) => void;
}

type SortKey = 'sales_yoy' | 'sales_yoy_change' | 'op_margin' | 'op_margin_change' | 'progress_rate' | 'progress_diff' | 'market_cap';
type SortDirection = 'asc' | 'desc';

// 表示用の銘柄コード。
// 5桁かつ末尾が0の従来形式だけ4桁に変換する。
// API通信や銘柄選択には元のコードを使う。
const formatStockCode = (code: string) =>
  /^\d{4}0$/.test(code) ? code.slice(0, 4) : code;

const getIndustry = (item: EarningsItem): string | undefined => {
  return item.industry || item.industry_33 || item.industry_17;
};

const getRevisionLabel = (
  revision?: EarningsItem['prior_year_revision'],
): string => {
  switch (revision) {
    case 'up':
      return '上方修正';
    case 'down':
      return '下方修正';
    case 'unchanged':
      return '据え置き';
    default:
      return '判定不可';
  }
};

export function CalendarTab({ onSelectStock }: Props) {
const [selectedDate, setSelectedDate] = useState<string>(() =>
  toDateString(normalizeBusinessDate(new Date()))
);
const [minMarketCap, setMinMarketCap] = useState('100');
const [items, setItems] = useState<EarningsItem[]>([]);
const [isLoading, setIsLoading] = useState(false);

const [sortConfig, setSortConfig] = useState<{
  key: SortKey;
  direction: SortDirection;
}>({
  key: 'progress_diff',
  direction: 'desc',
});

const dateOptions = useMemo(() => {
  const base = normalizeBusinessDate(
    new Date(`${selectedDate}T12:00:00`)
  );

  return Array.from({ length: 7 }, (_, index) =>
    shiftBusinessDate(base, index - 3)
  );
}, [selectedDate]);

 const [error, setError] = useState<string | null>(null);

useEffect(() => {
  const controller = new AbortController();

  const loadEarnings = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch(
        `http://localhost:8000/api/calendar/earnings?date=${selectedDate}`,
        { signal: controller.signal }
      );

      if (!res.ok) {
        throw new Error(`決算データの取得に失敗しました (${res.status})`);
      }

      const data = await res.json();
      setItems(data.items ?? []);
    } catch (e) {
      if (e instanceof Error && e.name === 'AbortError') return;

      console.error(e);
      setItems([]);
      setError('決算データを取得できませんでした。再度お試しください。');
    } finally {
      if (!controller.signal.aborted) {
        setIsLoading(false);
      }
    }
  };

  loadEarnings();

  return () => controller.abort();
}, [selectedDate]);

  const shiftDate = (days: number) => {
  const current = normalizeBusinessDate(
    new Date(`${selectedDate}T12:00:00`)
  );

  setSelectedDate(
    toDateString(shiftBusinessDate(current, days))
  );
};

const handleDateChange = (value: string) => {
  if (!value) return;

  const selected = normalizeBusinessDate(
    new Date(`${value}T12:00:00`)
  );

  setSelectedDate(toDateString(selected));
};

  const requestSort = (key: SortKey) => {
    let direction: SortDirection = 'desc';
    if (sortConfig.key === key && sortConfig.direction === 'desc') direction = 'asc';
    setSortConfig({ key, direction });
  };

  const filteredItems = useMemo(() => {
    const input = minMarketCap.trim();
    const min = Number(input);

    // 空欄・無効な入力・0以下の場合は、全件表示（時価総額不明も含む）
    if (input === '' || !Number.isFinite(min) || min <= 0) {
      return items;
    }

    const minMarketCapMillionYen = min * 100;

    return items.filter((item) => {
      // 時価総額が不明(null/undefined)な銘柄は、フィルタで消さずに念のため表示させる
      if (item.market_cap == null || !Number.isFinite(item.market_cap)) {
        return true; 
      }
      return item.market_cap >= minMarketCapMillionYen;
    });
  }, [items, minMarketCap]);
//   const filteredItems = useMemo(() => {
//   const input = minMarketCap.trim();
//   const min = Number(input);

//   // 空欄・無効な入力では、時価総額が取得できている銘柄を表示
//   if (input === '' || !Number.isFinite(min)) {
//     return items.filter((item) => item.market_cap != null);
//   }

//   // 0以下なら、時価総額が取得できている銘柄をすべて表示
//   if (min <= 0) {
//     return items.filter((item) => item.market_cap != null);
//   }

//   // market_cap は百万円単位
//   // 100億円 = 10,000百万円
//   const minMarketCapMillionYen = min * 100;

//   return items.filter(
//     (item) =>
//       item.market_cap != null &&
//       Number.isFinite(item.market_cap) &&
//       item.market_cap >= minMarketCapMillionYen
//   );
// }, [items, minMarketCap]);
  
const sortedItems = useMemo(() => {
   return [...filteredItems].sort((a, b) => {
    const aValue = a[sortConfig.key];
    const bValue = b[sortConfig.key];

    // 欠損値は昇順・降順のどちらでも最後
    const aMissing = aValue == null || !Number.isFinite(aValue);
    const bMissing = bValue == null || !Number.isFinite(bValue);

    if (aMissing && bMissing) return 0;
    if (aMissing) return 1;
    if (bMissing) return -1;

    if (aValue < bValue) {
      return sortConfig.direction === 'asc' ? -1 : 1;
    }
    if (aValue > bValue) {
      return sortConfig.direction === 'asc' ? 1 : -1;
    }
    return 0;
  });
}, [filteredItems, sortConfig]);

  const SortIcon = ({ sortKey }: { sortKey: SortKey }) => {
    if (sortConfig.key !== sortKey) return <ArrowUpDown size={12} className="inline ml-1 text-slate-600" />;
    return sortConfig.direction === 'asc' ? <ArrowUp size={12} className="inline ml-1 text-blue-400" /> : <ArrowDown size={12} className="inline ml-1 text-blue-400" />;
  };

const formatSignedPct = (val?: number) => {
  if (val == null || !Number.isFinite(val)) return '-';

  const formatted = formatPct(val);
  return val > 0 && !formatted.startsWith('+')
    ? `+${formatted}`
    : formatted;
};

const getChangeColor = (val?: number | null) => {
  if (val == null || !Number.isFinite(val)) return 'text-slate-500';
  if (val > 0) return 'text-rose-400 font-bold';
  if (val < 0) return 'text-emerald-400 font-bold';
  return 'text-slate-300';
};

const formatPt = (val?: number) => {
  if (val == null || !Number.isFinite(val)) return '-';
  const sign = val > 0 ? '+' : '';
  return `${sign}${val.toFixed(1)}pt`;
};

  return (
    <div className="flex flex-col h-full bg-slate-950 p-4">
      {/* Header Controls */}
      <div className="flex items-center justify-between bg-slate-900 border border-slate-700 rounded-lg p-3 mb-4 shadow-lg shrink-0">
        <div className="flex items-center gap-2 text-amber-400 font-bold">
          <Zap size={20} />
          <h2>決算モメンタムレーダー</h2>
        </div>
        <div className="flex items-center gap-2 ml-4">
  <label
    htmlFor="min-market-cap"
    className="text-xs text-slate-400 whitespace-nowrap"
  >
    時価総額
  </label>

  <input
    id="min-market-cap"
    type="number"
    min="0"
    step="10"
    value={minMarketCap}
    onChange={(e) => setMinMarketCap(e.target.value)}
    className="w-24 bg-slate-800 border border-slate-700 text-white text-xs rounded px-2 py-1.5"
  />

  <span className="text-xs text-slate-400 whitespace-nowrap">
    億円以上
  </span>
</div>
        
        <div className="flex items-center gap-2">
          <button onClick={() => shiftDate(-1)} className="p-1 hover:bg-slate-800 rounded text-slate-400"><ChevronLeft size={20}/></button>
          <div className="flex gap-1">
            {dateOptions.map((d, i) => {
              const dStr = formatDate(d);
              return (
          <button key={i} onClick={() => handleDateChange(dStr)}
                  className={`flex flex-col items-center justify-center w-12 h-12 rounded-md transition-all ${
                    dStr === selectedDate ? 'bg-blue-600 text-white font-bold scale-110 z-10' : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  <span className="text-[9px] uppercase">{['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][d.getDay()]}</span>
                  <span className="text-sm">{d.getDate()}</span>
                </button>
              );
            })}
          </div>
          <button onClick={() => shiftDate(1)} className="p-1 hover:bg-slate-800 rounded text-slate-400"><ChevronRight size={20}/></button>
          <input type="date" value={selectedDate} onChange={(e) => handleDateChange(e.target.value)} className="ml-4 bg-slate-800 border border-slate-700 text-white text-xs rounded px-2 py-1.5" />
        </div>
      </div>

      {/* Main Table */}
      <div className="flex-1 bg-slate-900 border border-slate-700 rounded-lg overflow-hidden flex flex-col shadow-xl min-h-0">
        <div className="flex-1 overflow-auto custom-scrollbar relative">
            {isLoading ? (
                <div className="p-8 text-center text-slate-400 animate-pulse text-sm">解析中...</div>
            ) : error ? (
              <div className="flex flex-col items-center justify-center h-full text-slate-500 p-8">
                <Calendar size={48} className="mb-4 opacity-20" />
                <p>{error}</p>
              </div>
            ) : items.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 p-8">
              <Calendar size={48} className="mb-4 opacity-20" />
              <p>この日の決算発表予定はありません</p>
            </div>
          ) : (
            <table className="w-full text-left border-collapse text-xs">
              <thead className="bg-slate-950/90 sticky top-0 z-10 backdrop-blur-sm border-b border-slate-700 shadow-sm cursor-pointer select-none">
                <tr className="text-slate-400">
                  <th className="py-3 px-4 font-normal">銘柄</th>
                  <th className="py-3 px-4 font-normal text-right">変化タイプ</th>
                  <th className="py-3 px-4 font-normal text-right hover:text-white" onClick={() => requestSort('sales_yoy')}>
                    <div className="flex flex-col items-end">
                      <span>直近Q 売上YoY <SortIcon sortKey="sales_yoy" /></span>
                      <span className="text-[10px] text-slate-500 font-normal">営利YoY</span>
                    </div>
                  </th>
                  <th className="py-3 px-4 font-normal text-right hover:text-white" onClick={() => requestSort('sales_yoy_change')}>
                    <div className="flex flex-col items-end">
                      <span className="text-orange-400">成長加速幅 <SortIcon sortKey="sales_yoy_change" /></span>
                      <span className="text-[10px] text-slate-500 font-normal">(前Q比 pt)</span>
                    </div>
                  </th>
                  <th className="py-3 px-4 font-normal text-right hover:text-white" onClick={() => requestSort('op_margin')}>
                    <div className="flex flex-col items-end">
                      <span>直近Q 利益率 <SortIcon sortKey="op_margin" /></span>
                      <span className="text-[10px] text-slate-500 font-normal hover:text-emerald-400" onClick={(e) => { e.stopPropagation(); requestSort('op_margin_change'); }}>
                        改善幅(YoY pt) <SortIcon sortKey="op_margin_change" />
                      </span>
                    </div>
                  </th>
                  <th className="py-3 px-4 font-normal text-right hover:text-white" onClick={() => requestSort('progress_rate')}>
                    <div className="flex flex-col items-end">
                      <span>通期進捗率 <SortIcon sortKey="progress_rate" /></span>
                      <span className="text-[10px] text-slate-500 font-normal hover:text-amber-400" onClick={(e) => { e.stopPropagation(); requestSort('progress_diff'); }}>
                        過去平均差(pt) <SortIcon sortKey="progress_diff" />
                      </span>
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {sortedItems.map((item) => (
                  <tr key={item.code} className="hover:bg-slate-800/80 transition-colors cursor-pointer" onClick={() => onSelectStock && onSelectStock(item.code)}>
                    <td className="py-3 px-4 min-w-[220px]">
  <div className="flex items-center gap-2">
    <span className="font-mono text-blue-300 text-xs font-bold shrink-0">
      {formatStockCode(item.code)}
    </span>

    <span
      className="text-slate-100 text-sm font-semibold truncate max-w-[180px]"
      title={item.name}
    >
      {item.name}
    </span>
  </div>

  <div className="flex items-center gap-2 mt-1.5 flex-wrap">
    <span className="inline-flex rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-medium text-slate-200">
      {item.period_type || '-'}
    </span>

    {getIndustry(item) && (
      <span className="text-[10px] text-cyan-300">
        {getIndustry(item)}
      </span>
    )}
  </div>

  <div className="text-[11px] text-slate-300 mt-1">
    時価総額：
    <span className="font-mono font-semibold text-slate-100">
      {formatMarketCap(item.market_cap)}
    </span>
  </div>
</td>
                    
                    <td className="py-3 px-4 text-right">
                      <div className="flex flex-col items-end gap-1">
                        {item.flag_growth_accel && <span className="bg-orange-500/20 text-orange-400 text-[10px] px-1.5 py-0.5 rounded border border-orange-500/30">成長加速🔥</span>}
                        {item.prior_year_revision && (
  <span
    className={`text-[10px] px-1.5 py-0.5 rounded border ${
  item.prior_year_revision === 'up'
    ? 'bg-rose-500/15 text-rose-300 border-rose-500/30'
    : item.prior_year_revision === 'down'
      ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
      : item.prior_year_revision === 'unchanged'
        ? 'bg-slate-700/60 text-slate-300 border-slate-600'
        : 'bg-slate-800 text-slate-400 border-slate-700'
}`}
  >
    前年同期：{getRevisionLabel(item.prior_year_revision)}
  </span>
)}
                        {item.flag_margin_imp && <span className="bg-emerald-500/20 text-emerald-400 text-[10px] px-1.5 py-0.5 rounded border border-emerald-500/30">利益率改善📈</span>}
                        {item.flag_turnaround && <span className="bg-purple-500/20 text-purple-400 text-[10px] px-1.5 py-0.5 rounded border border-purple-500/30">黒字転換✨</span>}
                        {item.flag_rapid_recover && <span className="bg-blue-500/20 text-blue-400 text-[10px] px-1.5 py-0.5 rounded border border-blue-500/30">急回復🚀</span>}
                      </div>
                    </td>

                    <td className="py-3 px-4 text-right font-mono font-bold">
                      <div className={getChangeColor(item.sales_yoy)}>
  {formatSignedPct(item.sales_yoy)}
</div>
<div className={`text-[10px] font-normal ${getChangeColor(item.op_yoy)}`}>
  {formatSignedPct(item.op_yoy)}
</div>
                    </td>

                    <td className="py-3 px-4 text-right font-mono">
  <span
    className={`px-2 py-0.5 rounded ${
      item.sales_yoy_change != null && item.sales_yoy_change !== 0
        ? `${getChangeColor(item.sales_yoy_change)} ${
            item.sales_yoy_change > 0
              ? 'bg-rose-500/10'
              : 'bg-emerald-500/10'
          }`
        : 'text-slate-500'
    }`}
  >
    {formatPt(item.sales_yoy_change)}
  </span>
</td>

                    <td className="py-3 px-4 text-right font-mono">
                    <div className="text-white font-bold">
                      {item.op_margin != null
                        ? `${item.op_margin.toFixed(1)}%`
                        : '-'}
                    </div>
                      <div className={`text-[10px] ${getChangeColor(item.op_margin_change)}`}>
  {formatPt(item.op_margin_change)}
</div>
                    </td>

                    <td className="py-3 px-4 text-right font-mono">
                      <div className="text-white font-bold">
                          {item.progress_rate != null
                            ? `${item.progress_rate.toFixed(1)}%`
                            : '-'}
                        </div>
                      <div className={`text-[10px] ${getChangeColor(item.progress_diff)}`}>
  {item.progress_diff != null && item.progress_diff > 0
    ? '▲ '
    : item.progress_diff != null && item.progress_diff < 0
      ? '▼ '
      : ''}
  {formatPt(item.progress_diff)}
</div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}