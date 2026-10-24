import React from 'react';
import type { StockAnalysis } from '../../types';
import { Users, TrendingUp, TrendingDown, AlertCircle, Clock, ChevronRight, ArrowRight } from 'lucide-react';

interface Props {
  analysis: StockAnalysis;
}

// 数値変換ヘルパー
const toNumber = (val: any): number => {
  if (val === null || val === undefined) return 0;
  const parsed = parseFloat(val);
  return isNaN(parsed) ? 0 : parsed;
};

export function ShareholdersTab({ analysis }: Props) {
  const majorRaw = analysis.major_shareholders || {};
  const largeVolumeRaw = Array.isArray(analysis.large_volume) ? analysis.large_volume : [];

  // ==========================================
  // 大株主データの正規化 (J-Quants V2仕様: Hldrs配列)
  // ==========================================
  let majorList: any[] = [];
  if (Array.isArray(majorRaw.Hldrs)) {
    majorList = majorRaw.Hldrs;
  } else if (Array.isArray(majorRaw.MajorShareholders)) {
    majorList = majorRaw.MajorShareholders;
  } else if (Array.isArray(majorRaw.Shareholders)) {
    majorList = majorRaw.Shareholders;
  } else if (typeof majorRaw === 'string') {
    try {
      const parsed = JSON.parse(majorRaw);
      majorList = parsed.Hldrs || parsed.MajorShareholders || parsed.Shareholders || [];
    } catch (e) {
      majorList = [];
    }
  }

  // ==========================================
  // 大量保有報告書の正規化 (J-Quants V2仕様)
  // ==========================================
  // 1つの書類(Doc)の中に複数の提出者(Hldrs)がいる場合があるのでフラットに展開する
  const timelineEvents: any[] = [];
  largeVolumeRaw.forEach((doc: any) => {
    // 書類全体としての合計比率（単独提出ならこれを使う）
    const totalCurrent = toNumber(doc.TotalShsRatio) * 100; // APIは小数(0.05=5%)で返すので100倍
    const totalPrev = toNumber(doc.TotalShsRatioLast) * 100;
    const submitDate = doc.SubDate || doc.SubmitDate || '-';
    
    // Hldrs配列(共同保有者などのリスト)がある場合はそれぞれをイベントとして展開
    if (Array.isArray(doc.Hldrs) && doc.Hldrs.length > 0) {
      doc.Hldrs.forEach((hldr: any) => {
        const curRatio = toNumber(hldr.ShsRatio) * 100;
        const prevRatio = toNumber(hldr.ShsRatioLast) * 100;
        
        // わずかな変動（0.00%）はノイズになるためスキップするかどうかはお好みで
        timelineEvents.push({
          submitDate: submitDate,
          name: hldr.HldrName || hldr.Name || '不明な提出者',
          currentRatio: curRatio,
          previousRatio: prevRatio,
          purpose: hldr.HldgPurp || '目的記載なし',
          docTitle: doc.DocTitle || '大量保有報告関連'
        });
      });
    } else {
      // Hldrsがない(あるいはパース失敗)場合は書類全体の数値を採用
      timelineEvents.push({
        submitDate: submitDate,
        name: doc.FilerName || doc.SubmitterName || '不明な提出者',
        currentRatio: totalCurrent,
        previousRatio: totalPrev,
        purpose: '目的記載なし',
        docTitle: doc.DocTitle || '大量保有報告関連'
      });
    }
  });

  // タイムラインを日付の降順（新しい順）にソート
  timelineEvents.sort((a, b) => (a.submitDate < b.submitDate ? 1 : -1));

  // イベント判定ロジック
  const analyzeEvent = (current: number, prev: number) => {
    const diff = current - prev;
    
    if (prev === 0 && current >= 5) {
      return { type: 'NEW', label: '5%超え (新規)', color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20', icon: <AlertCircle size={14} /> };
    }
    if (current < 5 && prev >= 5) {
      return { type: 'EXIT', label: '5%未満 (消失)', color: 'text-slate-400', bg: 'bg-slate-500/10', border: 'border-slate-500/20', icon: <ChevronRight size={14} /> };
    }
    if (diff > 0.01) { // 0.01%以上の増加
      return { type: 'INCREASE', label: '保有割合 増加', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', icon: <TrendingUp size={14} /> };
    }
    if (diff < -0.01) { // 0.01%以上の減少
      return { type: 'DECREASE', label: '保有割合 減少', color: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/20', icon: <TrendingDown size={14} /> };
    }
    return { type: 'MAINTAIN', label: '変動なし', color: 'text-slate-400', bg: 'bg-slate-800', border: 'border-white/10', icon: <ChevronRight size={14} /> };
  };

  return (
    <div className="space-y-4 animate-in fade-in duration-500">
      
      {/* タイムライン (大量保有報告書) */}
      <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 p-5 rounded-xl shadow-md">
        <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
          <Clock className="text-blue-400" size={18} />
          株主・資本移動イベント (大量保有報告)
        </h2>
        
        {timelineEvents.length > 0 ? (
          <div className="space-y-4 relative before:absolute before:inset-0 before:ml-4 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-700 before:to-transparent">
            {timelineEvents.map((eventData, idx) => {
              const diff = eventData.currentRatio - eventData.previousRatio;
              const event = analyzeEvent(eventData.currentRatio, eventData.previousRatio);
              
              return (
                <div key={idx} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full border-4 border-slate-900 bg-slate-800 text-slate-400 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                    {event.icon}
                  </div>
                  <div className="w-[calc(100%-3rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-white/5 bg-slate-800/50 hover:bg-slate-800 transition-colors shadow-sm">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-slate-400 font-mono">{eventData.submitDate}</span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${event.bg} ${event.color} ${event.border}`}>
                        {event.label}
                      </span>
                    </div>
                    <p className="text-sm font-bold text-white mb-1 line-clamp-1">{eventData.name}</p>
                    <p className="text-[10px] text-slate-500 mb-2 truncate">{eventData.docTitle} / {eventData.purpose}</p>
                    
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-slate-400">
                        {eventData.previousRatio !== 0 ? `${eventData.previousRatio.toFixed(2)}%` : '0.00%'}
                      </span>
                      <ArrowRight size={14} className="text-slate-500" />
                      <span className="text-white font-bold">{eventData.currentRatio.toFixed(2)}%</span>
                      {Math.abs(diff) > 0.001 && (
                        <span className={`text-xs ml-2 ${diff > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          ({diff > 0 ? '+' : ''}{diff.toFixed(2)}pt)
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-slate-400 text-center py-6">直近の大量保有報告書はありません</p>
        )}
      </div>

      {/* 大株主一覧 */}
      <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 p-5 rounded-xl shadow-md overflow-x-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Users className="text-emerald-400" size={18} />
            主要株主構成 (上位10名)
          </h2>
          {majorRaw?.SubDate && (
            <span className="text-xs text-slate-400 bg-white/5 px-2 py-1 rounded border border-white/10">
              提出日: {majorRaw.SubDate}
            </span>
          )}
        </div>

        {majorList.length > 0 ? (
          <table className="w-full text-sm text-left whitespace-nowrap">
            <thead className="bg-white/5 text-slate-400 font-medium border-b border-white/10 text-xs">
              <tr>
                <th className="py-2 px-3 rounded-tl-lg w-12 text-center">順位</th>
                <th className="py-2 px-3">株主名</th>
                <th className="py-2 px-3 text-right rounded-tr-lg">保有比率</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-slate-200">
              {majorList.slice(0, 10).map((s: any, idx: number) => {
                // J-Quantsは比率を小数(0.1704等)で返すので100を掛けて%にする
                const ratio = toNumber(s.ShsRatio || s.HoldingRatio) * 100;
                const name = s.HldrName || s.Name || '不明';
                return (
                  <tr key={idx} className="hover:bg-white/5 transition-colors">
                    <td className="py-2.5 px-3 text-center text-slate-500">{s.Rank || idx + 1}</td>
                    <td className="py-2.5 px-3 font-medium truncate max-w-[300px]">{name}</td>
                    <td className="py-2.5 px-3 text-right font-bold text-emerald-400/90">{ratio.toFixed(2)}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div className="text-center py-6">
            <p className="text-sm text-slate-400 mb-2">大株主データが見つかりませんでした</p>
          </div>
        )}
      </div>

    </div>
  );
}