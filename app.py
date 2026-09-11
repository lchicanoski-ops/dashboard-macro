import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

st.set_page_config(page_title="Cenário Macro Pro", layout="wide")

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
        .block-container { padding-top: 0.5rem; padding-bottom: 0.5rem; padding-left: 0.8rem; padding-right: 0.8rem; }
        h1 { font-size: 1.0rem !important; margin-bottom: 0.2rem !important; color: #E0E0E0; }
        h6 { font-size: 0.80rem !important; margin-bottom: 0.2rem !important; margin-top: 0.2rem !important; font-weight: 600; }
        hr { margin: 0.3rem 0 !important; border-color: #222 !important; }
        
        .side-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.78rem;
        }
        .side-table tr { border-bottom: 1px solid #1e2330; }
        .side-table td { padding: 2px 4px; font-weight: 600; white-space: nowrap; }
        .symbol-col { text-align: left; color: #B0BEC5; }
        .var-col { text-align: right; }
        .positive { color: #26a69a; }
        .negative { color: #ef5350; }
    </style>
""", unsafe_allow_html=True)

st.title("CENÁRIO MACRO - PAINEL DE CORRELAÇÃO DE MERCADO")

# ------------------------------------------------------------------
# DICIONÁRIOS DE ATIVOS
# ------------------------------------------------------------------
MOEDAS = {
    '6E=F': 'EUR/USD (6E)',
    '6J=F': 'JPY/USD (6J)',
    '6L=F': 'BRL/USD (6L)',
    '6M=F': 'MXN/USD (6M)',
    'DX=F': 'DXY'
}

CORES_MOEDAS_EXATAS = {
    '6E=F': '#1e50bc',
    '6J=F': '#d4c92a',
    '6L=F': '#1b8a2e',
    '6M=F': '#c87820',
    'DX=F': '#dcdcdc'
}

YIELDS = {
    '^TYX': 'US30Y',
    '^TNX': 'US10Y',
    '^FVX': 'US05Y',
    '^ZT=F': 'US02Y'
}

COMMODITIES_RISCO = {
    'EWZ': 'EWZ',
    '^VIX': 'VIX',
    'CL=F': 'Petróleo (WTI)',
    'GC=F': 'Ouro'
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

CORES_YIELDS = ['#ef5350', '#4fc3f7', '#ab47bc', '#26a69a']
ALTURA_GRAFICO = 210
MARGEM_GRAFICO = dict(l=5, r=65, t=10, b=5)

# ------------------------------------------------------------------
# DADOS EM LOTE (OTIMIZADO)
# ------------------------------------------------------------------
TODOS_TICKERS = list(set(list(MOEDAS.keys()) + list(YIELDS.keys()) + list(COMMODITIES_RISCO.keys()) + list(ADRS.keys())))

@st.cache_data(ttl=60)
def carregar_dados_mercado(tickers):
    # Download vetorizado único para evitar rate-limiting e otimizar tempo
    df = yf.download(tickers, period="5d", interval="5m", prepost=True, progress=False)
    
    if df.empty:
        return pd.DataFrame(), {}
        
    df_close = df['Close']
    if isinstance(df_close.index, pd.DatetimeIndex) and df_close.index.tz is not None:
        df_close.index = df_close.index.tz_convert('UTC')
        
    df_close = df_close.ffill().bfill()

    # Cálculo da variação percentual diária
    dados_var = {}
    for ticker in tickers:
        if ticker in df_close.columns:
            serie = df_close[ticker].dropna()
            if not serie.empty:
                preco_atual = serie.iloc[-1]
                # Agrupa por data para pegar o último preço do dia anterior
                datas_unicas = np.unique(serie.index.date)
                if len(datas_unicas) >= 2:
                    data_anterior = datas_unicas[-2]
                    fechamento_anterior = serie[serie.index.date == data_anterior].iloc[-1]
                else:
                    fechamento_anterior = serie.iloc[0]
                
                var_pct = ((preco_atual / fechamento_anterior) - 1) * 100
                dados_var[ticker] = {
                    'preco': preco_atual,
                    'var_pct': var_pct,
                    'fechamento_anterior': fechamento_anterior
                }

    return df_close, dados_var

dados_linha, dados_var = carregar_dados_mercado(TODOS_TICKERS)

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

# ------------------------------------------------------------------
# CONSTRUÇÃO DOS GRÁFICOS DE LINHA
# ------------------------------------------------------------------
def grafico_com_variacao(tickers_nomes: dict, cores, var_dict: dict, mostrar_legenda: bool = False):
    fig = go.Figure()
    cols_existentes = [t for t in tickers_nomes.keys() if t in dados_linha.columns]
    
    if not cols_existentes or dados_linha.empty:
        return fig
        
    df_filtrado = dados_linha[cols_existentes].dropna(how='all')
    datas_str = df_filtrado.index.strftime('%d/%m %H:%M')

    for i, (ticker, nome) in enumerate(tickers_nomes.items()):
        if ticker not in df_filtrado.columns:
            continue
            
        s = df_filtrado[ticker]
        fech_ant = var_dict.get(ticker, {}).get('fechamento_anterior')
        
        if s.empty or fech_ant is None or fech_ant == 0:
            continue

        cor = cores.get(ticker, '#FFFFFF') if isinstance(cores, dict) else cores[i % len(cores)]
        # Calculado sobre o fechamento do dia anterior para refletir variação diária real
        ret = ((s / fech_ant) - 1) * 100

        fig.add_trace(go.Scatter(
            x=datas_str, 
            y=ret.values, 
            mode='lines', 
            name=nome,
            line=dict(color=cor, width=1.5),
            connectgaps=True
        ))

        var_pct = var_dict.get(ticker, {}).get('var_pct')
        texto = f"{nome} {var_pct:+.2f}%" if var_pct is not None else nome

        fig.add_annotation(
            xref="paper", x=1.005, xanchor="left",
            yref="y", y=ret.iloc[-1], yanchor="middle",
            text=texto, showarrow=False,
            bgcolor=cor, font=dict(color="white", size=8),
            borderpad=2, align="left"
        )

    fig.update_layout(
        template="plotly_dark", 
        height=ALTURA_GRAFICO, 
        margin=MARGEM_GRAFICO,
        yaxis=dict(title=None, zeroline=True, zerolinecolor='#333'),
        xaxis=dict(type='category', showticklabels=False),
        showlegend=mostrar_legenda,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0.5)", font=dict(size=8)) if mostrar_legenda else None
    )
    return fig

# ----------------------------------------------------
# LINHA 1: MOEDAS E YIELDS
# ----------------------------------------------------
col_esquerda, col_direita = st.columns(2, gap="small")

with col_esquerda:
    st.markdown("###### Moedas & DXY (% Variação Diária)")
    c_g1, c_t1 = st.columns([3, 1], gap="small")
    with c_g1:
        st.plotly_chart(
            grafico_com_variacao(MOEDAS, CORES_MOEDAS_EXATAS, dados_var, mostrar_legenda=True), 
            use_container_width=True
        )
    with c_t1:
        st.markdown(renderizar_tabela_lateral(MOEDAS, dados_var), unsafe_allow_html=True)

with col_direita:
    st.markdown("###### US Treasury Yields (% Variação Diária)")
    c_g2, c_t2 = st.columns([3, 1], gap="small")
    with c_g2:
        st.plotly_chart(
            grafico_com_variacao(YIELDS, CORES_YIELDS, dados_var, mostrar_legenda=False), 
            use_container_width=True
        )
    with c_t2:
        st.markdown(renderizar_tabela_lateral(YIELDS, dados_var), unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ----------------------------------------------------
# LINHA 2: ADRs BRASILEIRAS E COMMODITIES/RISCO
# ----------------------------------------------------
col_adr, col_macro = st.columns(2, gap="small")

def criar_grafico_barras(tickers_dict, dados_dict):
    names, vars_pct, colors = [], [], []
    for ticker, nome in tickers_dict.items():
        if ticker in dados_dict:
            v = dados_dict[ticker]['var_pct']
            names.append(nome)
            vars_pct.append(v)
            colors.append('#26a69a' if v >= 0 else '#ef5350')

    fig = go.Figure(data=[
        go.Bar(
            x=names, y=vars_pct, marker_color=colors,
            text=[f"{v:+.2f}%" for v in vars_pct],
            textposition='outside', textfont=dict(color='white', size=8)
        )
    ])
    fig.update_layout(
        template="plotly_dark", height=150,
        yaxis=dict(title=None, zeroline=True, zerolinecolor='#444', zerolinewidth=1),
        xaxis=dict(title=None, tickfont=dict(size=8)),
        margin=dict(l=5, r=5, t=15, b=5)
    )
    return fig

with col_adr:
    st.markdown("###### ADRs Brasileiras (Variação Diária %)")
    st.plotly_chart(criar_grafico_barras(ADRS, dados_var), use_container_width=True)
    
    metade_adr = len(ADRS) // 2
    c_t_adr1, c_t_adr2 = st.columns(2, gap="small")
    with c_t_adr1:
        st.markdown(renderizar_tabela_lateral(dict(list(ADRS.items())[:metade_adr]), dados_var), unsafe_allow_html=True)
    with c_t_adr2:
        st.markdown(renderizar_tabela_lateral(dict(list(ADRS.items())[metade_adr:]), dados_var), unsafe_allow_html=True)

with col_macro:
    st.markdown("###### EWZ, VIX & Commodities (Variação Diária %)")
    st.plotly_chart(criar_grafico_barras(COMMODITIES_RISCO, dados_var), use_container_width=True)
    
    metade_comm = len(COMMODITIES_RISCO) // 2
    c_t_comm1, c_t_comm2 = st.columns(2, gap="small")
    with c_t_comm1:
        st.markdown(renderizar_tabela_lateral(dict(list(COMMODITIES_RISCO.items())[:metade_comm]), dados_var), unsafe_allow_html=True)
    with c_t_comm2:
        st.markdown(renderizar_tabela_lateral(dict(list(COMMODITIES_RISCO.items())[metade_comm:]), dados_var), unsafe_allow_html=True)
