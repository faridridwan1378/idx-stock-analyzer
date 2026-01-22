"""
IDX Stock Analyzer - V7 FIXED
Copyright © 2026 Farid Ridwan | farid.rdwan@gmail.com
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="IDX Market Review", page_icon="💰", layout="wide")

# ═══════════════════════════════════════════════════════════════════════════
# DAFTAR SAHAM (Dikurangi untuk mempercepat loading)
# ═══════════════════════════════════════════════════════════════════════════
IDX_STOCKS = {
    'BLUE_CHIP': ['BBCA', 'BBRI', 'BMRI', 'BBNI', 'TLKM', 'ASII', 'UNVR', 'ICBP', 'INDF', 'GGRM', 'KLBF', 'AMRT'],
    'LQ45': ['ADRO', 'ANTM', 'CPIN', 'EXCL', 'GOTO', 'ITMG', 'JSMR', 'MDKA', 'MEDC', 'PGAS', 'PTBA', 'SMGR', 'UNTR'],
    'BANKING': ['BBCA', 'BBRI', 'BMRI', 'BBNI', 'BRIS', 'MEGA'],
    'MINING': ['ADRO', 'ANTM', 'INCO', 'ITMG', 'PTBA', 'MEDC', 'HRUM'],
    'CONSUMER': ['UNVR', 'ICBP', 'INDF', 'MYOR', 'CPIN', 'SIDO', 'GGRM', 'KLBF'],
    'TECH': ['TLKM', 'ISAT', 'EXCL', 'GOTO', 'EMTK'],
    'PROPERTY': ['BSDE', 'CTRA', 'SMRA', 'PWON']
}

# Saham untuk market review (dikurangi agar lebih cepat)
MARKET_STOCKS = ['BBCA', 'BBRI', 'BMRI', 'BBNI', 'TLKM', 'ASII', 'UNVR', 'ICBP', 
                 'INDF', 'ADRO', 'ANTM', 'PTBA', 'GOTO', 'BUKA', 'ITMG', 'MEDC',
                 'CPIN', 'SMGR', 'KLBF', 'GGRM', 'EXCL', 'JSMR', 'BSDE', 'CTRA']

SECTOR_MAP = {
    'BBCA': 'BANKING', 'BBRI': 'BANKING', 'BMRI': 'BANKING', 'BBNI': 'BANKING',
    'TLKM': 'TECH', 'EXCL': 'TECH', 'GOTO': 'TECH', 'BUKA': 'TECH', 'ISAT': 'TECH',
    'ASII': 'AUTOMOTIVE', 'UNVR': 'CONSUMER', 'ICBP': 'CONSUMER', 'INDF': 'CONSUMER',
    'ADRO': 'MINING', 'ANTM': 'MINING', 'PTBA': 'MINING', 'ITMG': 'MINING', 'MEDC': 'MINING',
    'CPIN': 'CONSUMER', 'SMGR': 'BASIC', 'KLBF': 'HEALTHCARE', 'GGRM': 'CONSUMER',
    'JSMR': 'INFRA', 'BSDE': 'PROPERTY', 'CTRA': 'PROPERTY', 'EMTK': 'TECH'
}

PERIOD_OPTIONS = {
    '1mo': '1 Bulan', '3mo': '3 Bulan', '6mo': '6 Bulan',
    '1y': '1 Tahun', '2y': '2 Tahun', '5y': '5 Tahun',
    '10y': '10 Tahun', 'max': 'Maksimum'
}

# ═══════════════════════════════════════════════════════════════════════════
# FUNGSI FETCH DATA
# ═══════════════════════════════════════════════════════════════════════════
def get_single_stock(ticker, period="5d"):
    """Ambil data satu saham"""
    try:
        if not ticker.endswith('.JK'):
            ticker = f"{ticker}.JK"
        
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        
        if df.empty:
            return None
        
        # Handle timezone
        df = df.reset_index()
        df['Date'] = pd.to_datetime(df[df.columns[0]])
        if df['Date'].dt.tz is not None:
            df['Date'] = df['Date'].dt.tz_convert(None)
        df = df.set_index('Date')
        
        return df
    except:
        return None

def get_market_data_simple():
    """Ambil data market dengan cara sederhana"""
    results = []
    
    total = len(MARKET_STOCKS)
    progress = st.progress(0, text="Memulai...")
    
    for i, ticker in enumerate(MARKET_STOCKS):
        progress.progress((i + 1) / total, text=f"Mengambil {ticker}... ({i+1}/{total})")
        
        try:
            df = get_single_stock(ticker, "5d")
            
            if df is not None and len(df) >= 2:
                last_close = df['Close'].iloc[-1]
                prev_close = df['Close'].iloc[-2]
                change = ((last_close - prev_close) / prev_close) * 100
                volume = df['Volume'].iloc[-1]
                
                results.append({
                    'Ticker': ticker,
                    'Close': last_close,
                    'Prev_Close': prev_close,
                    'Change': change,
                    'Volume': volume,
                    'Sector': SECTOR_MAP.get(ticker, 'OTHER')
                })
        except Exception as e:
            st.warning(f"⚠️ Gagal ambil {ticker}: {str(e)[:50]}")
            continue
    
    progress.empty()
    
    if results:
        return pd.DataFrame(results)
    return pd.DataFrame()

def get_ihsg():
    """Ambil data IHSG"""
    try:
        stock = yf.Ticker("^JKSE")
        df = stock.history(period="5d")
        
        if df.empty or len(df) < 2:
            return None
        
        last = df['Close'].iloc[-1]
        prev = df['Close'].iloc[-2]
        change = ((last - prev) / prev) * 100
        
        return {
            'value': last,
            'change': change,
            'volume': df['Volume'].iloc[-1]
        }
    except:
        return None

# ═══════════════════════════════════════════════════════════════════════════
# FUNGSI ANALISIS SAHAM
# ═══════════════════════════════════════════════════════════════════════════
def add_indicators(df):
    """Tambah indikator teknikal"""
    if df is None or df.empty:
        return df
    
    df = df.copy()
    df['Returns'] = df['Close'].pct_change()
    df['Direction'] = (df['Returns'] > 0).astype(int)
    df['SMA_20'] = df['Close'].rolling(20, min_periods=1).mean()
    df['SMA_50'] = df['Close'].rolling(50, min_periods=1).mean()
    
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14, min_periods=1).mean()
    rs = gain / (loss + 0.0001)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    exp12 = df['Close'].ewm(span=12, adjust=False, min_periods=1).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False, min_periods=1).mean()
    df['MACD'] = exp12 - exp26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False, min_periods=1).mean()
    
    df['Vol_SMA'] = df['Volume'].rolling(20, min_periods=1).mean()
    df['Vol_Ratio'] = df['Volume'] / (df['Vol_SMA'] + 1)
    
    if isinstance(df.index, pd.DatetimeIndex):
        df['Year'] = df.index.year
    
    return df.ffill().bfill()

def analyze_stats(df):
    """Analisis statistik"""
    if df is None or df.empty or 'Returns' not in df.columns:
        return {}
    
    returns = df['Returns'].dropna()
    total = len(returns)
    if total == 0:
        return {}
    
    up = (returns > 0).sum()
    total_return = ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100
    years = max((df.index[-1] - df.index[0]).days / 365.25, 0.01)
    
    return {
        'basic': {
            'total_days': total,
            'up_days': int(up),
            'down_days': int(total - up),
            'prob_up': up / total,
            'prob_down': (total - up) / total,
            'total_return': total_return,
            'annualized_return': ((df['Close'].iloc[-1] / df['Close'].iloc[0]) ** (1/years) - 1) * 100,
            'years': years
        }
    }

def get_recommendation(df, stats):
    """Rekomendasi"""
    if df is None or len(df) < 2:
        return "❓ N/A", "❓", "#888", [], 0
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    score = 0
    signals = []
    
    # RSI
    rsi = last.get('RSI', 50)
    if rsi < 30:
        score += 3
        signals.append("🔥 RSI Oversold")
    elif rsi > 70:
        score -= 3
        signals.append("🛑 RSI Overbought")
    else:
        signals.append(f"⚪ RSI: {rsi:.0f}")
    
    # MACD
    macd = last.get('MACD', 0)
    macd_sig = last.get('MACD_Signal', 0)
    if macd > macd_sig:
        score += 2
        signals.append("🟢 MACD Bullish")
    else:
        score -= 2
        signals.append("🔴 MACD Bearish")
    
    # Trend
    close = last.get('Close', 0)
    sma20 = last.get('SMA_20', close)
    if close > sma20:
        score += 1
        signals.append("📈 > SMA20")
    else:
        score -= 1
        signals.append("📉 < SMA20")
    
    # Probability
    prob = stats.get('basic', {}).get('prob_up', 0.5) * 100
    signals.append(f"📊 Prob: {prob:.0f}%")
    
    if score >= 4:
        return "💎 STRONG BUY", "🚀", "#00C853", signals, score
    elif score >= 1:
        return "✅ BUY", "📈", "#4CAF50", signals, score
    elif score <= -4:
        return "🚨 STRONG SELL", "⛔", "#D50000", signals, score
    elif score <= -1:
        return "📉 SELL", "📉", "#FF5722", signals, score
    else:
        return "⏳ HOLD", "⚖️", "#607D8B", signals, score

# ═══════════════════════════════════════════════════════════════════════════
# FUNGSI CHART
# ═══════════════════════════════════════════════════════════════════════════
def plot_candlestick(df, ticker):
    """Candlestick chart"""
    if df is None or df.empty:
        return go.Figure()
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.03)
    
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], 
        low=df['Low'], close=df['Close'], name='OHLC'
    ), row=1, col=1)
    
    if 'SMA_20' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name='SMA20', line=dict(color='orange')), row=1, col=1)
    
    colors = ['red' if df['Close'].iloc[i] < df['Open'].iloc[i] else 'green' for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, opacity=0.7, name='Vol'), row=2, col=1)
    
    fig.update_layout(title=f'📈 {ticker}', height=500, template='plotly_dark', xaxis_rangeslider_visible=False)
    return fig

def plot_pie_chart(advancing, declining, unchanged):
    """Pie chart market breadth"""
    fig = go.Figure(data=[go.Pie(
        labels=['Naik', 'Turun', 'Tetap'],
        values=[advancing, declining, unchanged],
        marker_colors=['#00C853', '#FF5252', '#9E9E9E'],
        hole=0.4
    )])
    fig.update_layout(title='Market Breadth', height=300, template='plotly_dark')
    return fig

def plot_bar_chart(df, x_col, y_col, title, color):
    """Bar chart horizontal"""
    fig = go.Figure(go.Bar(
        x=df[y_col],
        y=df[x_col],
        orientation='h',
        marker_color=color,
        text=[f"{x:+.2f}%" for x in df[y_col]],
        textposition='outside'
    ))
    fig.update_layout(title=title, height=350, template='plotly_dark')
    return fig

# ═══════════════════════════════════════════════════════════════════════════
# HALAMAN MARKET REVIEW
# ═══════════════════════════════════════════════════════════════════════════
def page_market_review():
    st.header("📊 Market Review Harian")
    st.caption(f"📅 {datetime.now().strftime('%A, %d %B %Y')}")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown("---")
    
    # IHSG
    st.subheader("📈 IHSG (Indeks Harga Saham Gabungan)")
    ihsg = get_ihsg()
    if ihsg:
        col1, col2, col3 = st.columns(3)
        col1.metric("IHSG", f"{ihsg['value']:,.2f}", f"{ihsg['change']:+.2f}%")
        col2.metric("Status", "🟢 Naik" if ihsg['change'] > 0 else "🔴 Turun")
        col3.metric("Volume", f"{ihsg['volume']:,.0f}")
    else:
        st.warning("⚠️ Gagal mengambil data IHSG")
    
    st.markdown("---")
    
    # Market Data
    st.subheader("📊 Data Saham Hari Ini")
    
    market_df = get_market_data_simple()
    
    if market_df.empty:
        st.error("❌ Gagal mengambil data market. Coba refresh.")
        st.info("💡 Tips: Klik tombol Refresh atau tunggu beberapa saat")
        return
    
    st.success(f"✅ Berhasil mengambil data {len(market_df)} saham")
    
    # Market Breadth
    advancing = (market_df['Change'] > 0).sum()
    declining = (market_df['Change'] < 0).sum()
    unchanged = (market_df['Change'] == 0).sum()
    
    st.subheader("📊 Market Breadth")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🟢 Naik", advancing)
    col2.metric("🔴 Turun", declining)
    col3.metric("⚪ Tetap", unchanged)
    col4.metric("Ratio A/D", f"{advancing/max(declining,1):.2f}")
    
    fig = plot_pie_chart(advancing, declining, unchanged)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Top Gainers & Losers
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚀 Top Gainers")
        gainers = market_df.nlargest(5, 'Change')
        
        for _, row in gainers.iterrows():
            st.markdown(f"""
            <div style="background:#1a472a;padding:10px;border-radius:8px;margin:5px 0;">
                <b>{row['Ticker']}</b> | Rp {row['Close']:,.0f} | 
                <span style="color:#00ff00;">{row['Change']:+.2f}%</span>
            </div>
            """, unsafe_allow_html=True)
        
        fig = plot_bar_chart(gainers, 'Ticker', 'Change', '🚀 Top Gainers', '#00C853')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📉 Top Losers")
        losers = market_df.nsmallest(5, 'Change')
        
        for _, row in losers.iterrows():
            st.markdown(f"""
            <div style="background:#4a1a1a;padding:10px;border-radius:8px;margin:5px 0;">
                <b>{row['Ticker']}</b> | Rp {row['Close']:,.0f} | 
                <span style="color:#ff4444;">{row['Change']:+.2f}%</span>
            </div>
            """, unsafe_allow_html=True)
        
        fig = plot_bar_chart(losers, 'Ticker', 'Change', '📉 Top Losers', '#FF5252')
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Most Active
    st.subheader("💹 Most Active (Volume Tertinggi)")
    active = market_df.nlargest(5, 'Volume')
    
    for _, row in active.iterrows():
        change_color = "#00ff00" if row['Change'] > 0 else "#ff4444"
        st.markdown(f"""
        <div style="background:#1a1a2e;padding:10px;border-radius:8px;margin:5px 0;display:flex;justify-content:space-between;">
            <span><b>{row['Ticker']}</b></span>
            <span>Rp {row['Close']:,.0f}</span>
            <span style="color:{change_color};">{row['Change']:+.2f}%</span>
            <span>Vol: {row['Volume']:,.0f}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Sector Performance
    st.subheader("🏭 Sector Performance")
    sector_perf = market_df.groupby('Sector')['Change'].mean().reset_index()
    sector_perf = sector_perf.sort_values('Change', ascending=False)
    
    for _, row in sector_perf.iterrows():
        color = "#00C853" if row['Change'] > 0 else "#FF5252"
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;padding:8px;border-bottom:1px solid #333;">
            <span>{row['Sector']}</span>
            <span style="color:{color};">{row['Change']:+.2f}%</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Market Summary
    avg_change = market_df['Change'].mean()
    if avg_change > 1:
        sentiment, color = "🟢 BULLISH", "#00C853"
    elif avg_change < -1:
        sentiment, color = "🔴 BEARISH", "#FF5252"
    else:
        sentiment, color = "🟡 NEUTRAL", "#FFC107"
    
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:25px;border-radius:15px;text-align:center;margin:20px 0;">
        <h2 style="color:{color};margin:0;">{sentiment}</h2>
        <p style="margin:10px 0;">Avg Change: <b>{avg_change:+.2f}%</b></p>
        <p>🟢 {advancing} naik | 🔴 {declining} turun</p>
    </div>
    """, unsafe_allow_html=True)
    
    # All Data
    with st.expander("📋 Lihat Semua Data"):
        st.dataframe(market_df.sort_values('Change', ascending=False), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════
# HALAMAN ANALISIS SAHAM
# ═══════════════════════════════════════════════════════════════════════════
def page_stock_analysis():
    st.header("📈 Analisis Saham")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        method = st.radio("Input:", ["Pilih", "Ketik"], horizontal=True)
    
    with col2:
        if method == "Ketik":
            ticker = st.text_input("Kode:", "BBCA").upper().strip()
        else:
            cat = st.selectbox("Kategori:", list(IDX_STOCKS.keys()))
            ticker = st.selectbox("Saham:", IDX_STOCKS[cat])
    
    with col3:
        period = st.selectbox("Periode:", list(PERIOD_OPTIONS.keys()), 
                             format_func=lambda x: PERIOD_OPTIONS[x], index=4)
    
    if st.button("🔍 ANALISIS", use_container_width=True, type="primary"):
        if not ticker:
            st.error("Masukkan kode saham!")
            return
        
        with st.spinner(f"Mengambil data {ticker}..."):
            df = get_single_stock(ticker, period)
        
        if df is None or df.empty:
            st.error(f"❌ Gagal mengambil data {ticker}")
            return
        
        st.success(f"✅ {ticker} - {len(df)} hari data")
        
        df = add_indicators(df)
        stats = analyze_stats(df)
        status, icon, color, signals, score = get_recommendation(df, stats)
        
        # Recommendation Box
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{color},{color}88);padding:20px;border-radius:15px;text-align:center;color:white;margin:15px 0;">
            <h2 style="margin:0;">{icon} {status}</h2>
            <p>Score: <b>{score:+d}</b></p>
            <p>{' | '.join(signals)}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Metrics
        last = df.iloc[-1]
        basic = stats.get('basic', {})
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Harga", f"Rp {last['Close']:,.0f}")
        c2.metric("RSI", f"{last.get('RSI', 0):.0f}")
        c3.metric("Prob Naik", f"{basic.get('prob_up', 0)*100:.0f}%")
        c4.metric("Total Return", f"{basic.get('total_return', 0):+.1f}%")
        
        # Chart
        fig = plot_candlestick(df.tail(100), ticker)
        st.plotly_chart(fig, use_container_width=True)
        
        # Data
        with st.expander("📋 Data"):
            st.dataframe(df.tail(20), use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    with st.sidebar:
        st.image("https://raw.githubusercontent.com/faridridwan1378/varsha-catalog/main/gambar%20buah/gemini-2.5-flash-image-preview%20(nano-banana)_a_Create_an_ultra-real%20(3).png", use_container_width=True)
        st.markdown("---")
        
        page = st.radio("Menu:", ["📊 Market Review", "📈 Analisis Saham"])
        
        st.markdown("---")
        if st.button("🗑️ Clear Cache"):
            st.cache_data.clear()
            st.success("✅ Done!")
        
        st.markdown("---")
        st.caption("**v7.0** © 2026 Farid Ridwan")
        st.caption("📧 farid.rdwan@gmail.com")
    
    st.title("💰 IDX Stock Analyzer")
    
    if page == "📊 Market Review":
        page_market_review()
    else:
        page_stock_analysis()
    
    st.markdown("<hr><p style='text-align:center;color:#666;'>⚠️ Bukan saran investasi</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
