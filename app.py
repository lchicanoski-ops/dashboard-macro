import streamlit as st
import yfinance as yf
import pandas as pd
import requests
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

# ------------------------------------------------------------------
# Configuração da API da Twelve Data
# ------------------------------------------------------------------
st.sidebar.header("Configuração")
TD_API_KEY = st.secrets.get("TWELVE_DATA_API_KEY", "") if hasattr(st, "secrets") else ""
if not TD_API_KEY:
    TD_API_KEY = st.sidebar.text_input(
        "Twelve Data API Key", type="password",
        help="Crie gratis em twelvedata.com (plano Basic/free)."
    )
if not TD_API_KEY:
    st.warning("Cole sua API Key da Twelve Data na barra lateral (ou configure em Secrets) para carregar Moedas e ADRs.")

TD_BASE = "https://api.twelvedata.com"

# ------------------------------------------------------------------
# Dicionários
# ------------------------------------------------------------------
# Moedas: a Twelve Data (free) nao tem os futuros da CME (6L/6M/6J/6E),
# entao usamos o par a vista (spot) equivalente.
MOEDAS_TD = {
    'USD/BRL': 'BRL (6L)',
    'USD/JPY': 'JPY (6J)',
    'USD/MXN': 'MXN (6M)',
    'EUR/USD': 'EUR (6E)',
}
# DXY (indice) nao esta disponivel no plano free da Twelve Data -> mantido via Yahoo
DXY_TICKER_YAHOO = 'DX-Y.NYB'

# Yields continuam no Yahoo: nem Twelve Data nem Alpha Vantage (free) cobrem
# yield de titulo do tesouro de forma direta e confiavel.
YIELDS = {
    '^TNX': 'US10Y',
    '^ZT=F': 'US2Y',   # obs: verificar esse ticker, ver nota no chat
    '^FVX': 'US5Y',
    '^TYX': 'US30Y'
}

# ADRs: cobertas em açoes americanas no plano free da Twelve Data
ADRS_TD = {
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

ALTURA_GRAFICO = 230
MARGEM_GRAFICO = dict(l=10, r=95, t=25, b=10)

# ------------------------------------------------------------------
# Funções Twelve Data (em lote, pra economizar chamadas/minuto do free tier)
# ------------------------------------------------------------------
@st.cache_data(ttl=300)
def td_time_series_batch(symbols: list, api_key: str, interval: str = "1h", outputsize: int = 240):
    resultado = {}
    if not api_key or not symbols:
        return resultado
    try:
        r = requests.get(f"{TD_BASE}/time_series", params={
            "symbol": ",".join(symbols), "interval": interval,
            "outputsize": outputsize, "apikey": api_key,
        }, timeout=15)
        data = r.json()
        if len(symbols) == 1:
            data = {symbols[0]: data}
        for sym in symbols:
            bloco = data.get(sym, {})
            valores = bloco.get("values")
            if not valores:
                continue
            df = pd.DataFrame(valores)
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.sort_values("datetime").set_index("datetime")
            df["close"] = df["close"].astype(float)
            resultado[sym] = df["close"]
    except Exception:
        pass
    return resultado

@st.cache_data(ttl=60)
def td_quote_batch(symbols: list, api_key: str):
    resultado = {}
    if not api_key or not symbols:
        return resultado
    try:
        r = requests.get(f"{TD_BASE}/quote", params={
            "symbol": ",".join(symbols), "apikey": api_key,
        }, timeout=15)
        data = r.json()
        if len(symbols) == 1:
            data = {symbols[0]: data}
        for sym in symbols:
            bloco = data.get(sym, {})
            if "close" not in bloco:
                continue
            resultado[sym] = {
                "preco": float(bloco["close"]),
                "var_pct": float(bloco.get("percent_change", 0)),
            }
    except Exception:
        pass
    return resultado

# ------------------------------------------------------------------
# Funções Yahoo (ainda usadas para Yields e DXY)
# ------------------------------------------------------------------
@st.cache_data(ttl=300)
def carregar_dados_linha_yahoo(tickers):
    df = yf.download(tickers, period="10d", interval="1h")['Close']
    return df

@st.cache_data(ttl=60)
def obter_dados_diarios_yahoo(tickers):
    dados_info = {}
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                fechamento_anterior = hist['Close'].iloc[-2]
                preco_atual = hist['Close'].iloc[-1]
                var_pct = ((preco_atual / fechamento_anterior) - 1) * 100
                dados_info[ticker] = {'preco': preco_atual, 'var_pct': var_pct}
        except Exception:
            pass
    return dados_info

# ------------------------------------------------------------------
# Coleta MOEDAS (Twelve Data + DXY via Yahoo)
# ------------------------------------------------------------------
moedas_symbols = list(MOEDAS_TD.keys())
ts_moedas = td_time_series_batch(moedas_symbols, TD_API_KEY)
q_moedas = td_quote_batch(moedas_symbols, TD_API_KEY)

dados_linha_moedas = {MOEDAS_TD[sym]: serie for sym, serie in ts_moedas.items()}
dados_moedas_var = {MOEDAS_TD[sym]: info for sym, info in q_moedas.items()}

dxy_linha_df = carregar_dados_linha_yahoo([DXY_TICKER_YAHOO])
dxy_serie = dxy_linha_df[DXY_TICKER_YAHOO].dropna() if DXY_TICKER_YAHOO in getattr(dxy_linha_df, "columns", []) else pd.Series(dtype=float)
if not dxy_serie.empty:
    dados_linha_moedas['DXY'] = dxy_serie
dxy_var = obter_dados_diarios_yahoo([DXY_TICKER_YAHOO])
if DXY_TICKER_YAHOO in dxy_var:
    dados_moedas_var['DXY'] = dxy_var[DXY_TICKER_YAHOO]

nomes_moedas_ordem = list(MOEDAS_TD.values()) + ['DXY']

# ------------------------------------------------------------------
# Coleta YIELDS (continua no Yahoo)
# ------------------------------------------------------------------
dados_linha_yields_raw = carregar_dados_linha_yahoo(list(YIELDS.keys()))
dados_yields_var_ticker = obter_dados_diarios_yahoo(list(YIELDS.keys()))

dados_linha_yields = {}
for ticker, nome in YIELDS.items():
    if ticker in getattr(dados_linha_yields_raw, "columns", []):
        s = dados_linha_yields_raw[ticker].dropna()
        if not s.empty:
            dados_linha_yields[nome] = s
dados_yields_var = {YIELDS[t]: info for t, info in dados_yields_var_ticker.items() if t in YIELDS}

# ------------------------------------------------------------------
# Coleta ADRs (Twelve Data)
# ------------------------------------------------------------------
dados_adrs_var = td_quote_batch(list(ADRS_TD.keys()), TD_API_KEY)


def grafico_com_variacao(series_dict: dict, cores: list, var_dict: dict):
    """Monta o grafico de linha com blocos coloridos de variacao % 'grudados'
    na frente/direita do grafico, alinhados com o ultimo valor de cada linha."""
    fig = go.Figure()
    for i, (nome, s) in enumerate(series_dict.items()):
        s = s.dropna()
        if s.empty:
            continue
        cor = cores[i % len(cores)]
        ret = ((s / s.iloc[0]) - 1) * 100
        fig.add_trace(go.Scatter(
            x=ret.index, y=ret, mode='lines', name=nome,
            line=dict(color=cor, width=2),
        ))

        var_pct = var_dict.get(nome, {}).get('var_pct')
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
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    return fig

# ----------------------------------------------------
# SEÇÃO 1: MOEDAS & DXY (LINHA)
# ----------------------------------------------------
col_m1, col_m2 = st.columns([2.8, 1], gap="small")

with col_m1:
    st.markdown("###### Moedas & DXY (% Variação - 1h / 10 dias) — via Twelve Data + Yahoo (DXY)")
    st.plotly_chart(grafico_com_variacao(dados_linha_moedas, CORES_MOEDAS, dados_moedas_var), use_container_width=True)

with col_m2:
    st.markdown("###### Var. % Moedas / DXY")
    for i in range(0, len(nomes_moedas_ordem), 2):
        par = nomes_moedas_ordem[i:i + 2]
        cols_par = st.columns(2, gap="small")
        for j, nome in enumerate(par):
            info = dados_moedas_var.get(nome)
            with cols_par[j]:
                if info:
                    st.metric(nome, f"{info['preco']:.4f}", f"{info['var_pct']:+.2f}%")
                else:
                    st.metric(nome, "-")

st.markdown("<hr>", unsafe_allow_html=True)

# ----------------------------------------------------
# SEÇÃO 2: US TREASURY YIELDS (LINHA)
# ----------------------------------------------------
col_y1, col_y2 = st.columns([2.8, 1], gap="small")

with col_y1:
    st.markdown("###### US Treasury Yields - 2Y, 5Y, 10Y, 30Y (% Variação - 1h / 10 dias) — via Yahoo")
    st.plotly_chart(grafico_com_variacao(dados_linha_yields, CORES_YIELDS, dados_yields_var), use_container_width=True)

with col_y2:
    st.markdown("###### Var. % Diária Yields")
    nomes_yields_ordem = list(YIELDS.values())
    for i in range(0, len(nomes_yields_ordem), 2):
        par = nomes_yields_ordem[i:i + 2]
        cols_par = st.columns(2, gap="small")
        for j, nome in enumerate(par):
            info = dados_yields_var.get(nome)
            with cols_par[j]:
                if info:
                    st.metric(nome, f"{info['preco']:.3f}%", f"{info['var_pct']:+.2f}%")
                else:
                    st.metric(nome, "-")

st.markdown("<hr>", unsafe_allow_html=True)

# ----------------------------------------------------
# SEÇÃO 3: ADRs BRASILEIRAS (GRÁFICO DE BARRAS + COTAÇÕES) — via Twelve Data
# ----------------------------------------------------
st.markdown("###### ADRs Brasileiras (Variação Diária) — via Twelve Data")

tickers_adr = []
variacoes_adr = []
cores = []

for ticker in ADRS_TD.keys():
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

adrs_lista = list(ADRS_TD.items())
linha1 = adrs_lista[:5]
linha2 = adrs_lista[5:]

cols1 = st.columns(5, gap="small")
for idx, (ticker, nome) in enumerate(linha1):
    with cols1[idx]:
        info = dados_adrs_var.get(ticker)
        if info:
            st.metric(f"{ticker} ({nome})", f"US$ {info['preco']:.2f}", f"{info['var_pct']:+.2f}%")
        else:
            st.metric(f"{ticker} ({nome})", "-")

cols2 = st.columns(5, gap="small")
for idx, (ticker, nome) in enumerate(linha2):
    with cols2[idx]:
        info = dados_adrs_var.get(ticker)
        if info:
            st.metric(f"{ticker} ({nome})", f"US$ {info['preco']:.2f}", f"{info['var_pct']:+.2f}%")
        else:
            st.metric(f"{ticker} ({nome})", "-")
