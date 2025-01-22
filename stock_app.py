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

# 스토캐스틱 오실레이터 계산 함수
def calculate_stochastic(data, period=14):
    high = data['High'].rolling(window=period).max()
    low = data['Low'].rolling(window=period).min()
    data['%K'] = (data['Close'] - low) / (high - low) * 100
    data['%D'] = data['%K'].rolling(window=3).mean()

# Streamlit 앱 제목
st.title("주식 데이터 분석 대시보드")

# 사용자 입력 받기
stock_codes = st.text_input("비교할 종목 코드를 입력하세요 (쉼표로 구분, 예: AAPL,MSFT,GOOG): ", "AAPL,MSFT,GOOG")
stock_codes = [code.strip() for code in stock_codes.split(",")]  # 쉼표로 구분하여 리스트로 변환
start_date = st.text_input("시작 날짜를 입력하세요 (예: 2023-01-01): ", "2023-01-01")
end_date = st.text_input("종료 날짜를 입력하세요 (예: 2023-12-31): ", "2023-12-31")

# 주가 데이터 가져오기
try:
    stock_data = yf.download(stock_codes, start=start_date, end=end_date, group_by='ticker')
except Exception as e:
    st.error(f"오류 발생: {e}")
    st.stop()

# 각 종목별로 데이터 처리
for code in stock_codes:
    # 종가, 고가, 저가 데이터를 데이터프레임으로 변환
    df = stock_data[code][['Close', 'High', 'Low']].copy()
    df.columns = ['Close', 'High', 'Low']  # 컬럼 이름 변경

    # 이동평균 계산 (20일, 50일)
    df['MA_20'] = df['Close'].rolling(window=20).mean()
    df['MA_50'] = df['Close'].rolling(window=50).mean()

    # 볼린저 밴드 계산
    df['Upper'] = df['MA_20'] + (df['Close'].rolling(window=20).std() * 2)
    df['Lower'] = df['MA_20'] - (df['Close'].rolling(window=20).std() * 2)

    # RSI 계산
    df['RSI'] = calculate_rsi(df)

    # 결측값 제거 (옵션)
    df = df.dropna()

    # MACD 계산
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # 스토캐스틱 오실레이터 계산
    calculate_stochastic(df)

    # 계산된 데이터를 stock_data에 저장
    stock_data[(code, 'MA_20')] = df['MA_20']
    stock_data[(code, 'MA_50')] = df['MA_50']
    stock_data[(code, 'Upper')] = df['Upper']
    stock_data[(code, 'Lower')] = df['Lower']
    stock_data[(code, 'RSI')] = df['RSI']
    stock_data[(code, 'MACD')] = df['MACD']
    stock_data[(code, 'Signal')] = df['Signal']
    stock_data[(code, '%K')] = df['%K']
    stock_data[(code, '%D')] = df['%D']

# 사용자에게 그래프 설정 입력 받기
st.sidebar.header("그래프 설정")
show_ma = st.sidebar.checkbox("이동평균선 표시", value=True)
show_bb = st.sidebar.checkbox("볼린저 밴드 표시", value=True)
show_rsi = st.sidebar.checkbox("RSI 표시", value=True)
show_macd = st.sidebar.checkbox("MACD 표시", value=True)
show_stochastic = st.sidebar.checkbox("스토캐스틱 오실레이터 표시", value=True)

# 그래프 그리기
fig, axes = plt.subplots(4, 1, figsize=(14, 20))  # 4개의 Subplot (세로로 배치)
axes = axes.flatten()  # 1차원 배열로 변환

# 색상 리스트 (각 티커마다 다른 색상 사용)
colors = ['darkblue', 'orange', 'green', 'purple', 'red']

# 주가 그래프
for i, code in enumerate(stock_codes):
    axes[0].plot(stock_data[code]['Close'], label=f"{code} Close", alpha=0.8, linewidth=2, color=colors[i])
    if show_ma:
        axes[0].plot(stock_data[(code, 'MA_20')], label=f"{code} 20일 이동평균", linestyle="--", linewidth=1.5, color=colors[i])
        axes[0].plot(stock_data[(code, 'MA_50')], label=f"{code} 50일 이동평균", linestyle="--", linewidth=1.5, color=colors[i])
    if show_bb:
        axes[0].plot(stock_data[(code, 'Upper')], label=f"{code} 상단 밴드", linestyle="--", linewidth=1.5, color=colors[i])
        axes[0].plot(stock_data[(code, 'Lower')], label=f"{code} 하단 밴드", linestyle="--", linewidth=1.5, color=colors[i])
        axes[0].fill_between(stock_data.index, stock_data[(code, 'Upper')], stock_data[(code, 'Lower')], color=colors[i], alpha=0.1)
axes[0].set_title("주가 및 이동평균선", fontproperties=font_prop)
axes[0].set_xlabel("날짜", fontproperties=font_prop)
axes[0].set_ylabel("주가 (USD)", fontproperties=font_prop)
axes[0].legend(prop=font_prop)

# MACD 그래프 (주가 흐름 추가)
if show_macd:
    for i, code in enumerate(stock_codes):
        axes[1].plot(stock_data[code]['Close'], label=f"{code} Close", alpha=0.3, linewidth=1, color=colors[i])
        axes[1].plot(stock_data[(code, 'MACD')], label=f"{code} MACD", linewidth=2, color=colors[i])
        axes[1].plot(stock_data[(code, 'Signal')], label=f"{code} Signal", linestyle="--", linewidth=1.5, color=colors[i])
    axes[1].set_title("MACD", fontproperties=font_prop)
    axes[1].set_xlabel("날짜", fontproperties=font_prop)
    axes[1].set_ylabel("MACD", fontproperties=font_prop)
    axes[1].legend(prop=font_prop)

# 스토캐스틱 오실레이터 그래프 (주가 흐름 추가)
if show_stochastic:
    for i, code in enumerate(stock_codes):
        axes[2].plot(stock_data[code]['Close'], label=f"{code} Close", alpha=0.3, linewidth=1, color=colors[i])
        axes[2].plot(stock_data[(code, '%K')], label=f"{code} %K", linewidth=2, color=colors[i])
        axes[2].plot(stock_data[(code, '%D')], label=f"{code} %D", linestyle="--", linewidth=1.5, color=colors[i])
    axes[2].axhline(80, linestyle="--", color="red", alpha=0.5)
    axes[2].axhline(20, linestyle="--", color="green", alpha=0.5)
    axes[2].set_title("스토캐스틱 오실레이터", fontproperties=font_prop)
    axes[2].set_xlabel("날짜", fontproperties=font_prop)
    axes[2].set_ylabel("%K / %D", fontproperties=font_prop)
    axes[2].legend(prop=font_prop)

# RSI 그래프 (주가 흐름 추가)
if show_rsi:
    for i, code in enumerate(stock_codes):
        axes[3].plot(stock_data[code]['Close'], label=f"{code} Close", alpha=0.3, linewidth=1, color=colors[i])
        axes[3].plot(stock_data[(code, 'RSI')], label=f"{code} RSI", linewidth=2, color=colors[i])
    axes[3].axhline(70, linestyle="--", color="red", alpha=0.5)
    axes[3].axhline(30, linestyle="--", color="green", alpha=0.5)
    axes[3].set_title("RSI", fontproperties=font_prop)
    axes[3].set_xlabel("날짜", fontproperties=font_prop)
    axes[3].set_ylabel("RSI", fontproperties=font_prop)
    axes[3].legend(prop=font_prop)

# Figure 표시
plt.tight_layout()
st.pyplot(fig)