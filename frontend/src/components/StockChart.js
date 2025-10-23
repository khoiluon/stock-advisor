// frontend/src/components/StockChart.js

import React, { useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';

function calculateSMA(data, period) {
  if (!data || data.length < period) return [];
  const result = [];
  for (let i = period - 1; i < data.length; i++) {
    const sum = data.slice(i - period + 1, i + 1).reduce((acc, d) => acc + d.close, 0);
    result.push({ time: data[i].date, value: Number((sum / period).toFixed(2)) });
  }
  return result;
}

function calculateMACD(data, fast = 12, slow = 26, signal = 9) {
  if (!data || data.length < slow) return []; // Cần đủ dữ liệu để tính toán
  const ema = (arr, period, key = 'close') => {
    const k = 2 / (period + 1);
    let emaArr = [];
    if (arr.length > 0 && arr[0][key] !== undefined) {
      emaArr.push(arr[0][key]);
      for (let i = 1; i < arr.length; i++) {
        emaArr.push(arr[i][key] * k + emaArr[i - 1] * (1 - k));
      }
    }
    return emaArr;
  };
  const fastEMA = ema(data, fast);
  const slowEMA = ema(data, slow);
  const macdLine = fastEMA.map((val, i) => val - slowEMA[i]);
  const signalLineData = macdLine.map((value, i) => ({ close: value, date: data[i].date }));
  const signalLine = ema(signalLineData, signal);
  const histogram = macdLine.map((val, i) => val - signalLine[i]);
  return data.map((d, i) => ({
    time: d.date, macd: macdLine[i], signal: signalLine[i], hist: histogram[i],
  }));
}

// --- COMPONENT BIỂU ĐỒ ---
const StockChart = ({ data, ticker, maLines = [], indicators = {} }) => {
  const chartContainerRef = useRef(null);

  useEffect(() => {
    if (!chartContainerRef.current || !data || data.length === 0) {
      // Nếu không có dữ liệu, dọn dẹp biểu đồ cũ (nếu có)
      if (chartContainerRef.current) chartContainerRef.current.innerHTML = '';
      return;
    }

    // **LOGIC "PHÁ ĐI XÂY LẠI" CÓ KIỂM SOÁT**
    // Xóa biểu đồ cũ trước khi vẽ cái mới để đảm bảo sự sạch sẽ
    chartContainerRef.current.innerHTML = '';

    const chart = createChart(chartContainerRef.current, {
      layout: { background: { type: ColorType.Solid, color: '#0f172a' }, textColor: '#94a3b8' },
      grid: { vertLines: { color: '#1e293b' }, horzLines: { color: '#1e293b' } },
      width: chartContainerRef.current.clientWidth,
      height: 400,
      timeScale: { borderColor: '#475569', timeVisible: true },
    });

    // --- Xử lý dữ liệu ---
    const sortedData = [...data].sort((a, b) => new Date(a.date) - new Date(b.date));
    const candlestickData = sortedData.map(d => ({
      time: d.date, open: d.open, high: d.high, low: d.low, close: d.close,
    }));
    const volumeData = sortedData.map(d => ({
      time: d.date, value: d.volume,
      color: d.close >= d.open ? 'rgba(34, 197, 94, 0.5)' : 'rgba(239, 68, 68, 0.5)',
    }));

    // --- Vẽ Series chính ---
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#22c55e', downColor: '#ef4444', borderVisible: false,
      wickUpColor: '#22c55e', wickDownColor: '#ef4444',
    });
    candleSeries.setData(candlestickData);

    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume_scale',
    });
    volumeSeries.setData(volumeData);

    // --- Vẽ các chỉ báo (dựa trên logic từ file cũ của bạn) ---
    let macdCreated = false;

    // Moving Averages
    const maColors = { 20: '#38bdf8', 50: '#a78bfa', 200: '#facc15' };
    maLines.forEach(line => {
      const maData = calculateSMA(sortedData, line.period);
      const maSeries = chart.addLineSeries({ color: maColors[line.period] || '#FFFFFF', lineWidth: 2 });
      maSeries.setData(maData);
    });

    // Bollinger Bands
    if (indicators.bbands?.visible && sortedData[0]?.['BBU_20_2.0']) {
      const bbandsData = sortedData.map(d => ({
        time: d.date, upper: d['BBU_20_2.0'], middle: d['BBM_20_2.0'], lower: d['BBL_20_2.0'],
      })).filter(d => d.upper);
      const upper = chart.addLineSeries({ color: 'rgba(59,130,246,0.5)', lineWidth: 1 });
      const middle = chart.addLineSeries({ color: 'rgba(250, 204, 21, 0.5)', lineWidth: 1, lineStyle: 2 });
      const lower = chart.addLineSeries({ color: 'rgba(59,130,246,0.5)', lineWidth: 1 });
      upper.setData(bbandsData.map(d => ({ time: d.time, value: d.upper })));
      middle.setData(bbandsData.map(d => ({ time: d.time, value: d.middle })));
      lower.setData(bbandsData.map(d => ({ time: d.time, value: d.lower })));
    }

    // MACD
    if (indicators.macd?.visible) {
      macdCreated = true;
      const macdData = calculateMACD(sortedData, indicators.macd.fast, indicators.macd.slow, indicators.macd.signal);
      const macdSeries = chart.addLineSeries({ color: '#38bdf8', lineWidth: 2, priceScaleId: 'macd' });
      const signalSeries = chart.addLineSeries({ color: '#a78bfa', lineWidth: 2, lineStyle: 2, priceScaleId: 'macd' });
      const histSeries = chart.addHistogramSeries({ priceScaleId: 'macd' });
      macdSeries.setData(macdData.map(d => ({ time: d.time, value: d.macd })));
      signalSeries.setData(macdData.map(d => ({ time: d.time, value: d.signal })));
      histSeries.setData(macdData.map(d => ({ time: d.time, value: d.hist, color: d.hist >= 0 ? '#22c55e' : '#ef4444' })));
    }

    // RSI
    if (indicators.rsi?.visible && sortedData[0]?.['RSI_14']) {
      const rsiData = sortedData.map(d => ({ time: d.date, value: d.RSI_14 })).filter(p => p.value);
      const rsiSeries = chart.addLineSeries({ color: '#fcd34d', lineWidth: 2, priceScaleId: 'rsi' });
      rsiSeries.setData(rsiData);
      rsiSeries.createPriceLine({ price: 70, color: '#ef4444', lineWidth: 1, lineStyle: 2, title: 'Overbought' });
      rsiSeries.createPriceLine({ price: 30, color: '#22c55e', lineWidth: 1, lineStyle: 2, title: 'Oversold' });
    }

    // --- Cấu hình layout động ---
    if (macdCreated && indicators.rsi?.visible) {
      chart.priceScale('right').applyOptions({ scaleMargins: { top: 0.1, bottom: 0.65 } });
      chart.priceScale('volume_scale').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 }, visible: false });
      chart.priceScale('macd').applyOptions({ scaleMargins: { top: 0.35, bottom: 0.35 } });
      chart.priceScale('rsi').applyOptions({ scaleMargins: { top: 0.7, bottom: 0.05 } });
    } else if (macdCreated) {
      chart.priceScale('right').applyOptions({ scaleMargins: { top: 0.1, bottom: 0.3 } });
      chart.priceScale('volume_scale').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 }, visible: false });
      chart.priceScale('macd').applyOptions({ scaleMargins: { top: 0.55, bottom: 0.15 } });
    } else if (indicators.rsi?.visible) {
      chart.priceScale('right').applyOptions({ scaleMargins: { top: 0.1, bottom: 0.3 } });
      chart.priceScale('volume_scale').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 }, visible: false });
      chart.priceScale('rsi').applyOptions({ scaleMargins: { top: 0.70, bottom: 0.15 } });
    } else {
      // Layout mặc định
      chart.priceScale('right').applyOptions({ scaleMargins: { top: 0.1, bottom: 0.3 } });
      chart.priceScale('volume_scale').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 }, visible: false });
    }

    // --- Hoàn thiện ---
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data, ticker, maLines, indicators]); // Phụ thuộc vào tất cả để vẽ lại khi cần

  return (
    <div style={{ width: '100%', maxWidth: 1200, margin: '0 auto', height: 400 }}>
      <div ref={chartContainerRef} style={{ position: 'relative', width: '100%', height: 400 }} />
    </div>
  );
};

export default StockChart;