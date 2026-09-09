import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="Cenário Macro", layout="wide")

st.markdown("""
    <style>
        .stApp { background-color: #0E1117; color: #FFFFFF; }
    </style>
""", unsafe_allow_html=True)

st.title("CENÁRIO MACRO - PAINEL DE CORRELAÇÃO")

# Dicionários
MOEDAS = {
    '6L=F': 'BRL (6L)', 
    '6J=F': 'JPY (6J)', 
    '6M=F': 'MXN (6M)', 
    '6E=F': 'EUR (6E)', 
    'DX-Y.NYB': 'DXY'
}

YIELDS = {
    '^TNX': 'US10Y', 
    '^ZT=F': 'US2Y', 
    '^FVX': 'US5Y', 
    '^TYX': 'US30Y'
}

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

# 1. DADOS INTRADAY PARA GRÁFICOS DE LINHA (MOEDAS E YIELDS)
@st.cache_data(ttl=60)
def carregar_dados_intraday(tickers):
    df = yf.download(tickers, period="5d", interval="1m")['Close']
    return df

todos_intraday = list(MOEDAS.keys()) + list(YIELDS.keys())
dados_intraday = carregar_dados_intraday(todos_intraday)

# 2. DADOS DIÁRIOS PARA VARIAÇÃO % (COMPARADO AO FECHAMENTO DE ONTEM)
@st.cache_data(ttl=60)
def obter_dados_diarios(tickers):
    dados_info = {}
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                fechamento_anterior = hist['Close'].iloc[-2]
                preco_atual = hist['Close'].iloc[-1]
                var_pct = ((preco_atual / fechamento_anterior) - 1) * 100
                dados_info[ticker] = {
                    'preco': preco_atual,
                    'var_pct': var_pct
                }
        except:
            pass
    return dados_info

dados_moedas_var = obter_dados_diarios(list(MOEDAS.keys()))
dados_yields_var = obter_dados_diarios(list(YIELDS.keys()))
dados_adrs_var = obter_dados_diarios(list(ADRS.keys()))

# ----------------------------------------------------
# SEÇÃO 1: MOEDAS & DXY (LINHA)
# ----------------------------------------------------
col_m1, col_m2 = st.columns([2.5, 1])

with col_m1:
    st.subheader("Moedas & DXY (% Variação Intraday)")
    fig_moedas = go.Figure()
    for ticker, nome in MOEDAS.items():
        if ticker in dados_intraday.columns and not dados_intraday[ticker].dropna().empty:
            s = dados_intraday[ticker].dropna()
            ret = ((s / s.iloc[0]) - 1) * 100
            fig_moedas.add_trace(go.Scatter(x=ret.index, y=ret, mode='lines', name=nome))
    
    fig_moedas.update_layout(template="plotly_dark", height=300, yaxis=dict(title="Variação %", zeroline=True))
    st.plotly_chart(fig_moedas, use_container_width=True)

with col_m2:
    st.subheader("Var. % Moedas / DXY")
    for ticker, nome in MOEDAS.items():
        if ticker in dados_moedas_var:
            info = dados_moedas_var[ticker]
            st.metric(
                label=nome, 
                value=f"{info['preco']:.4f}", 
                delta=f"{info['var_pct']:+.2f}%"
            )

st.divider()

# ----------------------------------------------------
# SEÇÃO 2: US TREASURY YIELDS (LINHA)
# ----------------------------------------------------
col_y1, col_y2 = st.columns([2.5, 1])

with col_y1:
    st.subheader("US Treasury Yields (2Y, 5Y, 10Y, 30Y)")
    fig_yields = go.Figure()
    for ticker, nome in YIELDS.items():
        if ticker in dados_intraday.columns and not dados_intraday[ticker].dropna().empty:
            s = dados_intraday[ticker].dropna()
            ret = ((s / s.iloc[0]) - 1) * 100
            fig_yields.add_trace(go.Scatter(x=ret.index, y=ret, mode='lines', name=nome))
            
    fig_yields.update_layout(template="plotly_dark", height=300, yaxis=dict(title="Variação % Intraday", zeroline=True))
    st.plotly_chart(fig_yields, use_container_width=True)

with col_y2:
    st.subheader("Var. % Diária Yields")
    for ticker, nome in YIELDS.items():
        if ticker in dados_yields_var:
            info = dados_yields_var[ticker]
            st.metric(
                label=nome, 
                value=f"{info['preco']:.3f}%", 
                delta=f"{info['var_pct']:+.2f}%"
            )

st.divider()

# ----------------------------------------------------
# SEÇÃO 3: ADRs BRASILEIRAS (GRÁFICO DE BARRAS DE VARIAÇÃO %)
# ----------------------------------------------------
st.subheader("ADRs Brasileiras (Variação Diária)")

# Cards Superiores
adrs_lista = list(ADRS.items())
linha1 = adrs_lista[:5]
linha2 = adrs_lista[5:]

cols1 = st.columns(5)
for idx, (ticker, nome) in enumerate(linha1):
    with cols1[idx]:
        if ticker in dados_adrs_var:
            info = dados_adrs_var[ticker]
            st.metric(label=f"{ticker} ({nome})", value=f"US$ {info['preco']:.2f}", delta=f"{info['var_pct']:+.2f}%")

cols2 = st.columns(5)
for idx, (ticker, nome) in enumerate(linha2):
    with cols2[idx]:
        if ticker in dados_adrs_var:
            info = dados_adrs_var[ticker]
            st.metric(label=f"{ticker} ({nome})", value=f"US$ {info['preco']:.2f}", delta=f"{info['var_pct']:+.2f}%")

st.write("")

# Monta o gráfico no estilo da imagem
tickers_adr = []
variacoes_adr = []
cores = []

for ticker in ADRS.keys():
    if ticker in dados_adrs_var:
        var = dados_adrs_var[ticker]['var_pct']
        tickers_adr.append(ticker)
        variacoes_adr.append(var)
        # Verde se positivo/zero, Vermelho se negativo
        cores.append('#26a69a' if var >= 0 else '#ef5350')

fig_adrs_bar = go.Figure(data=[
    go.Bar(
        x=tickers_adr,
        y=variacoes_adr,
        marker_color=cores,
        text=[f"{v:+.2f}%" for v in variacoes_adr],
        textposition='outside',
        textfont=dict(color='white', size=12)
    )
])

fig_adrs_bar.update_layout(
    template="plotly_dark",
    height=350,
    yaxis=dict(
        title="Variação %", 
        zeroline=True, 
        zerolinecolor='white', 
        zerolinewidth=1.5
    ),
    xaxis=dict(title="ADRs"),
    margin=dict(l=20, r=20, t=30, b=20)
)

st.plotly_chart(fig_adrs_bar, use_container_width=True)
