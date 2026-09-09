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

ADRS = {
    'VALE': 'Vale',
    'PBR': 'Petrobras',
    'ITUB': 'Itaú',
    'BBD': 'Bradesco',
    'ABEV': 'Ambev',
    'GGB': 'Gerdau',
    'CSAN': 'Cosan',
    'BAK': 'Braskem',
    'XP': 'XP Inc',
    'NU': 'Nubank'
}

MOEDAS = {'6L=F': 'BRL (6L)', '6J=F': 'JPY (6J)', '6M=F': 'MXN (6M)', '6E=F': 'EUR (6E)', 'DX-Y.NYB': 'DXY'}
YIELDS = {'^TNX': 'US10Y', '^IRX': 'US2Y', '^FVX': 'US5Y', '^TYX': 'US30Y'}

@st.cache_data(ttl=60)
def carregar_dados_intraday(tickers):
    # Puxa 5 dias para garantir que pegamos o fechamento de ontem e os dados de hoje
    df = yf.download(tickers, period="5d", interval="1m")['Close']
    return df

todos_tickers = list(ADRS.keys()) + list(MOEDAS.keys()) + list(YIELDS.keys())
dados = carregar_dados_intraday(todos_tickers)

# MOEDAS & DXY
st.subheader("Moedas & DXY (% Variação Intraday)")
fig_moedas = go.Figure()
for ticker, nome in MOEDAS.items():
    if ticker in dados.columns and not dados[ticker].dropna().empty:
        s = dados[ticker].dropna()
        ret = ((s / s.iloc[0]) - 1) * 100
        fig_moedas.add_trace(go.Scatter(x=ret.index, y=ret, mode='lines', name=nome))

fig_moedas.update_layout(template="plotly_dark", height=300, yaxis=dict(title="Variação %", zeroline=True))
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
    fig_yields.update_layout(template="plotly_dark", height=280, yaxis=dict(title="Variação %"))
    st.plotly_chart(fig_yields, use_container_width=True)

with col2:
    st.subheader("Var. % Atual Yields")
    for ticker, nome in YIELDS.items():
        if ticker in dados.columns and not dados[ticker].dropna().empty:
            s = dados[ticker].dropna()
            var = ((s.iloc[-1] / s.iloc[0]) - 1) * 100
            st.metric(label=nome, value=f"{s.iloc[-1]:.3f}%", delta=f"{var:.2f}%")

# ADRs EM CARDS (CALCULADO EM RELAÇÃO AO FECHAMENTO DE ONTEM)
st.subheader("ADRs Brasileiras (Variação Diária x Fechamento Anterior)")

@st.cache_data(ttl=60)
def obter_variacao_diaria_adrs(tickers):
    info_adrs = {}
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                fechamento_anterior = hist['Close'].iloc[-2]
                preco_atual = hist['Close'].iloc[-1]
                var_pct = ((preco_atual / fechamento_anterior) - 1) * 100
                info_adrs[ticker] = (preco_atual, var_pct)
        except:
            pass
    return info_adrs

dados_adrs = obter_variacao_diaria_adrs(list(ADRS.keys()))

adrs_lista = list(ADRS.items())
linha1 = adrs_lista[:5]
linha2 = adrs_lista[5:]

# Primeira linha
cols1 = st.columns(5)
for idx, (ticker, nome) in enumerate(linha1):
    with cols1[idx]:
        if ticker in dados_adrs:
            preco, var_pct = dados_adrs[ticker]
            st.metric(
                label=f"{ticker} ({nome})", 
                value=f"US$ {preco:.2f}", 
                delta=f"{var_pct:+.2f}%"
            )

st.write("")

# Segunda linha
cols2 = st.columns(5)
for idx, (ticker, nome) in enumerate(linha2):
    with cols2[idx]:
        if ticker in dados_adrs:
            preco, var_pct = dados_adrs[ticker]
            st.metric(
                label=f"{ticker} ({nome})", 
                value=f"US$ {preco:.2f}", 
                delta=f"{var_pct:+.2f}%"
            )
