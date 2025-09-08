import React, { useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';

// Hàm tính SMA (Moving Average)
function calculateSMA(data, period) {
  const result = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) continue;

    const sum = data
      .slice(i - period + 1, i + 1)
      .reduce((acc, d) => acc + parseFloat(d.Close), 0);

    result.push({
      time: data[i].date,
      value: Number((sum / period).toFixed(2)),
    });
  }
  return result;
}

const StockChart = ({ data, maLines = [], indicators = {} }) => {
  const chartContainerRef = useRef(null);

  useEffect(() => {
    if (!chartContainerRef.current || !data || data.length === 0) return;
    chartContainerRef.current.innerHTML = '';

    // Khởi tạo chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0f172a' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: '#1e293b' },
        horzLines: { color: '#1e293b' },
      },
      width: chartContainerRef.current.clientWidth || 900,
      height: 400,
      localization: { locale: 'en-US' },
    });

    // Trục
    chart.priceScale('right').applyOptions({ borderColor: '#475569', textColor: '#94a3b8' });
    chart.timeScale().applyOptions({ borderColor: '#475569', textColor: '#94a3b8' });

    // === Candlestick ===
    const candlestickData = data.map(d => ({
      time: d.date,
      open: parseFloat(d.Open),
      high: parseFloat(d.High),
      low: parseFloat(d.Low),
      close: parseFloat(d.Close),
    }));

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: 'rgba(34,197,94,0.8)',
      wickDownColor: 'rgba(239,68,68,0.8)',
      priceScaleId: 'right',
    });
    candleSeries.setData(candlestickData);

    // === Moving Averages ===
    // MA colors: MA20: #38bdf8, MA50: #a78bfa, MA200: #facc15
    const maColors = {
      20: '#38bdf8',
      50: '#a78bfa',
      200: '#facc15',
    };
    maLines.forEach((maLine) => {
      const maData = calculateSMA(data, maLine.period);
      const color = maColors[maLine.period] || '#38bdf8';
      const maSeries = chart.addLineSeries({
        color,
        lineWidth: 2,
        priceScaleId: 'right',
      });
      maSeries.setData(maData);
    });

    // === Bollinger Bands ===
    if (indicators.bbands && indicators.bbands.visible) {
      const bbandsData = data.map(d => ({
        time: d.date,
        upper: parseFloat(d['BBU_20_2.0']),
        middle: parseFloat(d['BBM_20_2.0']),
        lower: parseFloat(d['BBL_20_2.0']),
      }));

      const upper = chart.addLineSeries({ color: 'rgba(59,130,246,0.5)', lineWidth: 1, priceScaleId: 'right' }); // #3b82f6
      const middle = chart.addLineSeries({ color: 'rgba(59,130,246,0.5)', lineWidth: 1, lineStyle: 2, priceScaleId: 'right' });
      const lower = chart.addLineSeries({ color: 'rgba(59,130,246,0.5)', lineWidth: 1, priceScaleId: 'right' });

      upper.setData(bbandsData.map(d => ({ time: d.time, value: d.upper })));
      middle.setData(bbandsData.map(d => ({ time: d.time, value: d.middle })));
      lower.setData(bbandsData.map(d => ({ time: d.time, value: d.lower })));
    }

    // === RSI Indicator ===
    if (indicators.rsi && indicators.rsi.visible) {
      // B1: tạo series RSI trước
      const rsiSeries = chart.addLineSeries({
        color: '#fcd34d',
        lineWidth: 2,
        priceScaleId: 'rsi',
      });

      // B2: sau đó mới apply options cho scale 'rsi'
      chart.priceScale('rsi').applyOptions({
        scaleMargins: { top: 0.70, bottom: 0.15 },
      });

      // B3: dữ liệu RSI
      const rsiData = data
        .map(d => ({ time: d.date, value: Number(d.RSI_14) }))
        .filter(p => Number.isFinite(p.value));
      rsiSeries.setData(rsiData);

      // B4: các đường overbought / oversold
      rsiSeries.createPriceLine({
        price: 70,
        color: '#ef4444',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: 'Overbought',
      });
      rsiSeries.createPriceLine({
        price: 30,
        color: '#22c55e',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: 'Oversold',
      });

      // B5: thu nhỏ khung giá chính (candlestick) để chừa chỗ
      chart.priceScale('right').applyOptions({ scaleMargins: { top: 0, bottom: 0.30 } });
    }

    // === Volume ===
    const volumeData = data.map(d => ({
      time: d.date,
      value: parseInt(d.Volume, 10),
      color: parseFloat(d.Close) >= parseFloat(d.Open)
        ? 'rgba(22,163,74,0.6)'
        : 'rgba(220,38,38,0.6)',
    }));

    const volumeSeries = chart.addHistogramSeries({
      color: 'rgba(22,163,74,0.6)',
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });

    // Apply scale margins sau khi đã add series
    chart.priceScale('volume').applyOptions(
      indicators.rsi && indicators.rsi.visible
        ? { scaleMargins: { top: 0.85, bottom: 0 } } // nếu có RSI thì volume nằm dưới cùng
        : { scaleMargins: { top: 0.75, bottom: 0 } } // mặc định
    );

    volumeSeries.setData(volumeData);

    // Fit nội dung chart
    chart.timeScale().fitContent();

    // Resize khi thay đổi màn hình
    const handleResize = () => {
      chart.applyOptions({
        width: chartContainerRef.current.clientWidth || 900,
      });
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data, maLines, indicators]);

  return (
    <div style={{ width: '100%', maxWidth: 1200, margin: '0 auto', height: 400 }}>
      <div ref={chartContainerRef} style={{ position: 'relative', width: '100%', height: 400 }} />
    </div>
  );
};

export default StockChart;
