import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from tvdatafeed import TvDatafeed, Interval

st.set_page_config(page_title="Cenário Macro", layout="wide")

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=60000, key="datarefresh")
except ImportError:
    pass

# Inicializa conexão pública com o TradingView
@st.cache_resource
def iniciar_tv():
    return TvDatafeed()

tv = iniciar_tv()

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

        .stTabs [data-baseweb="tab-list"] { gap: 4px; }
        .stTabs [data-baseweb="tab"] { padding: 2px 8px; font-size: 0.75rem; height: 24px; }

        .side-table {
            width: auto;
            border-collapse: collapse;
            font-size: 0.8rem;
            margin: 0 auto;
        }
        .side-table tr { border-bottom: 1px solid #1e2330; }
        .side-table td { padding: 3px 6px; font-weight: 600; white-space: nowrap; }
        .symbol-col { text-align: left; color: #e0e0e0; }
        .var-col { text-align: left; padding-left: 12px !important; }
        .positive { color: #26a69a; }
        .negative { color: #ef5350; }
    </style>
""", unsafe_allow_html=True)

st.title("CENÁRIO MACRO - PAINEL DE CORRELAÇÃO")

# ------------------------------------------------------------------
# DICIONÁRIOS REESTRUTURADOS COM BOLSA (EXCHANGE) DO TRADINGVIEW
# Estrutura: 'CHAVE_INTERNA': ('TICKER_TV', 'NOME_EXIBICAO', 'EXCHANGE_TV')
# ------------------------------------------------------------------
MOEDAS = {
    '6E': ('6E1!', '6E1!', 'CME'),
    '6J': ('6J1!', '6J1!', 'CME'),
    '6L': ('6L1!', '6L1!', 'CME'),
    '6M': ('6M1!', '6M1!', 'CME')
}

CORES_MOEDAS_EXATAS = {
    '6E': '#1e50bc',
    '6J': '#d4c92a',
    '6L': '#1b8a2e',
    '6M': '#c87820'
}

YIELDS = {
    'US30Y': ('US30Y', 'US30Y', 'TVC'),
    'US02Y': ('US02Y', 'US2Y', 'TVC'),
    'US10Y': ('US10Y', 'US10Y', 'TVC'),
    'US05Y': ('US05Y', 'US05Y', 'TVC')
}

DI_B3 = {
    'DI1F2029': ('DI1F2029', 'DI1 F29', 'BMF'),
    'DI1F2030': ('DI1F2030', 'DI1 F30', 'BMF'),
    'DI1F2035': ('DI1F2035', 'DI1 F35', 'BMF')
}

CORES_DI = {
    'DI1F2029': '#ff9800',
    'DI1F2030': '#e91e63',
    'DI1F2035': '#9c27b0'
}

COMMODITIES_RISCO = {
    'DXY': ('DXY', 'DXY', 'ICE'),
    'EWZ': ('EWZ', 'EWZ', 'NYSE'),
    'VIX': ('VIX', 'VIX', 'CBOE'),
    'CL': ('CL1!', 'Petróleo', 'NYMEX'),
    'GC': ('GC1!', 'Ouro', 'COMEX')
}

ADRS = {
    'VALE': ('VALE', 'Vale', 'NYSE'),
    'PBR': ('PBR', 'Petrobras', 'NYSE'),
    'ITUB': ('ITUB', 'Itaú', 'NYSE'),
    'BBD': ('BBD', 'Bradesco', 'NYSE'),
    'ABEV': ('ABEV', 'Ambev', 'NYSE'),
    'GGB': ('GGB', 'Gerdau', 'NYSE'),
    'CSAN': ('CSAN', 'Cosan', 'NYSE'),
    'BAK': ('BAK', 'Braskem', 'NYSE'),
    'XP': ('XP', 'XP Inc', 'NASDAQ'),
    'NU': ('NU', 'Nubank', 'NYSE')
}

CORES_YIELDS = ['#ef5350', '#26a69a', '#4fc3f7', '#ab47bc']
ALTURA_GRAFICO = 200
MARGEM_GRAFICO = dict(l=5, r=60, t=15, b=5)

# ------------------------------------------------------------------
# CARREGAMENTO DE DADOS VIA TRADINGVIEW API
# ------------------------------------------------------------------
@st.cache_data(ttl=60)
def carregar_dados_linha_tv(ativos_dict):
    series_list = {}
    for chave, (symbol, _, exchange) in ativos_dict.items():
        try:
            df_hist = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_15_minute, n_bars=300)
            if df_hist is not None and not df_hist.empty:
                series_list[chave] = df_hist['close']
        except Exception:
            pass
            
    if not series_list:
        return pd.DataFrame()
        
    df_final = pd.DataFrame(series_list)
    df_final = df_final.ffill().bfill()
    return df_final

todos_linha_map = {**MOEDAS, **YIELDS, **DI_B3}
dados_linha = carregar_dados_linha_tv(todos_linha_map)

@st.cache_data(ttl=60)
def obter_dados_diarios_tv(ativos_dict):
    dados_info = {}
    for chave, (symbol, _, exchange) in ativos_dict.items():
        try:
            df_hist = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_5_minute, n_bars=200)
            if df_hist is not None and not df_hist.empty:
                preco_atual = df_hist['close'].iloc[-1]
                
                # Agrupa os fechamentos por data para capturar o fechamento do dia anterior
                fechamentos_diarios = df_hist['close'].groupby(df_hist.index.date).last()
                fechamento_anterior = fechamentos_diarios.iloc[-2] if len(fechamentos_diarios) >= 2 else df_hist['close'].iloc[0]
                
                var_pct = ((preco_atual / fechamento_anterior) - 1) * 100
                dados_info[chave] = {'preco': preco_atual, 'var_pct': var_pct}
        except Exception:
            pass
            
    return dados_info

todos_diarios_map = {**MOEDAS, **YIELDS, **DI_B3, **COMMODITIES_RISCO, **ADRS}
dados_var = obter_dados_diarios_tv(todos_diarios_map)

def renderizar_tabela_lateral(ativos_dict, dados_dict):
    html = '<table class="side-table">'
    for chave, (_, nome, _) in ativos_dict.items():
        if chave in dados_dict:
            info = dados_dict[chave]
            var = info['var_pct']
            cor_classe = "positive" if var >= 0 else "negative"
            var_fmt = f"{var:+.2f}%"
            html += f'<tr><td class="symbol-col">{nome}</td><td class="var-col {cor_classe}">{var_fmt}</td></tr>'
    html += '</table>'
    return html

# ------------------------------------------------------------------
# CONSTRUÇÃO DOS GRÁFICOS DE LINHA
# ------------------------------------------------------------------
def grafico_com_variacao(ativos_dict: dict, cores, var_dict: dict, mostrar_legenda: bool = False):
    fig = go.Figure()
    cols_existentes = [k for k in ativos_dict.keys() if k in dados_linha.columns]
    if not cols_existentes:
        return fig
        
    df_filtrado = dados_linha[cols_existentes].dropna(how='all')
    datas_str = df_filtrado.index.strftime('%d/%m %H:%M')

    for i, (chave, (_, nome, _)) in enumerate(ativos_dict.items()):
        if chave not in df_filtrado.columns:
            continue
            
        s = df_filtrado[chave]
        if s.empty or s.iloc[0] == 0:
            continue

        cor = cores.get(chave, '#FFFFFF') if isinstance(cores, dict) else cores[i % len(cores)]
        ret = ((s / s.iloc[0]) - 1) * 100

        fig.add_trace(go.Scatter(
            x=datas_str, y=ret.values, mode='lines', name=nome,
            line=dict(color=cor, width=1.8), connectgaps=True
        ))

        var_pct = var_dict.get(chave, {}).get('var_pct')
        texto = f"{nome} {var_pct:+.2f}%" if var_pct is not None else nome

        fig.add_annotation(
            xref="paper", x=1.005, xanchor="left",
            yref="y", y=ret.iloc[-1], yanchor="middle",
            text=texto, showarrow=False,
            bgcolor=cor, font=dict(color="white", size=8),
            borderpad=2, align="left",
        )

    layout_args = dict(
        template="plotly_dark", height=ALTURA_GRAFICO, margin=MARGEM_GRAFICO,
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
# LINHA 1: MOEDAS E YIELDS / DI FUTURO (TABS)
# ----------------------------------------------------
col_esquerda, col_direita = st.columns(2, gap="medium")

with col_esquerda:
    st.markdown("###### Moedas Futures (% Variação)")
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
    tab_us, tab_di = st.tabs(["US Treasury Yields", "DI Futuro (B3)"])
    
    with tab_us:
        c_g2, c_t2 = st.columns([3, 1], gap="small")
        with c_g2:
            st.plotly_chart(
                grafico_com_variacao(YIELDS, CORES_YIELDS, dados_var, mostrar_legenda=False), 
                use_container_width=True
            )
        with c_t2:
            st.markdown("<h6 style='text-align: center;'>Yields</h6>", unsafe_allow_html=True)
            st.markdown(renderizar_tabela_lateral(YIELDS, dados_var), unsafe_allow_html=True)
            
    with tab_di:
        c_g3, c_t3 = st.columns([3, 1], gap="small")
        with c_g3:
            st.plotly_chart(
                grafico_com_variacao(DI_B3, CORES_DI, dados_var, mostrar_legenda=False), 
                use_container_width=True
            )
        with c_t3:
            st.markdown("<h6 style='text-align: center;'>Juros BR</h6>", unsafe_allow_html=True)
            st.markdown(renderizar_tabela_lateral(DI_B3, dados_var), unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ----------------------------------------------------
# LINHA 2: ADRs BRASILEIRAS E DXY/EWZ/COMMODITIES
# ----------------------------------------------------
col_adr, col_macro = st.columns(2, gap="medium")

with col_adr:
    st.markdown("###### ADRs Brasileiras (Variação Diária %)")
    tickers_adr, variacoes_adr, cores_adr = [], [], []

    for chave, (_, nome, _) in ADRS.items():
        if chave in dados_var:
            var = dados_var[chave]['var_pct']
            tickers_adr.append(nome)
            variacoes_adr.append(var)
            cores_adr.append('#1b8a2e' if var >= 0 else '#ff3b30')

    fig_adrs_bar = go.Figure(data=[
        go.Bar(
            x=tickers_adr, y=variacoes_adr, marker_color=cores_adr,
            text=[f"{v:+.2f}%" for v in variacoes_adr], textposition='outside',
            textfont=dict(color='white', size=9)
        )
    ])
    fig_adrs_bar.update_layout(
        template="plotly_dark", height=170,
        yaxis=dict(title=None, zeroline=True, zerolinecolor='#444', zerolinewidth=1),
        xaxis=dict(title=None, tickfont=dict(size=9)),
        margin=dict(l=5, r=5, t=10, b=5)
    )
    st.plotly_chart(fig_adrs_bar, use_container_width=True)

    metade_adr = len(ADRS) // 2
    c_t_adr1, c_t_adr2 = st.columns(2, gap="small")
    with c_t_adr1:
        st.markdown(renderizar_tabela_lateral(dict(list(ADRS.items())[:metade_adr]), dados_var), unsafe_allow_html=True)
    with c_t_adr2:
        st.markdown(renderizar_tabela_lateral(dict(list(ADRS.items())[metade_adr:]), dados_var), unsafe_allow_html=True)

with col_macro:
    st.markdown("###### DXY, EWZ, VIX & Commodities (Variação Diária %)")
    tickers_comm_x, variacoes_comm, cores_comm = [], [], []

    for chave, (_, nome, _) in COMMODITIES_RISCO.items():
        if chave in dados_var:
            var = dados_var[chave]['var_pct']
            tickers_comm_x.append(nome)
            variacoes_comm.append(var)
            cores_comm.append('#1b8a2e' if var >= 0 else '#ff3b30')
        else:
            tickers_comm_x.append(nome)
            variacoes_comm.append(0.0)
            cores_comm.append('#888888')

    fig_comm_bar = go.Figure(data=[
        go.Bar(
            x=tickers_comm_x, y=variacoes_comm, marker_color=cores_comm,
            text=[f"{v:+.2f}%" for v in variacoes_comm], textposition='outside',
            textfont=dict(color='white', size=9)
        )
    ])
    fig_comm_bar.update_layout(
        template="plotly_dark", height=170,
        yaxis=dict(title=None, zeroline=True, zerolinecolor='#444', zerolinewidth=1),
        xaxis=dict(title=None, tickfont=dict(size=9)),
        margin=dict(l=5, r=5, t=10, b=5)
    )
    st.plotly_chart(fig_comm_bar, use_container_width=True)

    items_comm = list(COMMODITIES_RISCO.items())
    c_t_comm1, c_t_comm2 = st.columns(2, gap="small")
    with c_t_comm1:
        st.markdown(renderizar_tabela_lateral(dict(items_comm[:3]), dados_var), unsafe_allow_html=True)
    with c_t_comm2:
        st.markdown(renderizar_tabela_lateral(dict(items_comm[3:]), dados_var), unsafe_allow_html=True)
