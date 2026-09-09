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
        .block-container { padding-top: 1rem; padding-bottom: 1rem; }
        h1 { font-size: 1.25rem !important; margin-bottom: 0.3rem !important; }
        h2, h3 { font-size: 0.95rem !important; margin-bottom: 0.2rem !important; margin-top: 0.2rem !important; }
        [data-testid="stMetric"] {
            background-color: #161a25;
            border-radius: 6px;
            padding: 6px 8px;
            margin-bottom: 4px;
        }
        [data-testid="stMetricValue"] { font-size: 0.82rem !important; }
        [data-testid="stMetricLabel"] { font-size: 0.65rem !important; }
        [data-testid="stMetricDelta"] { font-size: 0.65rem !important; }
        hr { margin: 0.35rem 0 !important; border-color: #222 !important; }
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

# paletas de cor fixas (linha do grafico = cor do bloco de variacao)
CORES_MOEDAS = ['#4fc3f7', '#ffb300', '#26a69a', '#ab47bc', '#ef5350']
CORES_YIELDS = ['#ef5350', '#26a69a', '#4fc3f7', '#ab47bc']

# altura padrao dos graficos (compacto), com espaco extra a direita p/ os blocos de variacao
ALTURA_GRAFICO = 230
MARGEM_GRAFICO = dict(l=10, r=95, t=25, b=10)

# ------------------------------------------------------------------
# 1. DADOS PARA GRÁFICOS DE LINHA (MOEDAS E YIELDS)
#    -> 1h de intervalo, 10 dias de historico (menos "espremido")
# ------------------------------------------------------------------
@st.cache_data(ttl=300)
def carregar_dados_linha(tickers):
    df = yf.download(tickers, period="10d", interval="1h")['Close']
    return df

todos_linha = list(MOEDAS.keys()) + list(YIELDS.keys())
dados_linha = carregar_dados_linha(todos_linha)

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


def grafico_com_variacao(tickers_nomes: dict, cores: list, var_dict: dict):
    """Monta o grafico de linha com blocos coloridos de variacao % 'grudados'
    na frente/direita do grafico, alinhados com o ultimo valor de cada linha."""
    fig = go.Figure()
    for i, (ticker, nome) in enumerate(tickers_nomes.items()):
        if ticker not in dados_linha.columns:
            continue
        s = dados_linha[ticker].dropna()
        if s.empty:
            continue
        cor = cores[i % len(cores)]
        ret = ((s / s.iloc[0]) - 1) * 100
        fig.add_trace(go.Scatter(
            x=ret.index, y=ret, mode='lines', name=nome,
            line=dict(color=cor, width=2),
        ))

        # valor de variacao % (diaria) que vai aparecer no bloco colorido
        var_pct = var_dict.get(ticker, {}).get('var_pct')
        texto = f"{nome} {var_pct:+.2f}%" if var_pct is not None else nome

        fig.add_annotation(
            xref="paper", x=1.01, xanchor="left",
            yref="y", y=ret.iloc[-1], yanchor="middle",
            text=texto, showarrow=False,
            bgcolor=cor, font=dict(color="white", size=8),
            borderpad=2, align="left",
        )

    fig.update_layout(
        template="plotly_dark", height=ALTURA_GRAFICO, margin=MARGEM_GRAFICO,
        yaxis=dict(title=None, zeroline=True),
        showlegend=False,
    )
    return fig

# ----------------------------------------------------
# SEÇÃO 1: MOEDAS & DXY (LINHA)
# ----------------------------------------------------
col_m1, col_m2 = st.columns([2.8, 1], gap="small")

with col_m1:
    st.markdown("###### Moedas & DXY (% Variação - 1h / 10 dias)")
    st.plotly_chart(grafico_com_variacao(MOEDAS, CORES_MOEDAS, dados_moedas_var), use_container_width=True)

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
    st.markdown("###### US Treasury Yields - 2Y, 5Y, 10Y, 30Y (% Variação - 1h / 10 dias)")
    st.plotly_chart(grafico_com_variacao(YIELDS, CORES_YIELDS, dados_yields_var), use_container_width=True)

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

# Monta o gráfico de barras (mais estreito, ocupando ~70% da largura)
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

col_bar, col_vazia = st.columns([2.2, 1])
with col_bar:
    st.plotly_chart(fig_adrs_bar, use_container_width=True)
