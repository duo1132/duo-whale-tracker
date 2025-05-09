import websocket
import json
import threading
import streamlit as st
from datetime import datetime
import time
import pandas as pd

log_data = []
ws_thread_started = False
USDT_MIN_AMOUNT = 100_000  # 최소 거래금액
MIN_VOLATILITY = 0.001     # 최소 가격 변동폭 (0.1%)
last_price = [0]           # 최근 가격 기록용

# 고래 감지 함수
def run_whale_detector(threshold):
    def on_message(ws, message):
     def on_message(ws, message):
    data = json.loads(message)
    price = float(data['p'])
    qty = float(data['q'])
    amount = price * qty
    is_buyer_maker = data['m']

    # 최근 가격 추적 → 변동성 계산
    last_price.append(price)
    if len(last_price) > 2:
        price_change = abs(last_price[-1] - last_price[-2]) / last_price[-2]
    else:
        price_change = 0

    # ✅ 고급 조건: 수량 + 금액 + 변동성 필터
    if qty >= threshold and amount >= USDT_MIN_AMOUNT and price_change >= MIN_VOLATILITY:
        direction = "🟢 매수" if is_buyer_maker else "🔴 매도"
        timestamp = datetime.now().strftime('%H:%M:%S')
        price_label = f"{price:,.2f} USDT에 {direction[2:]}"
        log_data.append({
            '시간': timestamp,
            '거래 방향': direction,
            '체결가': price_label,
            '수량': f"{qty:.2f} BTC",
            '금액': f"{amount:,.2f} USDT"
        })

    def start_ws():
        socket = "wss://stream.binance.com:9443/ws/btcusdt@trade"
        ws = websocket.WebSocketApp(socket, on_message=on_message)
        ws.run_forever()

    thread = threading.Thread(target=start_ws, daemon=True)
    thread.start()

# UI 설정
st.set_page_config(page_title="🐋 DUO 고래추적기", layout="wide")
st.title("🐋 DUO 고래추적기 (BTC/USDT)")

threshold = st.slider("⚙️ 감지 기준 (BTC 수량)", min_value=0.5, max_value=30.0, value=1.0, step=0.1)
start = st.button("🚀 감지 시작")

if start and not ws_thread_started:
    st.success(f"✅ 감지 시작됨! 기준: {threshold} BTC 이상 거래")
    ws_thread_started = True
    run_whale_detector(threshold)

# 👇 화면 2단 분할
left_col, right_col = st.columns([2, 3])  # 비율 조정 가능

# 왼쪽: 트레이딩뷰 차트 (Binance BTC/USDT)
with left_col:
    st.subheader("📊 실시간 BTC/USDT 차트")
    tradingview_embed = """
    <iframe src="https://www.tradingview.com/chart/?symbol=BINANCE:BTCUSDT" 
            width="100%" height="600" frameborder="0" allowfullscreen></iframe>
    """
    st.components.v1.html(tradingview_embed, height=600)

# 오른쪽: 고래 감지 결과 표시
with right_col:
    st.subheader("🐋 감지된 고래 거래 기록")
    table_placeholder = st.empty()

    while True:
        display_data = pd.DataFrame(log_data[-20:])
        table_placeholder.dataframe(display_data, use_container_width=True)
        time.sleep(1)

