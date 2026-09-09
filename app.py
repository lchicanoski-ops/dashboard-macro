import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Cenário Macro", layout="wide")

st.markdown("""
    <style>
        .stApp { background-color: #0E1117; color: #FFFFFF; }
    </style>
""", unsafe_allow_html=True)

st.title("CENÁRIO MACRO - PAINEL DE CORRELAÇÃO")

ADRS = ['VALE', 'PBR', 'ITUB', 'BBD', 'ABEV']
MOEDAS = {'6L=F': 'BRL (6L)', '6J=F': 'JPY (6J)', '6M=F': 'MXN (6M)', '6E=F': 'EUR (6E)', 'DX-Y.NYB': 'DXY'}
YIELDS = {'^TNX': 'US10Y', '^IRX': 'US2Y', '^FVX': 'US5Y', '^TYX': 'US30Y'}

@st.cache_data(ttl=60)
def carregar_dados_intraday(tickers):
    df = yf.download(tickers, period="1d", interval="1m")['Close']
    return df

todos_tickers = ADRS + list(MOEDAS.keys()) + list(YIELDS.keys())
dados = carregar_dados_intraday(todos_tickers)

# MOEDAS
st.subheader("Moedas & DXY (% Variação Intraday)")
fig_moedas = go.Figure()
for ticker, nome in MOEDAS.items():
    if ticker in dados.columns and not dados[ticker].dropna().empty:
        s = dados[ticker].dropna()
        ret = ((s / s.iloc[0]) - 1) * 100
        fig_moedas.add_trace(go.Scatter(x=ret.index, y=ret, mode='lines', name=nome))

fig_moedas.update_layout(template="plotly_dark", height=320, yaxis=dict(title="Variação %", zeroline=True))
st.plotly_chart(fig_moedas, use_container_width=True)

# YIELDS E METRICAS
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("US Treasury Yields (2Y, 5Y, 10Y, 30Y)")
    fig_yields = go.Figure()
    for ticker, nome in YIELDS.items():
        if ticker in dados.columns and not dados[ticker].dropna().empty:
            s = dados[ticker].dropna()
            ret = ((s / s.iloc[0]) - 1) * 100
            fig_yields.add_trace(go.Scatter(x=ret.index, y=ret, mode='lines', name=nome))
    fig_yields.update_layout(template="plotly_dark", height=300, yaxis=dict(title="Variação %"))
    st.plotly_chart(fig_yields, use_container_width=True)

with col2:
    st.subheader("Var. % Atual Yields")
    for ticker, nome in YIELDS.items():
        if ticker in dados.columns and not dados[ticker].dropna().empty:
            s = dados[ticker].dropna()
            var = ((s.iloc[-1] / s.iloc[0]) - 1) * 100
            st.metric(label=nome, value=f"{s.iloc[-1]:.3f}%", delta=f"{var:.2f}%")

# ADRS
st.subheader("ADRs Brasileiras (VALE, PBR, ITUB, BBD, ABEV)")
fig_adrs = go.Figure()
for ticker in ADRS:
    if ticker in dados.columns and not dados[ticker].dropna().empty:
        s = dados[ticker].dropna()
        ret = ((s / s.iloc[0]) - 1) * 100
        fig_adrs.add_trace(go.Scatter(x=ret.index, y=ret, mode='lines', name=ticker))

fig_adrs.update_layout(template="plotly_dark", height=320, yaxis=dict(title="Variação %"))
st.plotly_chart(fig_adrs, use_container_width=True)
