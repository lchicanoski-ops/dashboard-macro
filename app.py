import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

st.set_page_config(page_title="Cenário Macro", layout="wide")

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

# ------------------------------------------------------------------
# DICIONÁRIOS DE ATIVOS
# ------------------------------------------------------------------
MOEDAS = {
    '6E=F': '6E1!',
    '6J=F': '6J1!',
    '6L=F': '6L1!',
    '6M=F': '6M1!',
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
    '^ZT=F': 'US2Y',
    '^TNX': 'US10Y',
    '^FVX': 'US05Y'
}

COMMODITIES_RISCO = {
    'EWZ': 'EWZ',
    '^VIX': 'VIX',
    'CL=F': 'Petróleo',
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

CORES_YIELDS = ['#ef5350', '#26a69a', '#4fc3f7', '#ab47bc']

ALTURA_GRAFICO = 200
MARGEM_GRAFICO = dict(l=5, r=60, t=15, b=5)

# ------------------------------------------------------------------
# CARREGAMENTO DE DADOS COM SUPORTE A PRÉ-MERCADO (PREPOST)
# ------------------------------------------------------------------
@st.cache_data(ttl=60)
def carregar_dados_linha(tickers):
    df = yf.download(tickers, period="5d", interval="15m", prepost=True, progress=False)['Close']
    if isinstance(df, pd.DataFrame) and df.index.tz is not None:
        df.index = df.index.tz_convert('UTC')
    df = df.dropna(how='all')
    df = df.ffill().bfill()
    return df

todos_linha = list(MOEDAS.keys()) + list(YIELDS.keys())
dados_linha = carregar_dados_linha(todos_linha)

@st.cache_data(ttl=60)
def obter_dados_diarios_lote(tickers):
    dados_info = {}
    for ticker in tickers:
        try:
            tk = yf.Ticker(ticker)
            
            preco_atual = None
            try:
                preco_atual = tk.fast_info['lastPrice']
            except Exception:
                pass
            
            hist = tk.history(period="5d", interval="5m", prepost=True)
            
            if not hist.empty:
                if preco_atual is None or np.isnan(preco_atual):
                    preco_atual = hist['Close'].iloc[-1]
                
                fechamentos_diarios = hist['Close'].groupby(hist.index.date).last()
                
                if len(fechamentos_diarios) >= 2:
                    fechamento_anterior = fechamentos_diarios.iloc[-2]
                else:
                    fechamento_anterior = hist['Close'].iloc[0]
                
                var_pct = ((preco_atual / fechamento_anterior) - 1) * 100
                dados_info[ticker] = {
                    'preco': preco_atual,
                    'var_pct': var_pct
                }
        except Exception:
            pass
            
    return dados_info

todos_diarios = list(MOEDAS.keys()) + list(YIELDS.keys()) + list(COMMODITIES_RISCO.keys()) + list(ADRS.keys())
dados_var = obter_dados_diarios_lote(todos_diarios)

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
    if not cols_existentes:
        return fig
        
    df_filtrado = dados_linha[cols_existentes].dropna(how='all')
    datas_str = df_filtrado.index.strftime('%d/%m %H:%M')

    for i, (ticker, nome) in enumerate(tickers_nomes.items()):
        if ticker not in df_filtrado.columns:
            continue
            
        s = df_filtrado[ticker]
        if s.empty or s.iloc[0] == 0:
            continue

        cor = cores.get(ticker, '#FFFFFF') if isinstance(cores, dict) else cores[i % len(cores)]
        ret = ((s / s.iloc[0]) - 1) * 100

        fig.add_trace(go.Scatter(
            x=datas_str, 
            y=ret.values, 
            mode='lines', 
            name=nome,
            line=dict(color=cor, width=1.8),
            connectgaps=True
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
        xaxis=dict(type='category', showticklabels=False),
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
# LINHA 1: MOEDAS E YIELDS
# ----------------------------------------------------
col_esquerda, col_direita = st.columns(2, gap="medium")

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
# LINHA 2: ADRs BRASILEIRAS E COMMODITIES/RISCO
# ----------------------------------------------------
col_adr, col_macro = st.columns(2, gap="medium")

with col_adr:
    st.markdown("###### ADRs Brasileiras (Variação Diária %)")
    
    tickers_adr = []
    variacoes_adr = []
    cores_adr = []

    for ticker in ADRS.keys():
        if ticker in dados_var:
            var = dados_var[ticker]['var_pct']
            tickers_adr.append(ticker)
            variacoes_adr.append(var)
            cores_adr.append('#1b8a2e' if var >= 0 else '#ff3b30')

    fig_adrs_bar = go.Figure(data=[
        go.Bar(
            x=tickers_adr,
            y=variacoes_adr,
            marker_color=cores_adr,
            text=[f"{v:+.2f}%" for v in variacoes_adr],
            textposition='outside',
            textfont=dict(color='white', size=9)
        )
    ])

    fig_adrs_bar.update_layout(
        template="plotly_dark",
        height=170,
        yaxis=dict(title=None, zeroline=True, zerolinecolor='#444', zerolinewidth=1),
        xaxis=dict(title=None, tickfont=dict(size=9)),
        margin=dict(l=5, r=5, t=10, b=5)
    )

    st.plotly_chart(fig_adrs_bar, use_container_width=True)

    metade_adr = len(ADRS) // 2
    adrs_col1 = dict(list(ADRS.items())[:metade_adr])
    adrs_col2 = dict(list(ADRS.items())[metade_adr:])

    c_t_adr1, c_t_adr2 = st.columns(2, gap="small")
    with c_t_adr1:
        st.markdown(renderizar_tabela_lateral(adrs_col1, dados_var), unsafe_allow_html=True)
    with c_t_adr2:
        st.markdown(renderizar_tabela_lateral(adrs_col2, dados_var), unsafe_allow_html=True)

with col_macro:
    st.markdown("###### EWZ, VIX & Commodities (Variação Diária %)")
    
    tickers_comm_x = []
    variacoes_comm = []
    cores_comm = []

    for ticker, nome in COMMODITIES_RISCO.items():
        if ticker in dados_var:
            var = dados_var[ticker]['var_pct']
            tickers_comm_x.append(nome)
            variacoes_comm.append(var)
            cores_comm.append('#1b8a2e' if var >= 0 else '#ff3b30')

    fig_comm_bar = go.Figure(data=[
        go.Bar(
            x=tickers_comm_x,
            y=variacoes_comm,
            marker_color=cores_comm,
            text=[f"{v:+.2f}%" for v in variacoes_comm],
            textposition='outside',
            textfont=dict(color='white', size=9)
        )
    ])

    fig_comm_bar.update_layout(
        template="plotly_dark",
        height=170,
        yaxis=dict(title=None, zeroline=True, zerolinecolor='#444', zerolinewidth=1),
        xaxis=dict(title=None, tickfont=dict(size=9)),
        margin=dict(l=5, r=5, t=10, b=5)
    )

    st.plotly_chart(fig_comm_bar, use_container_width=True)

    metade_comm = len(COMMODITIES_RISCO.items()) // 2
    comm_col1 = dict(list(COMMODITIES_RISCO.items())[:metade_comm])
    comm_col2 = dict(list(COMMODITIES_RISCO.items())[metade_comm:])

    c_t_comm1, c_t_comm2 = st.columns(2, gap="small")
    with c_t_comm1:
        st.markdown(renderizar_tabela_lateral(comm_col1, dados_var), unsafe_allow_html=True)
    with c_t_comm2:
        st.markdown(renderizar_tabela_lateral(comm_col2, dados_var), unsafe_allow_html=True)
