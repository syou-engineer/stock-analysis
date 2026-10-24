import React, { useState } from 'react';
import { Search, TrendingUp, AlertCircle, Loader2, BarChart2, LineChart, ExternalLink, Calendar } from 'lucide-react';
import { useStockData } from '../../hooks/useStockData';
import { Background } from '../../components/layout/Background';
import { FundamentalsTab } from '../fundamentals/FundamentalsTab';
import { ChartsTab } from '../supply_demand/ChartsTab';
// ★ 追加: 作成したカレンダータブをインポート
import { CalendarTab } from '../calendar/CalendarTab'; 

type TabType = 'fundamentals' | 'charts' | 'calendar'; // ★ 'calendar' を追加

export function Dashboard() {
  const [searchInput, setSearchInput] = useState('6857');
  const [targetCode, setTargetCode] = useState('6857');
  const [activeTab, setActiveTab] = useState<TabType>('charts');

  const { data, isLoading, isError, error } = useStockData(targetCode);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim().length >= 4) {
      setTargetCode(searchInput.trim());
      // 検索窓から検索された場合は、強制的に詳細分析(チャート)へ遷移させる
      if (activeTab === 'calendar') setActiveTab('charts');
    }
  };

  // ★ 追加: カレンダーで「詳細分析」ボタンが押された時の処理
  const handleSelectFromCalendar = (code: string) => {
    setSearchInput(code); // 検索窓の表示を更新
    setTargetCode(code);  // データをフェッチ
    setActiveTab('charts'); // 詳細分析(チャート)へジャンプ
  };

  const analysis = data?.analysis;

  return (
    <div className="relative h-screen w-full text-slate-200 font-sans selection:bg-blue-500/30 overflow-hidden flex flex-col bg-slate-950">
      <Background />

      <header className="relative z-50 bg-slate-950/80 backdrop-blur-xl border-b border-white/5 shrink-0">
        <div className="w-full px-4 py-2 flex items-center justify-between">
          
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 text-white font-bold text-base">
              <TrendingUp className="text-blue-500" size={18} />
              <span>ProQuants</span>
            </div>
            
            <form onSubmit={handleSearch} className="relative w-64">
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="銘柄コード (例: 6857)"
                className="w-full pl-8 pr-3 py-1 text-xs bg-slate-900/50 border border-white/10 rounded text-white placeholder-slate-500 focus:bg-slate-900 focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 outline-none transition-all"
              />
              <Search className="absolute left-2.5 top-1.5 text-slate-500" size={14} />
            </form>
          </div>

          <div className="flex items-center gap-4">
            {/* ★ カレンダー表示中は現在の個別銘柄情報を非表示にする */}
            {analysis && activeTab !== 'calendar' && (
              <div className="flex items-center gap-3">
                <div className="flex items-baseline gap-2">
                  <h1 className="text-sm font-extrabold text-white">{analysis.basic.company_name}</h1>
                  <span className="text-xs text-blue-400 font-mono bg-blue-500/10 px-1.5 py-0.5 rounded">{analysis.basic.code}</span>
                </div>
                
                <a 
                  href={`https://kabutan.jp/stock/?code=${analysis.basic.code}`} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-[10px] font-medium text-slate-400 hover:text-white bg-white/5 hover:bg-white/10 px-2 py-1 rounded transition-colors border border-white/10"
                  title="株探で企業の事業概要やニュースを確認"
                >
                  株探で見る
                  <ExternalLink size={10} />
                </a>
              </div>
            )}
            
            <div className="flex bg-slate-900/60 rounded border border-white/5 p-0.5 ml-2">
              {/* ★ 追加: 決算カレンダートグル */}
              <button 
                onClick={() => setActiveTab('calendar')} 
                className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-all ${activeTab === 'calendar' ? 'bg-amber-500/20 text-amber-400' : 'text-slate-400 hover:text-white'}`}
              >
                <Calendar size={14} /> 決算カレンダー
              </button>
              
              <div className="w-px h-4 bg-white/10 mx-1 my-auto"></div>
              
              <button 
                onClick={() => setActiveTab('fundamentals')} 
                className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-all ${activeTab === 'fundamentals' ? 'bg-blue-500/20 text-blue-400' : 'text-slate-400 hover:text-white'}`}
              >
                <BarChart2 size={14} /> ファンダ
              </button>
              <button 
                onClick={() => setActiveTab('charts')} 
                className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-all ${activeTab === 'charts' ? 'bg-blue-500/20 text-blue-400' : 'text-slate-400 hover:text-white'}`}
              >
                <LineChart size={14} /> タイムマシン
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="relative z-10 flex-1 w-full p-2 min-h-0 flex flex-col">
        {/* ★ 追加: カレンダー表示時は個別銘柄のローディングを隠し、カレンダーを全画面表示 */}
        {activeTab === 'calendar' ? (
          <CalendarTab onSelectStock={handleSelectFromCalendar} />
        ) : (
          <>
            {isLoading && (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-400 gap-4">
                <Loader2 className="animate-spin text-blue-500" size={32} />
                <p className="text-sm">データを集計中...</p>
              </div>
            )}

            {isError && (
              <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-3 rounded flex items-start gap-3 m-4">
                <AlertCircle size={18} className="mt-0.5 shrink-0" />
                <p className="text-sm">{error instanceof Error ? error.message : 'エラーが発生しました'}</p>
              </div>
            )}

            {analysis && !isLoading && (
              <div className="flex-1 min-h-0 w-full">
                {activeTab === 'fundamentals' && <FundamentalsTab analysis={analysis} />}
                {activeTab === 'charts' && <ChartsTab analysis={analysis} />}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}