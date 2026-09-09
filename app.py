import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="Cenário Macro", layout="wide")

# ------------------------------------------------------------------
# CSS - versao compacta (cards menores, menos espaco entre secoes)
# ------------------------------------------------------------------
st.markdown("""
    <style>
        .stApp { background-color: #0E1117; color: #FFFFFF; }

        /* reduz padding geral da pagina */
        .block-container { padding-top: 1rem; padding-bottom: 1rem; }

        /* titulos menores e com menos margem */
        h1 { font-size: 1.25rem !important; margin-bottom: 0.3rem !important; }
        h2, h3 { font-size: 0.95rem !important; margin-bottom: 0.2rem !important; margin-top: 0.2rem !important; }

        /* metric cards menores */
        [data-testid="stMetric"] {
            background-color: #161a25;
            border-radius: 6px;
            padding: 6px 8px;
            margin-bottom: 4px;
        }
        [data-testid="stMetricValue"] { font-size: 0.95rem !important; }
        [data-testid="stMetricLabel"] { font-size: 0.72rem !important; }
        [data-testid="stMetricDelta"] { font-size: 0.72rem !important; }

        /* divisorias mais finas e com menos espaco */
        hr { margin: 0.35rem 0 !important; border-color: #222 !important; }

        /* reduz espaco entre elementos verticais */
        div[data-testid="stVerticalBlock"] > div { gap: 0.35rem; }
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
    '^ZT=F': 'US2Y',   # obs: verificar esse ticker, ver nota no chat
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

# altura padrao dos graficos (compacto)
ALTURA_GRAFICO = 190
MARGEM_GRAFICO = dict(l=10, r=10, t=25, b=10)

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
col_m1, col_m2 = st.columns([2.8, 1], gap="small")

with col_m1:
    st.markdown("###### Moedas & DXY (% Variação Intraday)")
    fig_moedas = go.Figure()
    for ticker, nome in MOEDAS.items():
        if ticker in dados_intraday.columns and not dados_intraday[ticker].dropna().empty:
            s = dados_intraday[ticker].dropna()
            ret = ((s / s.iloc[0]) - 1) * 100
            fig_moedas.add_trace(go.Scatter(x=ret.index, y=ret, mode='lines', name=nome))

    fig_moedas.update_layout(
        template="plotly_dark", height=ALTURA_GRAFICO, margin=MARGEM_GRAFICO,
        yaxis=dict(title=None, zeroline=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, font=dict(size=9)),
    )
    st.plotly_chart(fig_moedas, use_container_width=True)

with col_m2:
    st.markdown("###### Var. % Moedas / DXY")
    itens = list(MOEDAS.items())
    for i in range(0, len(itens), 2):
        par = itens[i:i + 2]
        cols_par = st.columns(2, gap="small")
        for j, (ticker, nome) in enumerate(par):
            if ticker in dados_moedas_var:
                info = dados_moedas_var[ticker]
                with cols_par[j]:
                    st.metric(nome, f"{info['preco']:.4f}", f"{info['var_pct']:+.2f}%")

st.markdown("<hr>", unsafe_allow_html=True)

# ----------------------------------------------------
# SEÇÃO 2: US TREASURY YIELDS (LINHA)
# ----------------------------------------------------
col_y1, col_y2 = st.columns([2.8, 1], gap="small")

with col_y1:
    st.markdown("###### US Treasury Yields (2Y, 5Y, 10Y, 30Y)")
    fig_yields = go.Figure()
    for ticker, nome in YIELDS.items():
        if ticker in dados_intraday.columns and not dados_intraday[ticker].dropna().empty:
            s = dados_intraday[ticker].dropna()
            ret = ((s / s.iloc[0]) - 1) * 100
            fig_yields.add_trace(go.Scatter(x=ret.index, y=ret, mode='lines', name=nome))

    fig_yields.update_layout(
        template="plotly_dark", height=ALTURA_GRAFICO, margin=MARGEM_GRAFICO,
        yaxis=dict(title=None, zeroline=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, font=dict(size=9)),
    )
    st.plotly_chart(fig_yields, use_container_width=True)

with col_y2:
    st.markdown("###### Var. % Diária Yields")
    itens = list(YIELDS.items())
    for i in range(0, len(itens), 2):
        par = itens[i:i + 2]
        cols_par = st.columns(2, gap="small")
        for j, (ticker, nome) in enumerate(par):
            if ticker in dados_yields_var:
                info = dados_yields_var[ticker]
                with cols_par[j]:
                    st.metric(nome, f"{info['preco']:.3f}%", f"{info['var_pct']:+.2f}%")

st.markdown("<hr>", unsafe_allow_html=True)

# ----------------------------------------------------
# SEÇÃO 3: ADRs BRASILEIRAS (GRÁFICO DE BARRAS DE VARIAÇÃO %)
# ----------------------------------------------------
st.markdown("###### ADRs Brasileiras (Variação Diária)")

adrs_lista = list(ADRS.items())
linha1 = adrs_lista[:5]
linha2 = adrs_lista[5:]

cols1 = st.columns(5, gap="small")
for idx, (ticker, nome) in enumerate(linha1):
    with cols1[idx]:
        if ticker in dados_adrs_var:
            info = dados_adrs_var[ticker]
            st.metric(f"{ticker} ({nome})", f"US$ {info['preco']:.2f}", f"{info['var_pct']:+.2f}%")

cols2 = st.columns(5, gap="small")
for idx, (ticker, nome) in enumerate(linha2):
    with cols2[idx]:
        if ticker in dados_adrs_var:
            info = dados_adrs_var[ticker]
            st.metric(f"{ticker} ({nome})", f"US$ {info['preco']:.2f}", f"{info['var_pct']:+.2f}%")

# Monta o gráfico no estilo da imagem
tickers_adr = []
variacoes_adr = []
cores = []

for ticker in ADRS.keys():
    if ticker in dados_adrs_var:
        var = dados_adrs_var[ticker]['var_pct']
        tickers_adr.append(ticker)
        variacoes_adr.append(var)
        cores.append('#26a69a' if var >= 0 else '#ef5350')

fig_adrs_bar = go.Figure(data=[
    go.Bar(
        x=tickers_adr,
        y=variacoes_adr,
        marker_color=cores,
        text=[f"{v:+.2f}%" for v in variacoes_adr],
        textposition='outside',
        textfont=dict(color='white', size=10)
    )
])

fig_adrs_bar.update_layout(
    template="plotly_dark",
    height=220,
    yaxis=dict(title=None, zeroline=True, zerolinecolor='white', zerolinewidth=1.5),
    xaxis=dict(title=None),
    margin=dict(l=10, r=10, t=15, b=10)
)

st.plotly_chart(fig_adrs_bar, use_container_width=True)
