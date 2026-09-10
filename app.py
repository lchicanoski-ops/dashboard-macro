import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Terminal Macro", layout="wide", initial_sidebar_state="collapsed")

# Estilização CSS para visual de terminal de trading
st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        .block-container { padding-top: 1rem; padding-bottom: 0.5rem; padding-left: 1.5rem; padding-right: 1.5rem; }
        h1, h2, h3 { margin-bottom: 0.2rem !important; }
        div[data-testid="stMetricValue"] { font-size: 1.3rem !important; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Termômetro Macro & Correlação")

@st.cache_data(ttl=60)
def carregar_dados_macro():
    tickers = {
        # Yields & Índices
        'US10Y': '^TNX',
        'S&P 500': '^GSPC',
        'EWZ': 'EWZ',
        # ADRs
        'VALE (ADR)': 'VALE',
        'PETR (PBR)': 'PBR',
        'ITUB (ADR)': 'ITUB',
        # Moedas
        '6E (Euro)': 'EURUSD=X',
        '6J (Iene)': 'JPY=X',
        '6L (Real)': 'BRL=X',
        '6M (Peso Mex)': 'MXN=X',
        'DXY': 'DX-Y.NYB'
    }
    
    dados_pct = {}
    dados_hist_moedas = []

    for nome, ticker in tickers.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="3d", interval="15m")
            if not hist.empty:
                last_price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else last_price
                
                # Para o gráfico histórico de moedas (3 dias em base %)
                if nome in ['6E (Euro)', '6J (Iene)', '6L (Real)', '6M (Peso Mex)', 'DXY']:
                    df_m = hist[['Close']].copy()
                    df_m.columns = [nome]
                    # Inverter par para moedas cotadas contra o USD
                    if nome in ['6J (Iene)', '6L (Real)', '6M (Peso Mex)']:
                        df_m[nome] = 1.0 / df_m[nome]
                    base_val = df_m[nome].iloc[0]
                    df_m[f"{nome}_pct"] = ((df_m[nome] - base_val) / base_val) * 100.0
                    dados_hist_moedas.append(df_m[[f"{nome}_pct"]])

                chg_pct = ((last_price - prev_close) / prev_close) * 100.0
                dados_pct[nome] = {'price': last_price, 'change_pct': chg_pct}
        except Exception:
            pass

    df_hist_moedas = pd.concat(dados_hist_moedas, axis=1).ffill().bfill() if dados_hist_moedas else pd.DataFrame()
    return dados_pct, df_hist_moedas

def plotar_grafico_moedas(df_moedas, moedas_visiveis):
    fig = go.Figure()
    cores = {
        '6E (Euro)': '#0055ff',      # Azul
        '6J (Iene)': '#e6b800',      # Amarelo
        '6L (Real)': '#00e640',      # Verde
        '6M (Peso Mex)': '#ff8000',  # Laranja
        'DXY': '#ffffff'             # Branco
    }

    cols = [col for col in df_moedas.columns if any(m in col for m in moedas_visiveis)]

    for col in cols:
        nome_limpo = col.replace("_pct", "")
        cor = cores.get(nome_limpo, '#ffffff')
        y_vals = df_moedas[col]
        last_val = y_vals.iloc[-1]
        
        fig.add_trace(go.Scatter(
            x=df_moedas.index,
            y=y_vals,
            mode='lines',
            name=nome_limpo,
            line=dict(color=cor, width=2)
        ))
        
        fig.add_annotation(
            x=df_moedas.index[-1],
            y=last_val,
            text=f"<b>{nome_limpo.split()[0]}: {last_val:+.2f}%</b>",
            showarrow=False,
            xanchor="left",
            yanchor="middle",
            bgcolor=cor,
            bordercolor=cor,
            font=dict(color="black" if cor in ['#e6b800', '#00e640'] else "white", size=10)
        )

    fig.update_layout(
        title="Correlação de Moedas (3 Dias) - Base %",
        template="plotly_dark",
        height=500,
        margin=dict(l=10, r=90, t=30, b=10),
        xaxis=dict(showgrid=True, gridcolor="#222"),
        yaxis=dict(showgrid=True, gridcolor="#222", title="Variação %"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
    )
    return fig

# Carregar dados
dados_pct, df_moedas = carregar_dados_macro()

if dados_pct:
    # 1. LINHA DE CARDS SUPERIORES (Yields, Índices & ADRs)
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    def exibe_card(col, titulo, chave):
        if chave in dados_pct:
            val = dados_pct[chave]['change_pct']
            p = dados_pct[chave]['price']
            col.metric(titulo, f"{p:.2f}", f"{val:+.2f}%")

    exibe_card(col1, "US10Y (Yield)", "US10Y")
    exibe_card(col2, "S&P 500", "S&P 500")
    exibe_card(col3, "EWZ", "EWZ")
    exibe_card(col4, "VALE (ADR)", "VALE (ADR)")
    exibe_card(col5, "PETR (PBR)", "PETR (PBR)")
    exibe_card(col6, "ITUB (ADR)", "ITUB (ADR)")

    st.divider()

    # 2. BLOCO DO GRÁFICO DE MOEDAS + TABELA
    if not df_moedas.empty:
        opcoes_disponiveis = ['6E (Euro)', '6J (Iene)', '6L (Real)', '6M (Peso Mex)', 'DXY']
        moedas_selecionadas = st.multiselect(
            "Filtrar Moedas no Gráfico:",
            options=opcoes_disponiveis,
            default=opcoes_disponiveis
        )

        col_graf, col_tabela = st.columns([3, 1])
        
        with col_graf:
            st.plotly_chart(
                plotar_grafico_moedas(df_moedas, moedas_selecionadas), 
                use_container_width=True
            )
            
        with col_tabela:
            st.markdown("### Moedas")
            for col in df_moedas.columns:
                nome_limpo = col.replace("_pct", "").split()[0]
                val = df_moedas[col].iloc[-1]
                cor_txt = "#00e640" if val >= 0 else "#ff3b30"
                st.markdown(
                    f"<div style='display:flex; justify-content:space-between; font-size:1.1rem; margin-bottom:12px;'>"
                    f"<b>{nome_limpo}!</b> <span style='color:{cor_txt}; font-weight:bold;'>{val:+.2f}%</span>"
                    f"</div>", 
                    unsafe_allow_html=True
                )
else:
    st.info("Carregando cotações de mercado...")
