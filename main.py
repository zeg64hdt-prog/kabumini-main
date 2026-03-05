import os, requests, pandas as pd, yfinance as yf, time
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=+9), 'JST')

def analyze_fundamentals(t_obj):
    score = 0
    try:
        info = t_obj.info
        if info.get('operatingMargins', 0) >= 0.10: score += 1
        per = info.get('trailingPE', 0)
        if per and 10 <= per <= 15: score += 1
        if info.get('returnOnEquity', 0) >= 0.08: score += 1
        if info.get('dividendYield', 0) >= 0.03: score += 1
        return "★" * score if score > 0 else ""
    except:
        return ""

def judge_stock(ticker_code, name):
    try:
        t_obj = yf.Ticker(f"{ticker_code}.T")
        data = t_obj.history(period="6mo", interval="1d")
        if data.empty or len(data) < 50: return None

        close = data['Close']
        p_now = float(close.iloc[-1])
        ma5 = close.rolling(5).mean()
        ma25 = close.rolling(25).mean()
        
        m5_n, m5_p = ma5.iloc[-1], ma5.iloc[-2]
        m25_n, m25_p = ma25.iloc[-1], ma25.iloc[-2]
        
        # フィルター：株価500円以上、乖離率5%以内
        dev = (p_now - m25_n) / m25_n
        if p_now < 500 or dev > 0.05: return None

        # ①【買サイン】ゴールデンクロス
        if m5_p <= m25_p and m5_n > m25_n:
            star = analyze_fundamentals(t_obj)
            return ("BUY", f"📈{star}{ticker_code} {name}({p_now:.0f}円)")

        # ②【警戒】デッドクロス
        if m5_p >= m25_p and m5_n < m25_n:
            return ("SELL", f"⚠️{ticker_code} {name}({p_now:.0f}円)")

        return None
    except:
        return None

def send_line(message):
    token, uid = os.environ.get('LINE_ACCESS_TOKEN'), os.environ.get('LINE_USER_ID')
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    for i in range(0, len(message), 4500):
        payload = {"to": uid, "messages": [{"type": "text", "text": message[i:i+4500]}]}
        requests.post(url, headers=headers, json=payload, timeout=20)
        time.sleep(1)

def main():
    if not os.path.exists("kabumini.csv"):
        print("CSV(kabumini.csv)が見つかりません"); return
    df = pd.read_csv("kabumini.csv", encoding='utf-8-sig')
    c_col = [c for c in df.columns if 'コード' in str(c) or 'Code' in str(c)][0]
    n_col = [c for c in df.columns if '銘柄' in str(c) or '名称' in str(c)][0]
    stocks = df[[c_col, n_col]].dropna().values.tolist()

    res = {"BUY":[], "SELL":[]}
    for i, (code, name) in enumerate(stocks):
        c = str(code).strip()[:4]
        if c.isdigit():
            out = judge_stock(c, str(name))
            if out: res[out[0]].append(out[1])
        if (i+1)%15 == 0: time.sleep(0.05)

    now_jst = datetime.now(JST)
    msg = f"📊 株ミニ：通常判定({now_jst.strftime('%m/%d %H:%M')})\n"
    msg += "【📈買い候補】\n" + ("\n".join(res["BUY"]) if res["BUY"] else "なし") + "\n\n"
    msg += "【⚠️警戒：出口】\n" + ("\n".join(res["SELL"]) if res["SELL"] else "なし")
    send_line(msg)

if __name__ == "__main__":
    main()
