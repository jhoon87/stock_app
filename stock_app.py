import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import pandas as pd

# 폰트 캐시 재생성
try:
    fm._rebuild()
except AttributeError:
    pass

# 프로젝트 내 폰트 파일 경로
font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NanumBarunGothic.ttf')
print(f"폰트 파일 경로: {font_path}")  # 경로 출력하여 확인

# 폰트 설정
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['axes.unicode_minus'] = False

# RSI 계산 함수
def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Streamlit 앱 제목
st.title("주식 데이터 분석 대시보드")

# 사용자 입력 받기
stock_code = st.text_input("분석할 주식 코드를 입력하세요 (예: AAPL): ", "AAPL")
start_date = st.text_input("시작 날짜를 입력하세요 (예: 2023-01-01): ", "2023-01-01")
end_date = st.text_input("종료 날짜를 입력하세요 (예: 2023-12-31): ", "2023-12-31")

# 주가 데이터 가져오기
try:
    stock_data = yf.download(stock_code, start=start_date, end=end_date)
except Exception as e:
    st.error(f"오류 발생: {e}")
    st.stop()

# 멀티컬럼 구조를 단일 컬럼 구조로 변환
stock_data.columns = stock_data.columns.droplevel(1)  # 'Ticker' 레벨 제거

# 'Close' 컬럼만 선택
stock_data = stock_data[['Close']]

# 이동평균 계산 (20일, 50일)
stock_data['MA_20'] = stock_data['Close'].rolling(window=20).mean()
stock_data['MA_50'] = stock_data['Close'].rolling(window=50).mean()

# 볼린저 밴드 계산
stock_data['Upper'] = stock_data['MA_20'] + (stock_data['Close'].rolling(window=20).std() * 2)
stock_data['Lower'] = stock_data['MA_20'] - (stock_data['Close'].rolling(window=20).std() * 2)

# RSI 계산
stock_data['RSI'] = calculate_rsi(stock_data)

# 결측값 제거 (옵션)
stock_data = stock_data.dropna()

# MACD 계산
stock_data['EMA_12'] = stock_data['Close'].ewm(span=12, adjust=False).mean()
stock_data['EMA_26'] = stock_data['Close'].ewm(span=26, adjust=False).mean()
stock_data['MACD'] = stock_data['EMA_12'] - stock_data['EMA_26']
stock_data['Signal'] = stock_data['MACD'].ewm(span=9, adjust=False).mean()

# 스토캐스틱 오실레이터 계산
def calculate_stochastic(data, period=14):
    high = data['Close'].rolling(window=period).max()
    low = data['Close'].rolling(window=period).min()
    data['%K'] = (data['Close'] - low) / (high - low) * 100
    data['%D'] = data['%K'].rolling(window=3).mean()

calculate_stochastic(stock_data)

# 사용자에게 그래프 설정 입력 받기
st.sidebar.header("그래프 설정")
show_ma = st.sidebar.checkbox("이동평균선 표시", value=True)
show_bb = st.sidebar.checkbox("볼린저 밴드 표시", value=True)
show_rsi = st.sidebar.checkbox("RSI 표시", value=True)
show_macd = st.sidebar.checkbox("MACD 표시", value=True)
show_stochastic = st.sidebar.checkbox("스토캐스틱 오실레이터 표시", value=True)

# 그래프 그리기
fig, ax = plt.subplots(2, 2, figsize=(14, 12))

# 주가 그래프
ax[0, 0].plot(stock_data['Close'], label="종가", alpha=0.8, linewidth=2, color='darkblue')
if show_ma:
    ax[0, 0].plot(stock_data['MA_20'], label="20일 이동평균", linestyle="--", linewidth=1.5, color='orange')
    ax[0, 0].plot(stock_data['MA_50'], label="50일 이동평균", linestyle="--", linewidth=1.5, color='green')
if show_bb:
    ax[0, 0].plot(stock_data['Upper'], label="상단 밴드", linestyle="--", color="red", linewidth=1.5)
    ax[0, 0].plot(stock_data['Lower'], label="하단 밴드", linestyle="--", color="green", linewidth=1.5)
    ax[0, 0].fill_between(stock_data.index, stock_data['Upper'], stock_data['Lower'], color="lightgray", alpha=0.3)
ax[0, 0].set_title(f"{stock_code} 주가", fontproperties=font_prop)
ax[0, 0].set_xlabel("날짜", fontproperties=font_prop)
ax[0, 0].set_ylabel("주가 (USD)", fontproperties=font_prop)
ax[0, 0].legend(prop=font_prop)

# MACD 그래프
if show_macd:
    ax[0, 1].plot(stock_data['MACD'], label="MACD", color="blue")
    ax[0, 1].plot(stock_data['Signal'], label="Signal", color="orange")
    ax[0, 1].set_title("MACD", fontproperties=font_prop)
    ax[0, 1].set_xlabel("날짜", fontproperties=font_prop)
    ax[0, 1].set_ylabel("MACD", fontproperties=font_prop)
    ax[0, 1].legend(prop=font_prop)

# 스토캐스틱 오실레이터 그래프
if show_stochastic:
    ax[1, 0].plot(stock_data['%K'], label="%K", color="purple")
    ax[1, 0].plot(stock_data['%D'], label="%D", color="green")
    ax[1, 0].axhline(80, linestyle="--", color="red", alpha=0.5)
    ax[1, 0].axhline(20, linestyle="--", color="green", alpha=0.5)
    ax[1, 0].set_title("스토캐스틱 오실레이터", fontproperties=font_prop)
    ax[1, 0].set_xlabel("날짜", fontproperties=font_prop)
    ax[1, 0].set_ylabel("%K / %D", fontproperties=font_prop)
    ax[1, 0].legend(prop=font_prop)

# RSI 그래프
if show_rsi:
    ax[1, 1].plot(stock_data['RSI'], label="RSI", color="purple")
    ax[1, 1].axhline(70, linestyle="--", color="red", alpha=0.5)
    ax[1, 1].axhline(30, linestyle="--", color="green", alpha=0.5)
    ax[1, 1].set_title("RSI", fontproperties=font_prop)
    ax[1, 1].set_xlabel("날짜", fontproperties=font_prop)
    ax[1, 1].set_ylabel("RSI", fontproperties=font_prop)
    ax[1, 1].legend(prop=font_prop)

plt.tight_layout()
st.pyplot(fig)