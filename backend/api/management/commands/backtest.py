import pandas as pd
import numpy as np
import decimal
import matplotlib.pyplot as plt
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Stock, StockData
# === SỬA LỖI QUAN TRỌNG: IMPORT TRỰC TIẾP HÀM LOGIC, KHÔNG IMPORT COMMAND NỮA ===
from api.analysis_logic import run_analysis_on_data

# --- Cấu hình Backtest ---
INITIAL_CAPITAL = 100_000_000
MAX_HOLDING_PERIOD = 60
POSITION_SIZE = 0.10
BACKTEST_START_YEAR = 2021


class Command(BaseCommand):
    help = 'Runs a value-based portfolio backtest on the ADMRS algorithm.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== Bắt đầu Backtest Mô phỏng Danh mục Dựa trên Giá trị ==="))

        # --- Bước 1: Chuẩn bị Dữ liệu ---
        self.stdout.write("-> Bước 1: Đang tải dữ liệu...")
        all_data = StockData.objects.all().values('stock_id', 'date', 'open', 'high', 'low', 'close', 'volume')
        if not all_data.exists():
            self.stdout.write(self.style.WARNING("Không có dữ liệu để backtest."))
            return

        df_all = pd.DataFrame(list(all_data))
        df_all['date'] = pd.to_datetime(df_all['date'])

        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            df_all[col] = pd.to_numeric(df_all[col], errors='coerce', downcast='float')
        df_all = df_all.dropna(subset=numeric_cols)

        open_prices = df_all.pivot(index='date', columns='stock_id', values='open').ffill()
        close_prices = df_all.pivot(index='date', columns='stock_id', values='close').ffill()

        # --- Bước 2: Chạy Phân tích để lấy Tín hiệu ---
        self.stdout.write("-> Bước 2: Đang chạy ADMRS trên toàn bộ lịch sử để tạo tín hiệu...")

        # === SỬA LỖI QUAN TRỌNG: GỌI TRỰC TIẾP HÀM LOGIC ===
        signals_list = run_analysis_on_data(df_all, scan_full_history=True)

        if not signals_list:
            self.stdout.write(self.style.ERROR("Thuật toán ADMRS không tạo ra bất kỳ tín hiệu nào."))
            return

        signals_df = pd.DataFrame(signals_list).rename(columns={'stock_id': 'ticker'})
        signals_df['analysis_date'] = pd.to_datetime(signals_df['analysis_date'])
        signals_df.set_index('analysis_date', inplace=True)
        self.stdout.write(self.style.SUCCESS(f"-> Đã tạo thành công {len(signals_df)} tín hiệu mua tiềm năng."))

        # --- Bước 3: Khởi tạo Danh mục và Vòng lặp Backtest ---
        self.stdout.write("-> Bước 3: Đang khởi tạo danh mục và bắt đầu mô phỏng...")

        portfolio = {'cash': decimal.Decimal(str(INITIAL_CAPITAL)), 'holdings': {}}

        trading_days = close_prices[close_prices.index.year >= BACKTEST_START_YEAR].index
        if trading_days.empty:
            self.stdout.write(self.style.ERROR(f"Không có dữ liệu giao dịch từ năm {BACKTEST_START_YEAR} trở đi."))
            return
        self.stdout.write(f"Chu kỳ Backtest: từ {trading_days[0].date()} đến {trading_days[-1].date()}")

        portfolio_history = pd.Series(index=trading_days, dtype=float)

        for i in range(len(trading_days)):
            date = trading_days[i]

            current_holdings_value = sum(
                decimal.Decimal(str(data['shares'])) * decimal.Decimal(str(close_prices.loc[date, ticker]))
                for ticker, data in portfolio['holdings'].items()
                if ticker in close_prices.columns and not pd.isna(close_prices.loc[date, ticker])
            )
            total_value = portfolio['cash'] + current_holdings_value

            tickers_to_sell = []
            for ticker, trade_info in portfolio['holdings'].items():
                days_held = (date - trade_info['entry_date']).days
                current_price = decimal.Decimal(str(close_prices.loc[date, ticker]))

                exit_signal = False
                if current_price < trade_info['stop_loss']: exit_signal = True
                if current_price > trade_info['target_price']: exit_signal = True
                if days_held > MAX_HOLDING_PERIOD * 1.4: exit_signal = True

                if exit_signal and i + 1 < len(trading_days):
                    next_day_open_price = decimal.Decimal(str(open_prices.loc[trading_days[i + 1], ticker]))
                    if not pd.isna(next_day_open_price) and next_day_open_price > 0:
                        cash_received = trade_info['shares'] * next_day_open_price
                        portfolio['cash'] += cash_received
                        tickers_to_sell.append(ticker)

            for ticker in tickers_to_sell:
                if ticker in portfolio['holdings']: del portfolio['holdings'][ticker]

            last_signal_date = signals_df.index[signals_df.index < date].max()

            if pd.notna(last_signal_date):
                signals_to_act_on = signals_df.loc[last_signal_date]
                if isinstance(signals_to_act_on, pd.Series):
                    signals_to_act_on = pd.DataFrame([signals_to_act_on])

                amount_per_position = total_value * decimal.Decimal(str(POSITION_SIZE))

                for _, signal in signals_to_act_on.iterrows():
                    ticker = signal['ticker']
                    if ticker not in portfolio['holdings']:
                        buy_price = decimal.Decimal(str(open_prices.loc[date, ticker]))
                        if not pd.isna(buy_price) and buy_price > 0 and portfolio['cash'] >= amount_per_position:
                            shares_to_buy = amount_per_position // buy_price
                            if shares_to_buy > 0:
                                cost = shares_to_buy * buy_price
                                portfolio['cash'] -= cost
                                portfolio['holdings'][ticker] = {
                                    'shares': shares_to_buy, 'buy_price': buy_price, 'entry_date': date,
                                    'stop_loss': signal['stop_loss'], 'target_price': signal['target_price']
                                }
                                self.stdout.write(self.style.SUCCESS(
                                    f"\n  -> {date.date()}: MUA {shares_to_buy} {ticker} @ {buy_price}"))

            final_holdings_value = sum(
                decimal.Decimal(str(data['shares'])) * decimal.Decimal(str(close_prices.loc[date, ticker]))
                for ticker, data in portfolio['holdings'].items()
                if ticker in close_prices.columns and not pd.isna(close_prices.loc[date, ticker])
            )
            portfolio_history.loc[date] = float(portfolio['cash'] + final_holdings_value)

        # --- 4. Tính toán và In các Chỉ số Hiệu suất Nâng cao ---
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("KẾT QUẢ BACKTEST HOÀN TẤT"))
        self.stdout.write("=" * 50)

        portfolio_history = portfolio_history[portfolio_history > 0].dropna()
        if portfolio_history.empty:
            self.stdout.write(
                self.style.WARNING("Không có giao dịch nào được thực hiện, không thể tính toán hiệu suất."))
            return

        daily_returns = portfolio_history.pct_change()
        cumulative_returns = portfolio_history / INITIAL_CAPITAL

        total_days = len(portfolio_history)
        annualized_return = (cumulative_returns.iloc[-1] ** (252 / total_days) - 1) * 100
        annualized_volatility = daily_returns.std() * np.sqrt(252) * 100
        sharpe_ratio = (annualized_return / annualized_volatility) if annualized_volatility != 0 else 0

        rolling_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100

        calmar_ratio = (annualized_return / abs(max_drawdown)) if max_drawdown != 0 else 0

        self.stdout.write(f"Vốn ban đầu: {INITIAL_CAPITAL:,.0f} VNĐ")
        self.stdout.write(f"Giá trị cuối cùng: {portfolio_history.iloc[-1]:,.0f} VNĐ")
        self.stdout.write(f"Tổng lợi nhuận: {((cumulative_returns.iloc[-1] - 1) * 100):.2f}%")
        self.stdout.write(f"Lợi nhuận Trung bình Năm: {annualized_return:.2f}%")
        self.stdout.write(f"Độ biến động Trung bình Năm: {annualized_volatility:.2f}%")
        self.stdout.write(self.style.SUCCESS(f"Tỷ lệ Sharpe (Sharpe Ratio): {sharpe_ratio:.2f}"))
        self.stdout.write(self.style.WARNING(f"Mức sụt giảm Tối đa (Max Drawdown): {max_drawdown:.2f}%"))
        self.stdout.write(f"Tỷ lệ Calmar (Calmar Ratio): {calmar_ratio:.2f}")

        # --- 5. Vẽ Biểu đồ ---
        self.stdout.write("-> Đang vẽ biểu đồ tăng trưởng vốn (Equity Curve)...")
        plt.figure(figsize=(12, 6))
        cumulative_returns.plot(title='ADMRS - Portfolio Equity Curve', grid=True)
        plt.xlabel('Date')
        plt.ylabel('Cumulative Returns (1 = Vốn ban đầu)')
        plt.savefig('equity_curve.png')
        self.stdout.write(self.style.SUCCESS("Đã lưu biểu đồ vào file 'equity_curve.png'."))