import os, requests, pandas as pd, yfinance as yf, time
from datetime import datetime, timedelta, timezone

# 日本時間(JST)の設定
JST = timezone(timedelta(hours=+9), 'JST')

def analyze_fundamentals(t_obj):
    """財務5項目をチェックし、適合数をカウント（★印）"""
    score = 0
    try:
        info = t_obj.info
        if info.get('operatingMargins', 0) >= 0.10: score += 1      # 利益率10%以上
        per = info.get('trailingPE', 0)
        if per and 10 <= per <= 15: score += 1                      # PER10-15倍
        if info.get('returnOnEquity', 0) >= 0.08: score += 1        # ROE8%以上
        if info.get('dividendYield', 0) >= 0.03: score += 1         # 配当利回り3%以上
        return "★" * score if score > 0 else ""
    except:
        return ""

def judge_stock(ticker_code, name):
    try:
        t_obj = yf.Ticker(f"{ticker_code}.T")
        data = t_obj.history(period="6mo", interval="1d")
        if data.empty or len(data) < 50: return None

        close = data['Close']
        vol = data['Volume']
        p_now, p_pre = float(close.iloc[-1]), float(close.iloc[-2])
        ma5 = close.rolling(5).mean()
        ma25 = close.rolling(25).mean()
        
        m5_n, m5_p = ma5.iloc[-1], ma5.iloc[-2]
        m25_n, m25_p = ma25.iloc[-1], ma25.iloc[-2]
        
        # --- ① 買い判定（ローリスク・フィルター） ---
        dev = (p_now - m25_n) / m25_n
        if p_now >= 500 and dev <= 0.05: # 株価500円以上、25日線からの乖離5%以内
            if m5_p <= m25_p and m5_n > m25_n: # ゴールデンクロス
                star = analyze_fundamentals(t_obj)
                return ("BUY", f"📈{star}{ticker_code} {name}({p_now:.0f}円)")

        # --- ② 厳選警戒判定（高値下落 ＋ 出来高増 ＋ 1000円↑） ---
        # 5日線が25日線の下にある、またはデッドクロス発生
        if m5_n < m25_n:
            high_20 = close.tail(20).max() # 直近1ヶ月(20日)の最高値
            drop_rate = (high_20 - p_now) / high_20 # 高値からの下落率
            v_avg = vol.shift(1).rolling(5).mean().iloc[-1] # 直近5日平均出来高
            
            # 条件：株価1000円以上 且つ 高値から5%以上下落 且つ 出来高が平均の1.2倍(投げ売り)
            if p_now >= 1000 and drop_rate >= 0.05 and vol.iloc[-1] > v_avg * 1.2:
                # 本日デッドクロスした、あるいは強い下落トレンドの初動
                if m5_p >= m2
