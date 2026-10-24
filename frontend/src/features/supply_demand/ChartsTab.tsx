import React, { useEffect, useRef, useState, useMemo } from 'react';
import type { StockAnalysis } from '../../types';
import {
  createChart, ColorType, CandlestickSeries, HistogramSeries, LineSeries, AreaSeries,
  createSeriesMarkers, type Time, type IChartApi, type SeriesMarker, type ISeriesApi
} from 'lightweight-charts';
import { TrendingUp, TrendingDown, Users, Activity, FileText, ChevronRight, PieChart, Building, AlertCircle, Percent, Crosshair, Flame } from 'lucide-react';
// ★ 追加: 共通フォーマッターをインポート
import { formatOku, formatMarketCap } from '../../utils/formatters';

interface Props { analysis: StockAnalysis; }
type Interval = 'D' | 'W' | 'M';
type ComparePreset = '1Y' | '6M' | '3M' | 'CUSTOM';
type ChartMode = 'NORMAL' | 'RELATIVE'; 

// const formatOku = (val: number | null | undefined) => {
//   if (val === null || val === undefined) return '-';
//   const oku = val / 100_000_000;
//   if (Math.abs(oku) < 1) return `${(val / 1000000).toLocaleString(undefined, { maximumFractionDigits: 0 })} 百万円`;
//   if (Math.abs(oku) >= 10000) return `${(oku / 10000).toFixed(1)} 兆円`;
//   return `${oku.toLocaleString(undefined, { maximumFractionDigits: 1 })} 億円`;
// };

// const formatMarketCap = (val: number | null | undefined) => {
//   if (val === null || val === undefined) return '-';
//   return formatOku(val * 1_000_000);
// };

export function ChartsTab({ analysis }: Props) {
  const mainChartContainerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  
  const [interval, setInterval] = useState<Interval>('D');
  const [timeframe, setTimeframe] = useState<'3M' | '6M' | '1Y' | '3Y' | '5Y' | '10Y' | 'MAX'>('1Y'); 
  const [chartMode, setChartMode] = useState<ChartMode>('NORMAL');
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [hoveredData, setHoveredData] = useState<any | null>(null);

  const [baseDate, setBaseDate] = useState<string | null>(null);
  const [comparePreset, setComparePreset] = useState<ComparePreset>('1Y');

  const [priceToPixelFn, setPriceToPixelFn] = useState<((price: number) => number | null) | null>(null);
  const primarySeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  const [layers, setLayers] = useState({
    revisions: true,
    topix: false,
    sector: false,
    per: true,
    pbr: false,
    largeVolume: true,
    volume: true,
    marginBuy: true,  
    marginSell: true, 
  });

  const eventsMap = useMemo(() => {
    const map = new Map<string, any[]>();
    const largeVolRaw = Array.isArray(analysis.large_volume) ? analysis.large_volume : [];
    largeVolRaw.forEach((doc: any) => {
      const dateStr = (doc.SubDate || doc.SubmitDate || '').substring(0, 10);
      if (!dateStr) return;
      const current = parseFloat(doc.TotalShsRatio || 0) * 100;
      const prev = parseFloat(doc.TotalShsRatioLast || 0) * 100;
      let submitterName = '不明な提出者';
      if (Array.isArray(doc.Hldrs) && doc.Hldrs.length > 0) submitterName = doc.Hldrs[0].HldrName || doc.Hldrs[0].Name || submitterName;
      else submitterName = doc.FilerName || doc.SubmitterName || submitterName;

      if (!map.has(dateStr)) map.set(dateStr, []);
      map.get(dateStr)!.push({
        type: 'LARGE_VOLUME', icon: <Users size={14} className="text-blue-400" />,
        title: '大量保有', name: submitterName, current, prev, diff: current - prev, desc: doc.DocTitle || '提出'
      });
    });

    const revisions = analysis.events?.revisions || [];
    revisions.forEach((rev) => {
      const dateStr = rev.date;
      if (!dateStr) return;
      if (!map.has(dateStr)) map.set(dateStr, []);
      map.get(dateStr)!.push({
        type: 'REVISION',
        icon: rev.is_up ? <TrendingUp size={14} className="text-rose-400" /> : <TrendingDown size={14} className="text-emerald-400" />,
        title: rev.is_up ? '上方修正' : '下方修正',
        name: `${rev.fy} 営業利益`, current: rev.new_fop, prev: rev.prev_fop, diff: rev.diff_pct,
        desc: `${formatOku(rev.prev_fop)} → ${formatOku(rev.new_fop)}`, isUp: rev.is_up, timing: rev.timing
      });
    });

    const earnings = analysis.events?.earnings || [];
    earnings.forEach((earn) => {
      const dateStr = earn.date;
      if (!dateStr) return;
      if (!map.has(dateStr)) map.set(dateStr, []);
      map.get(dateStr)!.push({
        type: 'EARNINGS', icon: <FileText size={14} className="text-purple-400" />,
        title: `${earn.title} 発表`, name: '業績ハイライト',
        sales_str: earn.sales_str, sales_yoy: earn.sales_yoy, op_str: earn.op_str, op_yoy: earn.op_yoy
      });
    });

    const others = analysis.events?.other || [];
    others.forEach((ev) => {
      const dateStr = ev.date;
      if (!dateStr) return;
      if (!map.has(dateStr)) map.set(dateStr, []);
      map.get(dateStr)!.push({ type: 'ACCOUNTING', icon: <AlertCircle size={14} className="text-amber-400" />, title: '異常検知', name: ev.title, desc: ev.desc });
    });

    // ★ 修正: イナゴ(主観的表現)から、客観的な需給イベント(アラート)へ変更
    const rawDataForEvents = analysis.price_margin_history || [];
    rawDataForEvents.forEach((d: any, i: number) => {
      const prevD = i > 0 ? rawDataForEvents[i - 1] : null;
      if (prevD && prevD.close && d.close && d.margin_buy_chg && d.margin_buy_chg > 0) {
        const priceChg = ((d.close - prevD.close) / prevD.close) * 100;
        if (priceChg >= 5.0) {
          const dateStr = d.date;
          if (!map.has(dateStr)) map.set(dateStr, []);
          map.get(dateStr)!.push({
            type: 'MARGIN_ALERT', // 変更
            icon: <Flame size={14} className="text-amber-500" />,
            title: '需給イベント (買い残急増)',
            name: `株価急騰 (+${priceChg.toFixed(1)}%) に伴う信用買い増加`,
            desc: `前日比で信用買い残が +${(d.margin_buy_chg / 10000).toFixed(0)}万株 増加。高値での買いポジション積み上がりの可能性があります。`
          });
        }
      }
    });

    return map;
  }, [analysis.large_volume, analysis.events, analysis.price_margin_history]);

  const aggregatedData = useMemo(() => {
    let rawData = analysis.price_margin_history;
    if (!rawData || !rawData.length) return [];
    
    const latestDate = new Date(rawData[rawData.length - 1].date);
    let cutoff = new Date(latestDate);
    if (timeframe !== 'MAX') {
      if (timeframe === '3M') cutoff.setMonth(cutoff.getMonth() - 3);
      if (timeframe === '6M') cutoff.setMonth(cutoff.getMonth() - 6);
      if (timeframe === '1Y') cutoff.setFullYear(cutoff.getFullYear() - 1);
      if (timeframe === '3Y') cutoff.setFullYear(cutoff.getFullYear() - 3);
      if (timeframe === '5Y') cutoff.setFullYear(cutoff.getFullYear() - 5);
      if (timeframe === '10Y') cutoff.setFullYear(cutoff.getFullYear() - 10);
      rawData = rawData.filter(d => new Date(d.date) >= cutoff);
    }

    const grouped: any[] = [];
    let currentPeriod = '';
    let currentCandle: any = null;

    rawData.forEach(d => {
      if (d.close === null) return;
      const date = new Date(d.date);
      let periodKey = '';
      if (interval === 'W') {
        const dDate = new Date(date.getTime());
        dDate.setUTCDate(dDate.getUTCDate() + 4 - (dDate.getUTCDay() || 7));
        const yearStart = new Date(Date.UTC(dDate.getUTCFullYear(), 0, 1));
        const weekNo = Math.ceil((((dDate.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
        periodKey = `${dDate.getUTCFullYear()}-W${weekNo}`;
      } else if (interval === 'M') {
        periodKey = `${date.getFullYear()}-${date.getMonth()}`;
      } else {
        periodKey = d.date;
      }

      const evs = eventsMap.get(d.date) || [];
      const isDailyNewFormat = interval === 'D' ? (new Date(d.date) >= new Date('2026-09-25')) : true;

      if (periodKey !== currentPeriod) {
        if (currentCandle) grouped.push(currentCandle);
        currentPeriod = periodKey;
        currentCandle = { ...d, open: d.open || d.close, high: d.high || d.close, low: d.low || d.close, groupedEvents: [...evs] };
        
        if (!isDailyNewFormat) {
          currentCandle.margin_buy = null;
          currentCandle.margin_sell = null;
          currentCandle.margin_buy_chg = null;
          currentCandle.margin_sell_chg = null;
          currentCandle.std_buy_avg_price = null;
          currentCandle.std_sell_avg_price = null;
        }

      } else {
        currentCandle.high = Math.max(currentCandle.high, d.high || d.close);
        currentCandle.low = Math.min(currentCandle.low, d.low || d.close);
        currentCandle.close = d.close;
        currentCandle.topix = d.topix || currentCandle.topix; 
        currentCandle.sector = d.sector || currentCandle.sector; 
        currentCandle.volume = (currentCandle.volume || 0) + (d.volume || 0);
        
        if (isDailyNewFormat) {
          currentCandle.margin_buy = d.margin_buy;
          currentCandle.margin_buy_chg = d.margin_buy_chg;
          currentCandle.margin_sell = d.margin_sell;
          currentCandle.margin_sell_chg = d.margin_sell_chg;
          currentCandle.std_buy_avg_price = d.std_buy_avg_price || currentCandle.std_buy_avg_price; 
          currentCandle.std_sell_avg_price = d.std_sell_avg_price || currentCandle.std_sell_avg_price; 
        }
        
        currentCandle.per = d.per || currentCandle.per;
      }
    });
    if (currentCandle) grouped.push(currentCandle);
    return grouped;
  }, [analysis.price_margin_history, interval, timeframe, eventsMap]);

  const priceProfileBins = useMemo(() => {
    if (chartMode === 'RELATIVE' || (!layers.marginBuy && !layers.marginSell) || aggregatedData.length === 0) return [];
    
    let minPrice = Infinity;
    let maxPrice = -Infinity;
    
    const targetData = aggregatedData.slice(-60).filter(d => d.std_buy_avg_price || d.std_sell_avg_price);
    
    if (targetData.length === 0) return [];

    targetData.forEach(d => {
      if (d.std_buy_avg_price) {
        minPrice = Math.min(minPrice, d.std_buy_avg_price);
        maxPrice = Math.max(maxPrice, d.std_buy_avg_price);
      }
      if (d.std_sell_avg_price) {
        minPrice = Math.min(minPrice, d.std_sell_avg_price);
        maxPrice = Math.max(maxPrice, d.std_sell_avg_price);
      }
    });
    
    if (minPrice === Infinity) return [];
    
    const binCount = 15;
    const binSize = Math.max((maxPrice - minPrice) / binCount, 1);
    
    const bins = Array.from({ length: binCount + 1 }, (_, i) => ({
      priceStart: minPrice + (i * binSize),
      priceEnd: minPrice + ((i + 1) * binSize),
      priceCenter: minPrice + ((i + 0.5) * binSize),
      buyVol: 0,
      sellVol: 0
    }));

    let maxVol = 0;

    targetData.forEach((d) => {
      if (d.margin_buy_chg && d.margin_buy_chg > 0 && d.std_buy_avg_price) {
        const binIdx = Math.min(Math.floor((d.std_buy_avg_price - minPrice) / binSize), binCount);
        bins[binIdx].buyVol += d.margin_buy_chg;
      }
      if (d.margin_sell_chg && d.margin_sell_chg > 0 && d.std_sell_avg_price) {
        const binIdx = Math.min(Math.floor((d.std_sell_avg_price - minPrice) / binSize), binCount);
        bins[binIdx].sellVol += d.margin_sell_chg;
      }
    });

    bins.forEach(b => {
      const bVol = layers.marginBuy ? b.buyVol : 0;
      const sVol = layers.marginSell ? b.sellVol : 0;
      maxVol = Math.max(maxVol, bVol + sVol);
    });

    return bins.map(b => ({
      ...b,
      buyWidthPct: maxVol > 0 ? (b.buyVol / maxVol) * 100 : 0,
      sellWidthPct: maxVol > 0 ? (b.sellVol / maxVol) * 100 : 0,
    })).filter(b => b.buyVol > 0 || b.sellVol > 0); 
    
  }, [aggregatedData, chartMode, layers.marginBuy, layers.marginSell]);


  useEffect(() => {
    if (!aggregatedData.length) return;
    const latestDate = new Date(aggregatedData[aggregatedData.length - 1].date);
    let targetDate = new Date(latestDate);

    if (comparePreset === '1Y') targetDate.setFullYear(latestDate.getFullYear() - 1);
    else if (comparePreset === '6M') targetDate.setMonth(latestDate.getMonth() - 6);
    else if (comparePreset === '3M') targetDate.setMonth(latestDate.getMonth() - 3);

    if (comparePreset !== 'CUSTOM') {
      const targetStr = targetDate.toISOString().split('T')[0];
      let closestBase = aggregatedData[0].date;
      for (const d of aggregatedData) {
        if (d.date >= targetStr) {
          closestBase = d.date;
          break;
        }
      }
      setBaseDate(closestBase);
    }
  }, [comparePreset, aggregatedData]);

  const baseData = useMemo(() => {
    if (!baseDate || !aggregatedData.length) return aggregatedData[0];
    const found = aggregatedData.find(d => d.date >= baseDate);
    return found || aggregatedData[aggregatedData.length - 1];
  }, [baseDate, aggregatedData]);

  const relativeData = useMemo(() => {
    if (chartMode !== 'RELATIVE' || !aggregatedData.length) return aggregatedData;
    const bClose = baseData.close || 1;
    const bTopix = baseData.topix || 1;
    const bSector = baseData.sector || 1;

    return aggregatedData.map(d => ({
      ...d,
      relClose: ((d.close || bClose) / bClose) * 100 - 100, 
      relTopix: ((d.topix || bTopix) / bTopix) * 100 - 100,
      relSector: ((d.sector || bSector) / bSector) * 100 - 100,
    }));
  }, [aggregatedData, chartMode, baseData]);

  const chartsRef = useRef<IChartApi[]>([]);

  useEffect(() => {
    if (!mainChartContainerRef.current || !aggregatedData.length) return;
    chartsRef.current = [];

    const commonOptions = {
      autoSize: true,
      layout: { background: { type: ColorType.Solid, color: 'transparent' }, textColor: '#94a3b8' },
      grid: { vertLines: { color: '#1e293b55' }, horzLines: { color: '#1e293b55' } },
      timeScale: { borderColor: '#33415555', rightOffset: 5 },
      crosshair: { mode: 1, vertLine: { color: '#ffffff1a', style: 3 }, horzLine: { color: '#ffffff1a', style: 3 } },
      rightPriceScale: { visible: true, borderColor: '#33415555' },
      leftPriceScale: { visible: false, autoScale: true },
    };

    const mainChart = createChart(mainChartContainerRef.current, commonOptions);
    chartsRef.current.push(mainChart);

    let primarySeries: any;

    if (chartMode === 'RELATIVE') {
      primarySeries = mainChart.addSeries(LineSeries, { color: '#3b82f6', lineWidth: 2, priceFormat: { type: 'custom', formatter: (price: number) => price.toFixed(1) + '%' } });
      primarySeries.setData(relativeData.map(d => ({ time: d.date as Time, value: (d as any).relClose })));
      
      if (layers.topix) {
        const topixSeries = mainChart.addSeries(LineSeries, { color: '#a855f7', lineWidth: 2, lineStyle: 1 });
        topixSeries.setData(relativeData.filter(d => d.topix).map(d => ({ time: d.date as Time, value: (d as any).relTopix })));
      }
      if (layers.sector) {
        const sectorSeries = mainChart.addSeries(LineSeries, { color: '#06b6d4', lineWidth: 2, lineStyle: 1 });
        sectorSeries.setData(relativeData.filter(d => d.sector).map(d => ({ time: d.date as Time, value: (d as any).relSector })));
      }
    } else {
      const hasDecimals = !aggregatedData.slice(-5).map(d => d.close || 0).every(c => Math.abs(c - Math.round(c)) < 0.01);
      primarySeries = mainChart.addSeries(CandlestickSeries, { upColor: '#f43f5e', downColor: '#10b981', borderVisible: false, wickUpColor: '#f43f5e', wickDownColor: '#10b981', priceFormat: { type: 'price' as const, precision: hasDecimals ? 2 : 0, minMove: hasDecimals ? 0.01 : 1 } });
      primarySeries.setData(aggregatedData.map(d => ({ time: d.date as Time, open: d.open, high: d.high, low: d.low, close: d.close })));
      
      primarySeriesRef.current = primarySeries;
      mainChart.timeScale().subscribeVisibleLogicalRangeChange(() => {
        setPriceToPixelFn(() => (price: number) => primarySeries.priceToCoordinate(price));
      });
      setTimeout(() => setPriceToPixelFn(() => (price: number) => primarySeries.priceToCoordinate(price)), 100);

      // ★ 修正: 時系列ラインの描画 (点線と現在値ラインの削除)
      if (layers.marginBuy) {
        const stdBuyAvgSeries = mainChart.addSeries(LineSeries, { 
          color: '#f59e0b', 
          lineWidth: 2, 
          // lineStyle: 3 は削除し、実線に変更 (視覚的ノイズを減らすため)
          crosshairMarkerVisible: false 
        });
        const stdBuyAvgData = aggregatedData.filter(d => d.std_buy_avg_price).map(d => ({ time: d.date as Time, value: d.std_buy_avg_price }));
        stdBuyAvgSeries.setData(stdBuyAvgData);
        // createPriceLine (水平線) は削除
      }

      if (layers.marginSell) {
        const stdSellAvgSeries = mainChart.addSeries(LineSeries, { 
          color: '#3b82f6', 
          lineWidth: 2, 
          // lineStyle: 3 は削除
          crosshairMarkerVisible: false 
        });
        const stdSellAvgData = aggregatedData.filter(d => d.std_sell_avg_price).map(d => ({ time: d.date as Time, value: d.std_sell_avg_price }));
        stdSellAvgSeries.setData(stdSellAvgData);
        // createPriceLine (水平線) は削除
      }

      const bClose = baseData.close || 1;
      if (layers.topix) {
        const bTopix = baseData.topix || 1;
        const topixSeries = mainChart.addSeries(LineSeries, { color: '#a855f7', lineWidth: 1.5, crosshairMarkerVisible: false });
        topixSeries.setData(aggregatedData.filter(d => d.topix).map(d => ({ time: d.date as Time, value: d.topix! * (bClose / bTopix) })));
      }
      if (layers.sector) {
        const bSector = baseData.sector || 1;
        const sectorSeries = mainChart.addSeries(LineSeries, { color: '#06b6d4', lineWidth: 1.5, crosshairMarkerVisible: false });
        sectorSeries.setData(aggregatedData.filter(d => d.sector).map(d => ({ time: d.date as Time, value: d.sector! * (bClose / bSector) })));
      }
    }

    if (layers.per && chartMode !== 'RELATIVE') {
      const perSeries = mainChart.addSeries(AreaSeries, { priceScaleId: 'perScale', lineColor: '#fbbf2444', topColor: '#fbbf2415', bottomColor: '#fbbf2400', lineWidth: 1, crosshairMarkerVisible: false, priceLineVisible: false });
      mainChart.priceScale('perScale').applyOptions({ visible: false });
      perSeries.setData(aggregatedData.map(d => ({ time: d.date as Time, value: d.per || 0 })));
    }
    if (layers.pbr && !layers.per && chartMode !== 'RELATIVE') { 
      const pbrSeries = mainChart.addSeries(AreaSeries, { priceScaleId: 'pbrScale', lineColor: '#a78bfa44', topColor: '#a78bfa15', bottomColor: '#a78bfa00', lineWidth: 1, crosshairMarkerVisible: false, priceLineVisible: false });
      mainChart.priceScale('pbrScale').applyOptions({ visible: false });
      pbrSeries.setData(aggregatedData.map(d => ({ time: d.date as Time, value: d.pbr || 0 })));
    }
    
    if (layers.volume) {
      const volumeSeries = mainChart.addSeries(HistogramSeries, { color: '#33415555', priceFormat: { type: 'volume' }, priceScaleId: 'vol' });
      mainChart.priceScale('vol').applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } });
      volumeSeries.setData(aggregatedData.map(d => ({ time: d.date as Time, value: d.volume || 0, color: (d.close || 0) > (d.open || 0) ? '#f43f5e44' : '#10b98144' })));
    }

    let visibleCount = 250; 
    if (interval === 'W') visibleCount = 52;
    if (interval === 'M') visibleCount = 12;
    mainChart.timeScale().setVisibleLogicalRange({ from: Math.max(0, aggregatedData.length - visibleCount), to: aggregatedData.length - 1 });

    const markers: SeriesMarker<Time>[] = [];
    relativeData.forEach(d => {
      const evs = d.groupedEvents || [];
      if (evs.length > 0) {
        const activeEvs = evs.filter((ev: any) => {
          if (ev.type === 'LARGE_VOLUME' && !layers.largeVolume) return false;
          if (ev.type === 'REVISION' && !layers.revisions) return false;
          if (ev.type === 'MARGIN_ALERT' && !layers.marginBuy) return false; // 変更
          return true;
        });

        if (activeEvs.length > 0) {
          let text = '';
          let color = '#3b82f6';
          if (activeEvs.length > 1) { text = `[${activeEvs.length}]`; color = '#8b5cf6'; }
          else {
            const ev = activeEvs[0];
            if (ev.type === 'LARGE_VOLUME') { text = '大'; color = '#3b82f6'; }
            else if (ev.type === 'EARNINGS') { text = '決'; color = '#a855f7'; }
            else if (ev.type === 'REVISION') { text = ev.isUp ? '↑' : '↓'; color = ev.isUp ? '#f43f5e' : '#10b981'; }
            else if (ev.type === 'MARGIN_ALERT') { text = '熱'; color = '#f59e0b'; } // 変更
          }
          markers.push({ time: d.date as Time, position: 'aboveBar', color, shape: 'circle', size: 1, text });
        }
      }
    });

    if (baseData) {
       markers.push({ time: baseData.date as Time, position: 'belowBar', color: '#e2e8f0', shape: 'arrowUp', size: 1, text: '基準' });
    }
    markers.sort((a, b) => (a.time as string).localeCompare(b.time as string));
    createSeriesMarkers(primarySeries, markers);

    const activeCharts = chartsRef.current;
    let isSyncing = false;

    activeCharts.forEach(chart => {
      chart.timeScale().subscribeVisibleLogicalRangeChange(range => {
        if (!isSyncing && range) {
          isSyncing = true;
          activeCharts.forEach(c => { if (c !== chart) c.timeScale().setVisibleLogicalRange(range); });
          isSyncing = false;
        }
      });

      chart.subscribeCrosshairMove(param => {
        if (!isSyncing && param.time) {
          isSyncing = true;
          activeCharts.forEach(c => { if (c !== chart) c.setCrosshairPosition(param.point!.x, param.time!, primarySeries as any); });
          isSyncing = false;
        }
        if (param.time) setHoveredData(relativeData.find(d => d.date === param.time) || null);
        else setHoveredData(null);

        const tooltip = tooltipRef.current;
        if (!tooltip || !param.point || !param.time || param.point.x < 0 || param.point.y < 0) {
          if (tooltip) tooltip.style.display = 'none';
          return;
        }
        
        const candle = aggregatedData.find(d => d.date === param.time);
        const evs = candle?.groupedEvents || [];
        const activeEvs = evs.filter((ev: any) => {
          if (ev.type === 'LARGE_VOLUME' && !layers.largeVolume) return false;
          if (ev.type === 'REVISION' && !layers.revisions) return false;
          if (ev.type === 'MARGIN_ALERT' && !layers.marginBuy) return false; // 変更
          return true;
        });

        if (activeEvs && activeEvs.length > 0) {
          let html = `<div class="font-mono text-xs text-slate-400 mb-2 border-b border-slate-700 pb-1">${param.time}</div>`;
          html += `<div class="text-xs text-blue-400 font-bold mb-1">${activeEvs.length}件のイベント</div>`;
          activeEvs.slice(0, 3).forEach((ev: any) => { html += `<div class="text-xs text-slate-300 truncate mb-0.5">• ${ev.title}: ${ev.name}</div>`; });
          if (activeEvs.length > 3) html += `<div class="text-[10px] text-slate-500">他 ${activeEvs.length - 3}件...</div>`;
          html += `<div class="text-[10px] text-emerald-400 mt-1">クリックして詳細を表示</div>`;
          tooltip.innerHTML = html;
          tooltip.style.display = 'block';
          tooltip.style.left = Math.min(param.point.x + 15, mainChartContainerRef.current!.clientWidth - 215) + 'px';
          tooltip.style.top = Math.max(10, param.point.y - 10) + 'px';
        } else {
            tooltip.style.display = 'none';
        }
      });

      chart.subscribeClick(param => {
        if (param.time) setSelectedDate(param.time as string);
      });
    });

    return () => activeCharts.forEach(c => c.remove());
  }, [relativeData, layers, interval, chartMode, baseData]); 

  const displayQuote = hoveredData || relativeData[relativeData.length - 1];
  
  const selectedEvents = useMemo(() => {
    if (!selectedDate) return [];
    const candle = aggregatedData.find(d => d.date === selectedDate);
    const rawEvs = candle?.groupedEvents || [];
    return rawEvs.filter((ev: any) => {
      if (ev.type === 'LARGE_VOLUME' && !layers.largeVolume) return false;
      if (ev.type === 'REVISION' && !layers.revisions) return false;
      if (ev.type === 'MARGIN_ALERT' && !layers.marginBuy) return false; // 変更
      return true;
    });
  }, [selectedDate, aggregatedData, layers]);

  const calcDiff = (current?: number | null, base?: number | null) => {
    if (!current || !base || base === 0) return null;
    return ((current / base) - 1) * 100;
  };
  
  const perf = {
    price: calcDiff(displayQuote?.close, baseData?.close),
    topix: calcDiff(displayQuote?.topix, baseData?.topix),
    sector: calcDiff(displayQuote?.sector, baseData?.sector),
    per: calcDiff(displayQuote?.per, baseData?.per),
    pbr: calcDiff(displayQuote?.pbr, baseData?.pbr),
  };

  const getAfterEventPerformance = (eventDateStr: string) => {
    const eventIdx = aggregatedData.findIndex(d => d.date === eventDateStr);
    if (eventIdx === -1) return null;
    const bClose = aggregatedData[eventIdx].close;
    if (!bClose) return null;
    const after1W = aggregatedData[Math.min(eventIdx + 5, aggregatedData.length - 1)]?.close;
    const after1M = aggregatedData[Math.min(eventIdx + 20, aggregatedData.length - 1)]?.close;
    return { baseClose: bClose, after1W: calcDiff(after1W, bClose), after1M: calcDiff(after1M, bClose) };
  };
  const eventPerf = selectedDate ? getAfterEventPerformance(selectedDate) : null;

  return (
    <div className="bg-slate-950 rounded border border-white/10 overflow-hidden flex h-full w-full animate-in fade-in duration-500 shadow-2xl relative">
      <div ref={tooltipRef} className="absolute z-50 w-48 bg-slate-900/95 backdrop-blur-md border border-slate-600 rounded p-2 shadow-2xl pointer-events-none transition-opacity duration-150" style={{ display: 'none' }} />

      <div className="flex-1 flex flex-col relative border-r border-white/5 min-w-0">
        
        <div className="px-3 py-2 border-b border-white/5 bg-slate-900/80 shrink-0 flex flex-col md:flex-row items-start md:items-center justify-between gap-2 overflow-x-auto custom-scrollbar">
          <div className="flex gap-4 text-[10px] min-w-max">
            <div className="flex items-center gap-2 border-r border-white/10 pr-4">
              <span className="text-slate-500 font-bold flex items-center gap-1"><Percent size={12}/> モード</span>
              <button onClick={() => setChartMode('NORMAL')} className={`px-2 py-0.5 rounded transition-all ${chartMode === 'NORMAL' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}>実数</button>
              <button onClick={() => setChartMode('RELATIVE')} className={`px-2 py-0.5 rounded transition-all ${chartMode === 'RELATIVE' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'}`} title="基準日を0%としてパフォーマンスを比較">比較 (相対)</button>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-slate-500 font-bold flex items-center gap-1"><Building size={12}/> 企業</span>
              <label className="flex items-center gap-1 text-emerald-400 hover:text-emerald-300 cursor-pointer"><input type="checkbox" checked={layers.revisions} onChange={() => setLayers(l => ({...l, revisions: !l.revisions}))} className="accent-emerald-500" /> 業績修正</label>
              <label className="flex items-center gap-1 text-purple-400 hover:text-purple-300 cursor-pointer"><input type="checkbox" checked={layers.topix} onChange={() => setLayers(l => ({...l, topix: !l.topix}))} className="accent-purple-500" /> TOPIX</label>
              <label className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300 cursor-pointer"><input type="checkbox" checked={layers.sector} onChange={() => setLayers(l => ({...l, sector: !l.sector}))} className="accent-cyan-500" /> 業種別({analysis.basic.industry})</label>
            </div>
            <div className="flex items-center gap-2 border-l border-white/10 pl-4">
              <span className="text-slate-500 font-bold flex items-center gap-1"><PieChart size={12}/> バリュー</span>
              <label className="flex items-center gap-1 text-amber-400 hover:text-amber-300 cursor-pointer"><input type="checkbox" checked={layers.per} onChange={() => setLayers(l => ({...l, per: !l.per, pbr: l.per ? l.pbr : false}))} className="accent-amber-500" disabled={chartMode==='RELATIVE'} /> PER</label>
              <label className="flex items-center gap-1 text-purple-400 hover:text-purple-300 cursor-pointer"><input type="checkbox" checked={layers.pbr} onChange={() => setLayers(l => ({...l, pbr: !l.pbr, per: l.pbr ? l.per : false}))} className="accent-purple-500" disabled={chartMode==='RELATIVE'} /> PBR</label>
            </div>
            <div className="flex items-center gap-2 border-l border-white/10 pl-4">
              <span className="text-slate-500 font-bold flex items-center gap-1"><Users size={12}/> 需給・株主</span>
              <label className="flex items-center gap-1 text-blue-400 hover:text-blue-300 cursor-pointer"><input type="checkbox" checked={layers.largeVolume} onChange={() => setLayers(l => ({...l, largeVolume: !l.largeVolume}))} className="accent-blue-500" /> 大量保有</label>
              <label className="flex items-center gap-1 text-rose-400 hover:text-rose-300 cursor-pointer"><input type="checkbox" checked={layers.marginBuy} onChange={() => setLayers(l => ({...l, marginBuy: !l.marginBuy}))} className="accent-rose-500" disabled={chartMode==='RELATIVE'} /> 買残(橙)</label>
              <label className="flex items-center gap-1 text-blue-500 hover:text-blue-400 cursor-pointer"><input type="checkbox" checked={layers.marginSell} onChange={() => setLayers(l => ({...l, marginSell: !l.marginSell}))} className="accent-blue-600" disabled={chartMode==='RELATIVE'} /> 売残(青)</label>
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0 mt-2 md:mt-0">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-medium text-slate-400">基準日:</span>
              <span className="text-[10px] font-bold text-white bg-slate-800 px-1.5 py-0.5 rounded border border-white/10">{baseData?.date || '-'}</span>
            </div>
            <div className="flex bg-slate-800/80 p-0.5 rounded border border-white/5">
              {(['1Y', '6M', '3M'] as ComparePreset[]).map(t => (
                <button key={t} onClick={() => setComparePreset(t)} className={`px-2 py-0.5 rounded text-[9px] font-bold ${comparePreset === t ? 'bg-blue-600 text-white' : 'text-slate-400'}`}>
                  {t === '1Y' ? '1年前' : t === '6M' ? '半年' : '3ヶ月'}
                </button>
              ))}
              <button onClick={() => setComparePreset('CUSTOM')} className={`px-2 py-0.5 rounded text-[9px] font-bold ${comparePreset === 'CUSTOM' ? 'bg-purple-600 text-white' : 'text-slate-400'}`}>イベント</button>
            </div>
          </div>
        </div>

        {/* チャート */}
        <div className="flex-1 flex flex-col min-h-0 bg-slate-900/40 relative">
          <div className="flex-[3] relative min-h-0">
            <div ref={mainChartContainerRef} className="absolute inset-0" />
            
            {/* ★ 価格帯別 信用建玉ヒストグラムのHTMLオーバーレイ */}
            {(layers.marginBuy || layers.marginSell) && chartMode === 'NORMAL' && priceToPixelFn && priceProfileBins.length > 0 && (
              <div className="absolute top-0 right-[60px] bottom-0 w-32 pointer-events-none z-10 flex flex-col justify-between overflow-hidden opacity-80 mix-blend-screen">
                {priceProfileBins.map((bin, i) => {
                  const yTop = priceToPixelFn(bin.priceEnd);
                  const yBottom = priceToPixelFn(bin.priceStart);
                  if (yTop === null || yBottom === null) return null;
                  
                  const height = Math.abs(yBottom - yTop);
                  const top = Math.min(yTop, yBottom);

                  return (
                    <div key={i} className="absolute right-0 flex flex-col justify-center" style={{ top: `${top}px`, height: `${height}px`, width: '100%' }}>
                      <div className="w-full flex justify-end gap-0.5 h-[80%]">
                        {layers.marginSell && bin.sellWidthPct > 0 && (
                          <div className="bg-blue-500 h-full rounded-l-sm" style={{ width: `${bin.sellWidthPct}%`, opacity: 0.6 }} />
                        )}
                        {layers.marginBuy && bin.buyWidthPct > 0 && (
                          <div className="bg-rose-500 h-full rounded-l-sm" style={{ width: `${bin.buyWidthPct}%`, opacity: 0.6 }} />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="absolute top-2 left-2 z-10 pointer-events-none flex gap-2">
              <div className="bg-slate-900/80 backdrop-blur border border-white/10 px-2 py-1 rounded shadow text-[10px] flex items-center gap-3">
                <div className="flex items-baseline gap-1">
                   <span className="text-slate-400">株価</span>
                   <span className="font-bold text-blue-400">{chartMode === 'RELATIVE' ? `${displayQuote?.relClose > 0 ? '+' : ''}${displayQuote?.relClose?.toFixed(1)}%` : `${displayQuote?.close?.toLocaleString()}円`}</span>
                   {perf.price !== null && chartMode !== 'RELATIVE' && <span className={`font-bold ml-1 ${perf.price > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>({perf.price > 0 ? '+' : ''}{perf.price.toFixed(1)}%)</span>}
                </div>
                {layers.topix && (
                  <div className="flex items-baseline gap-1 border-l border-white/10 pl-3">
                     <span className="text-purple-500/70">TOPIX</span>
                     <span className="font-bold text-purple-400">{chartMode === 'RELATIVE' ? `${displayQuote?.relTopix > 0 ? '+' : ''}${displayQuote?.relTopix?.toFixed(1)}%` : displayQuote?.topix?.toFixed(1)}</span>
                     {perf.topix !== null && chartMode !== 'RELATIVE' && <span className={`font-bold ml-1 ${perf.topix > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>({perf.topix > 0 ? '+' : ''}{perf.topix.toFixed(1)}%)</span>}
                  </div>
                )}
                {layers.sector && (
                  <div className="flex items-baseline gap-1 border-l border-white/10 pl-3">
                     <span className="text-cyan-500/70">{analysis.basic.industry}</span>
                     <span className="font-bold text-cyan-400">{chartMode === 'RELATIVE' ? `${displayQuote?.relSector > 0 ? '+' : ''}${displayQuote?.relSector?.toFixed(1)}%` : displayQuote?.sector?.toFixed(1)}</span>
                     {perf.sector !== null && chartMode !== 'RELATIVE' && <span className={`font-bold ml-1 ${perf.sector > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>({perf.sector > 0 ? '+' : ''}{perf.sector.toFixed(1)}%)</span>}
                  </div>
                )}
                {layers.per && chartMode !== 'RELATIVE' && (
                  <div className="flex items-baseline gap-1 border-l border-white/10 pl-3">
                     <span className="text-amber-500/70">PER</span>
                     <span className="font-bold text-amber-400">{displayQuote?.per?.toFixed(1)}倍</span>
                     {perf.per !== null && <span className={`font-bold ml-1 ${perf.per > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>({perf.per > 0 ? '+' : ''}{perf.per.toFixed(1)}%)</span>}
                  </div>
                )}
              </div>
            </div>

            <div className="absolute bottom-2 left-2 z-10 flex gap-2">
              <div className="flex bg-slate-800/80 p-0.5 rounded border border-white/5 pointer-events-auto">
                {(['3M', '6M', '1Y', '3Y', '5Y', '10Y', 'MAX'] as const).map(t => (
                  <button key={t} onClick={() => setTimeframe(t)} className={`px-2 py-0.5 rounded text-[10px] font-bold ${timeframe === t ? 'bg-slate-600 text-white' : 'text-slate-400'}`}>{t}</button>
                ))}
              </div>
              <div className="flex bg-slate-800/80 p-0.5 rounded border border-white/5 pointer-events-auto">
                {(['D', 'W', 'M'] as Interval[]).map(t => (
                  <button key={t} onClick={() => setInterval(t)} className={`px-3 py-0.5 rounded text-[10px] font-bold ${interval === t ? 'bg-blue-600 text-white' : 'text-slate-400'}`}>{t === 'D' ? '日' : t === 'W' ? '週' : '月'}</button>
                ))}
              </div>
            </div>
            
            {(layers.marginBuy || layers.marginSell) && chartMode !== 'RELATIVE' && (
              <div className="absolute top-10 right-[60px] z-10 pointer-events-none text-right">
                <span className="text-[9px] font-bold text-slate-500 bg-slate-900/60 px-1 rounded">直近60日 建玉分布</span>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="w-64 bg-slate-900 shrink-0 flex flex-col border-l border-white/5">
        <div className="p-3 border-b border-white/5 bg-slate-950/50 shrink-0">
          <div className="flex justify-between items-center mb-2">
             <span className="text-[10px] font-mono text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded border border-emerald-400/20">{displayQuote?.date || '-'}</span>
          </div>
          <div className="grid grid-cols-2 gap-y-3 gap-x-2 text-[10px]">
             <div><p className="text-slate-500">出来高</p><p className="font-bold text-slate-200">{displayQuote?.volume ? `${(displayQuote.volume / 10000).toFixed(1)} 万` : '-'}</p></div>
             <div><p className="text-slate-500">時価総額</p><p className="font-bold text-slate-200">{formatMarketCap(displayQuote?.market_cap)}</p></div>
             
             {(layers.marginBuy || layers.marginSell) && (
               <>
                <div className="col-span-2 border-t border-white/10 pt-2 mt-1">
                  <p className="text-slate-500 font-bold mb-1 border-b border-white/5 pb-1">信用需給状況 <span className="text-[9px] font-normal">(更新日のみ増減表示)</span></p>
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    {layers.marginBuy && (
                      <div>
                        <p className="text-slate-400">買残</p>
                        <p className="font-bold font-mono text-rose-400">
                          {displayQuote?.margin_buy ? `${(displayQuote.margin_buy / 10000).toFixed(0)}万` : '-'}
                          {displayQuote?.margin_buy_chg ? (
                            <span className={`text-[9px] ml-1 ${displayQuote.margin_buy_chg > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                              ({displayQuote.margin_buy_chg > 0 ? '+' : ''}{(displayQuote.margin_buy_chg / 10000).toFixed(0)}万)
                            </span>
                          ) : ''}
                        </p>
                      </div>
                    )}
                    {layers.marginSell && (
                      <div>
                        <p className="text-slate-400">売残</p>
                        <p className="font-bold font-mono text-blue-400">
                          {displayQuote?.margin_sell ? `${(displayQuote.margin_sell / 10000).toFixed(0)}万` : '-'}
                          {displayQuote?.margin_sell_chg ? (
                            <span className={`text-[9px] ml-1 ${displayQuote.margin_sell_chg > 0 ? 'text-blue-400' : 'text-rose-400'}`}>
                              ({displayQuote.margin_sell_chg > 0 ? '+' : ''}{(displayQuote.margin_sell_chg / 10000).toFixed(0)}万)
                            </span>
                          ) : ''}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* ★ 修正: 断定表現を避け、推計値であることを明示 */}
                {layers.marginBuy && displayQuote?.std_buy_avg_price && displayQuote?.close && (
                  <div className="col-span-2 bg-slate-800/50 border border-white/5 p-2 rounded mt-1">
                    <p className="text-slate-400 mb-0.5">制度買い <span className="text-slate-300">参考建値</span> <span className="text-[8px] text-slate-500">(金額÷株数)</span></p>
                    <div className="flex justify-between items-end">
                      <span className="font-bold text-rose-400 font-mono">{displayQuote.std_buy_avg_price.toLocaleString(undefined, {maximumFractionDigits: 1})} 円</span>
                      <div className="text-right">
                        <p className="text-[9px] text-slate-500 mb-0.5">現在株価との乖離率</p>
                        <span className={`font-bold font-mono ${displayQuote.close >= displayQuote.std_buy_avg_price ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {(((displayQuote.close / displayQuote.std_buy_avg_price) - 1) * 100) > 0 ? '+' : ''}
                          {(((displayQuote.close / displayQuote.std_buy_avg_price) - 1) * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                )}
                
                {layers.marginSell && displayQuote?.std_sell_avg_price && displayQuote?.close && (
                  <div className="col-span-2 bg-slate-800/50 border border-white/5 p-2 rounded mt-1">
                    <p className="text-slate-400 mb-0.5">制度売り <span className="text-slate-300">参考建値</span> <span className="text-[8px] text-slate-500">(金額÷株数)</span></p>
                    <div className="flex justify-between items-end">
                      <span className="font-bold text-blue-400 font-mono">{displayQuote.std_sell_avg_price.toLocaleString(undefined, {maximumFractionDigits: 1})} 円</span>
                      <div className="text-right">
                        <p className="text-[9px] text-slate-500 mb-0.5">現在株価との乖離率</p>
                        <span className={`font-bold font-mono ${displayQuote.close <= displayQuote.std_sell_avg_price ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {(((displayQuote.std_sell_avg_price / displayQuote.close) - 1) * 100) > 0 ? '+' : ''}
                          {(((displayQuote.std_sell_avg_price / displayQuote.close) - 1) * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                )}
               </>
             )}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-3 bg-slate-900/50 relative">
          <h3 className="text-[11px] font-bold text-slate-300 mb-3 flex items-center gap-1"><FileText size={12} className="text-blue-400" />選択イベント</h3>
          {!selectedDate ? (
            <div className="mt-8 text-center opacity-50"><AlertCircle size={14} className="text-slate-400 mx-auto mb-1" /><p className="text-[10px] text-slate-400">チャートのマーカーを<br/>クリックして詳細表示</p></div>
          ) : (
            <div className="space-y-4 animate-in slide-in-from-right-2 duration-300">
              <p className="text-[10px] font-mono text-white font-bold border-b border-white/5 pb-1">{selectedDate}</p>
              
              {selectedEvents.length === 0 ? (
                <p className="text-[10px] text-slate-500">イベントなし</p>
              ) : (
                <div className="space-y-3">
                  {selectedEvents.map((ev, idx) => (
                    <div key={idx} className="bg-slate-800/80 border border-slate-700 rounded p-2 relative overflow-hidden">
                      <div className={`absolute top-0 left-0 w-0.5 h-full ${ev.diff && ev.diff > 0 ? 'bg-rose-500' : 'bg-emerald-500'}`} />
                      <div className="flex items-center gap-1 mb-1 text-[10px] font-bold text-blue-400 pl-1">{ev.icon} {ev.title}</div>
                      <p className="text-xs text-white font-bold mb-1 pl-1">{ev.name} {ev.timing && <span className="text-[9px] text-slate-400 bg-slate-700 px-1 rounded ml-1">{ev.timing}</span>}</p>

                      {ev.type === 'LARGE_VOLUME' && (
                        <div className="bg-slate-900/80 rounded p-1.5 border border-white/5 text-[10px] ml-1">
                          <div className="flex justify-between items-center">
                            <span className="text-slate-400 font-mono">{ev.prev.toFixed(2)}%</span><ChevronRight size={10} className="text-slate-600"/><span className="text-white font-bold font-mono">{ev.current.toFixed(2)}%</span>
                          </div>
                          {Math.abs(ev.diff) > 0.01 && (<p className={`text-right font-bold mt-0.5 ${ev.diff > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>({ev.diff > 0 ? '+' : ''}{ev.diff.toFixed(2)} pt)</p>)}
                        </div>
                      )}

                      {ev.type === 'REVISION' && (
                        <div className="bg-slate-900/80 rounded p-1.5 border border-white/5 text-[10px] ml-1">
                          <div className="flex justify-center items-center mb-1 text-slate-300">
                             <span className="line-through">{ev.desc.split('→')[0]}</span><ChevronRight size={10} className="mx-1 text-slate-500"/><span className="font-bold text-white">{ev.desc.split('→')[1]}</span>
                          </div>
                          <p className={`text-center font-bold text-[11px] ${ev.isUp ? 'text-rose-400' : 'text-emerald-400'}`}>
                            {ev.isUp ? '+' : ''}{ev.diff.toFixed(1)}% {ev.isUp ? '上方修正' : '下方修正'}
                          </p>
                        </div>
                      )}

                      {ev.type === 'EARNINGS' && (
                        <div className="bg-purple-500/10 rounded p-1.5 border border-purple-500/20 text-[10px] ml-1 text-purple-200">
                          <div className="flex justify-between items-center border-b border-purple-500/20 pb-0.5 mb-1">
                            <span className="text-purple-300">売上高</span>
                            <span className="font-bold font-mono">{ev.sales_str} {ev.sales_yoy !== null && <span className={ev.sales_yoy > 0 ? 'text-rose-400' : 'text-emerald-400'}>({ev.sales_yoy > 0 ? '+' : ''}{ev.sales_yoy.toFixed(1)}%)</span>}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-purple-300">営業利益</span>
                            <span className="font-bold font-mono">{ev.op_str} {ev.op_yoy !== null && <span className={ev.op_yoy > 0 ? 'text-rose-400' : 'text-emerald-400'}>({ev.op_yoy > 0 ? '+' : ''}{ev.op_yoy.toFixed(1)}%)</span>}</span>
                          </div>
                        </div>
                      )}

                      {/* ★ 修正: イナゴという表現を排し、客観的なファクトに基づく説明へ */}
                      {ev.type === 'MARGIN_ALERT' && (
                        <div className="bg-amber-500/10 rounded p-1.5 border border-amber-500/20 text-[10px] ml-1">
                          <p className="text-amber-200">{ev.desc}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {eventPerf && eventPerf.baseClose && (
                <div className="bg-slate-950/50 rounded p-2 mt-4 border border-white/5">
                  <p className="text-[10px] text-slate-400 mb-2">イベント後のリアクション</p>
                  <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                    <div className="bg-slate-800/50 p-2 rounded">
                      <p className="text-[9px] text-slate-500 mb-0.5">当日の株価</p>
                      <p className="font-bold text-slate-300">{eventPerf.baseClose.toLocaleString()}円</p>
                    </div>
                    <div className="bg-slate-800/50 p-2 rounded">
                      <p className="text-[9px] text-slate-500 mb-0.5">1週間後</p>
                      <p className={`font-bold ${eventPerf.after1W && eventPerf.after1W > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {eventPerf.after1W ? `${eventPerf.after1W > 0 ? '+' : ''}${eventPerf.after1W.toFixed(1)}%` : '-'}
                      </p>
                    </div>
                    <div className="col-span-2 flex justify-between border-t border-white/5 pt-1 mt-1">
                      <span className="text-[9px] text-slate-500">1ヶ月後</span>
                      <span className={`font-bold ${eventPerf.after1M && eventPerf.after1M > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {eventPerf.after1M ? `${eventPerf.after1M > 0 ? '+' : ''}${eventPerf.after1M.toFixed(1)}%` : '-'}
                      </span>
                    </div>
                  </div>
                  
                  <button 
                    onClick={() => {
                      setComparePreset('CUSTOM');
                      setBaseDate(selectedDate);
                    }}
                    className={`w-full py-1.5 rounded flex items-center justify-center gap-1.5 text-[10px] font-bold transition-all border
                      ${baseDate === selectedDate 
                        ? 'bg-purple-500/20 border-purple-500/30 text-purple-300 cursor-default' 
                        : 'bg-slate-800 border-slate-600 text-white hover:bg-slate-700'}`}
                  >
                    <Crosshair size={12} />
                    {baseDate === selectedDate ? '比較基準日に設定中' : 'この日を比較基準にする'}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}