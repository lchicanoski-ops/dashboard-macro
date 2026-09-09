import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Cenário Macro", layout="wide")

# Configuração de atualização automática a cada 60 segundos
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=60000, key="datarefresh")
except ImportError:
    pass

# ------------------------------------------------------------------
# CSS - Design Ultradenso
# ------------------------------------------------------------------
st.markdown("""
    <style>
        .stApp { background-color: #0E1117; color: #FFFFFF; }
        .block-container { padding-top: 0.5rem; padding-bottom: 0.5rem; padding-left: 1rem; padding-right: 1rem; }
        h1 { font-size: 1.1rem !important; margin-bottom: 0.1rem !important; }
        h2, h3, h6 { font-size: 0.82rem !important; margin-bottom: 0.1rem !important; margin-top: 0.1rem !important; }
        hr { margin: 0.2rem 0 !important; border-color: #222 !important; }
        div[data-testid="stVerticalBlock"] > div { gap: 0.1rem; }

        /* Tabela lateral ultracompacta com texto colado */
        .side-table {
            width: auto;
            border-collapse: collapse;
            font-size: 0.8rem;
            margin: 0 auto;
        }
        .side-table tr {
            border-bottom: 1px solid #1e2330;
        }
        .side-table td {
            padding: 3px 6px;
            font-weight: 600;
            white-space: nowrap;
        }
        .symbol-col { text-align: left; color: #e0e0e0; }
        .var-col { text-align: left; padding-left: 12px !important; }
        .positive { color: #26a69a; }
        .negative { color: #ef5350; }
    </style>
""", unsafe_allow_html=True)

st.title("CENÁRIO MACRO - PAINEL DE CORRELAÇÃO")

# Dicionários de Ativos
MOEDAS = {
    '6E=F': '6E1!',
    '6J=F': '6J1!',
    '6L=F': '6L1!',
    '6M=F': '6M1!',
}

CORES_MOEDAS_EXATAS = {
    '6E=F': '#1e50bc',
    '6J=F': '#d4c92a',
    '6L=F': '#1b8a2e',
    '6M=F': '#c87820',
    'DX-Y.NYB': '#dcdcdc'
}

YIELDS = {
    '^TYX': 'US30Y',
    '^ZT=F': 'US2Y',
    '^TNX': 'US10Y',
    '^FVX': 'US05Y'
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

CORES_YIELDS = ['#ef5350', '#26a69a', '#4fc3f7', '#ab47bc']

ALTURA_GRAFICO = 240
MARGEM_GRAFICO = dict(l=5, r=60, t=15, b=5)

# ------------------------------------------------------------------
# DADOS EM LOTE
# ------------------------------------------------------------------
@st.cache_data(ttl=60)
def carregar_dados_linha(tickers):
    df = yf.download(tickers, period="5d", interval="1h")['Close']
    return df

todos_linha = list(MOEDAS.keys()) + list(YIELDS.keys())
dados_linha = carregar_dados_linha(todos_linha)

@st.cache_data(ttl=60)
def obter_dados_diarios_lote(tickers):
    dados_info = {}
    try:
        df = yf.download(tickers, period="5d", interval="1d")['Close']
        for ticker in tickers:
            s = df[ticker].dropna() if ticker in df.columns else pd.Series()
            if len(s) >= 2:
                fechamento_anterior = s.iloc[-2]
                preco_atual = s.iloc[-1]
                var_pct = ((preco_atual / fechamento_anterior) - 1) * 100
                dados_info[ticker] = {
                    'preco': preco_atual,
                    'var_pct': var_pct
                }
    except Exception:
        pass
    return dados_info

todos_diarios = list(MOEDAS.keys()) + list(YIELDS.keys()) + list(ADRS.keys())
dados_var = obter_dados_diarios_lote(todos_diarios)

# Tabela Compacta
def renderizar_tabela_lateral(tickers_map, dados_dict):
    html = '<table class="side-table">'
    for ticker, nome in tickers_map.items():
        if ticker in dados_dict:
            info = dados_dict[ticker]
            var = info['var_pct']
            cor_classe = "positive" if var >= 0 else "negative"
            var_fmt = f"{var:+.2f}%"
            html += f'<tr><td class="symbol-col">{nome}</td><td class="var-col {cor_classe}">{var_fmt}</td></tr>'
    html += '</table>'
    return html

# Gráfico Customizado (Sem Gaps do Fim de Semana e Sem Rabiscos)
def grafico_com_variacao(tickers_nomes: dict, cores, var_dict: dict, mostrar_legenda: bool = False):
    fig = go.Figure()
    for i, (ticker, nome) in enumerate(tickers_nomes.items()):
        if ticker not in dados_linha.columns:
            continue
        
        # Tratamento do DXY e demais ativos
        s = dados_linha[ticker].dropna()
        if s.empty:
            continue
            
        # Ordena a série temporal e remove horários duplicados
        s = s.sort_index()
        s = s.loc[~s.index.duplicated(keep='first')]
        
        cor = cores.get(ticker, '#FFFFFF') if isinstance(cores, dict) else cores[i % len(cores)]

        ret = ((s / s.iloc[0]) - 1) * 100
        
        # Converte em texto APÓS a ordenação limpa
        datas_str = ret.index.strftime('%Y-%m-%d %H:%M')

        fig.add_trace(go.Scatter(
            x=datas_str, y=ret.values, mode='lines', name=nome,
            line=dict(color=cor, width=1.8),
        ))

        var_pct = var_dict.get(ticker, {}).get('var_pct')
        texto = f"{nome} {var_pct:+.2f}%" if var_pct is not None else nome

        fig.add_annotation(
            xref="paper", x=1.005, xanchor="left",
            yref="y", y=ret.iloc[-1], yanchor="middle",
            text=texto, showarrow=False,
            bgcolor=cor, font=dict(color="white", size=8),
            borderpad=2, align="left",
        )

    layout_args = dict(
        template="plotly_dark", 
        height=ALTURA_GRAFICO, 
        margin=MARGEM_GRAFICO,
        yaxis=dict(title=None, zeroline=True),
        xaxis=dict(type='category', showticklabels=False), # Mantém o formato anterior sem vácuo do FDS
        showlegend=mostrar_legenda
    )

    if mostrar_legenda:
        layout_args['legend'] = dict(
            yanchor="top", y=0.99, xanchor="left", x=0.01,
            bgcolor="rgba(0,0,0,0.4)", font=dict(size=8)
        )

    fig.update_layout(**layout_args)
    return fig

# ----------------------------------------------------
# SEÇÃO PRINCIPAL: GRÁFICOS LADO A LADO
# ----------------------------------------------------
col_esquerda, col_direita = st.columns(2, gap="medium")

# PAINEL 1: MOEDAS & DXY
with col_esquerda:
    st.markdown("###### Moedas & DXY (% Variação)")
    c_g1, c_t1 = st.columns([3, 1], gap="small")
    with c_g1:
        st.plotly_chart(
            grafico_com_variacao(MOEDAS, CORES_MOEDAS_EXATAS, dados_var, mostrar_legenda=True), 
            use_container_width=True
        )
    with c_t1:
        st.markdown("<h6 style='text-align: center;'>Moedas</h6>", unsafe_allow_html=True)
        st.markdown(renderizar_tabela_lateral(MOEDAS, dados_var), unsafe_allow_html=True)

# PAINEL 2: YIELDS
with col_direita:
    st.markdown("###### US Treasury Yields (% Variação)")
    c_g2, c_t2 = st.columns([3, 1], gap="small")
    with c_g2:
        st.plotly_chart(
            grafico_com_variacao(YIELDS, CORES_YIELDS, dados_var, mostrar_legenda=False), 
            use_container_width=True
        )
    with c_t2:
        st.markdown("<h6 style='text-align: center;'>Yields</h6>", unsafe_allow_html=True)
        st.markdown(renderizar_tabela_lateral(YIELDS, dados_var), unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ----------------------------------------------------
# SEÇÃO 3: ADRs BRASILEIRAS
# ----------------------------------------------------
st.markdown("###### ADRs Brasileiras (Variação Diária)")

tickers_adr = []
variacoes_adr = []
cores = []

for ticker in ADRS.keys():
    if ticker in dados_var:
        var = dados_var[ticker]['var_pct']
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
        textfont=dict(color='white', size=9)
    )
])

fig_adrs_bar.update_layout(
    template="plotly_dark",
    height=160,
    yaxis=dict(title=None, zeroline=True, zerolinecolor='white', zerolinewidth=1.5),
    xaxis=dict(title=None),
    margin=dict(l=5, r=5, t=15, b=5)
)

st.plotly_chart(fig_adrs_bar, use_container_width=True)

adrs_lista = list(ADRS.items())
linha1 = adrs_lista[:5]
linha2 = adrs_lista[5:]

cols1 = st.columns(5, gap="small")
for idx, (ticker, nome) in enumerate(linha1):
    with cols1[idx]:
        if ticker in dados_var:
            info = dados_var[ticker]
            st.metric(f"{ticker} ({nome})", f"US$ {info['preco']:.2f}", f"{info['var_pct']:+.2f}%")

cols2 = st.columns(5, gap="small")
for idx, (ticker, nome) in enumerate(linha2):
    with cols2[idx]:
        if ticker in dados_var:
            info = dados_var[ticker]
            st.metric(f"{ticker} ({nome})", f"US$ {info['preco']:.2f}", f"{info['var_pct']:+.2f}%")
