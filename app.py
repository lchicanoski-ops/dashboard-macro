import streamlit as st
import pandas as pd
import yfinance as yf
from tvdatafeed import TvDatafeed, Interval
from streamlit_autorefresh import st_autorefresh

# 1. Configuração da página do Streamlit
st.set_page_config(
    page_title="Dashboard Macro & Contexto",
    page_layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Atualização Automática Controlada (10.000 ms = 10 segundos)
# O uso da chave 'macro_refresh_counter' evita conflitos no DOM React
refresh_count = st_autorefresh(interval=10000, limit=1000, key="macro_refresh_counter")

st.title("📊 Monitor de Contexto de Mercado & Macro")
st.caption(f"Atualizado automaticamente. Atualização nº: {refresh_count}")

# 3. Inicialização do TvDatafeed com cache do Streamlit
@st.cache_resource
def get_tv_client():
    # Inicialização sem credenciais para dados públicos
    return TvDatafeed()

tv = get_tv_client()

# 4. Função auxiliar para buscar dados do TradingView com segurança
def fetch_tv_data(symbol, exchange, interval=Interval.in_5_minute, n_bars=10):
    try:
        data = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=n_bars)
        if data is not None and not data.empty:
            return data
    except Exception as e:
        st.warning(f"Erro ao buscar {symbol} na {exchange}: {e}")
    return None

# 5. Função auxiliar para buscar dados do Yahoo Finance
def fetch_yf_data(tickers):
    try:
        df = yf.download(tickers=tickers, period="2d", interval="5m", progress=False)
        return df
    except Exception as e:
        st.warning(f"Erro ao buscar ativos no Yahoo Finance: {e}")
        return None

# --- PAINEL PRINCIPAL DE MÉTRICAS ---
st.subheader("🌐 Visão Geral do Mercado (Correlações & Meta Game)")

col1, col2, col3, col4 = st.columns(4)

# Exemplo: Ativos chaves para acompanhar correlação do Mini Índice
# EWZ (ETF Brasil nos EUA), 6L (Contrato de Real no CME / Dólar), Juros / S&P 500

with col1:
    ewz_data = fetch_tv_data("EWZ", "AMEX", n_bars=2)
    if ewz_data is not None and len(ewz_data) >= 2:
        close_now = ewz_data['close'].iloc[-1]
        close_prev = ewz_data['close'].iloc[-2]
        change = ((close_now - close_prev) / close_prev) * 100
        st.metric(
            label="EWZ (ETF Brasil)", 
            value=f"${close_now:.2f}", 
            delta=f"{change:.2f}%",
            key=f"metric_ewz_{refresh_count}"
        )
    else:
        st.metric(label="EWZ", value="N/D", key=f"metric_ewz_{refresh_count}")

with col2:
    spx_data = fetch_tv_data("SPX", "CBOE", n_bars=2)
    if spx_data is not None and len(spx_data) >= 2:
        close_now = spx_data['close'].iloc[-1]
        close_prev = spx_data['close'].iloc[-2]
        change = ((close_now - close_prev) / close_prev) * 100
        st.metric(
            label="S&P 500", 
            value=f"{close_now:.2f}", 
            delta=f"{change:.2f}%",
            key=f"metric_spx_{refresh_count}"
        )
    else:
        st.metric(label="S&P 500", value="N/D", key=f"metric_spx_{refresh_count}")

with col3:
    # Busca contratos futuros de dólar / real se necessário
    usd_data = fetch_tv_data("USDBRL", "FX_IDC", n_bars=2)
    if usd_data is not None and len(usd_data) >= 2:
        close_now = usd_data['close'].iloc[-1]
        close_prev = usd_data['close'].iloc[-2]
        change = ((close_now - close_prev) / close_prev) * 100
        st.metric(
            label="USD/BRL", 
            value=f"R$ {close_now:.4f}", 
            delta=f"{change:.2f}%",
            key=f"metric_usd_{refresh_count}"
        )
    else:
        st.metric(label="USD/BRL", value="N/D", key=f"metric_usd_{refresh_count}")

with col4:
    # Exemplo: Petróleo Brent ou DDI / Juros
    brent_data = fetch_tv_data("UKOIL", "TVC", n_bars=2)
    if brent_data is not None and len(brent_data) >= 2:
        close_now = brent_data['close'].iloc[-1]
        close_prev = brent_data['close'].iloc[-2]
        change = ((close_now - close_prev) / close_prev) * 100
        st.metric(
            label="Petróleo Brent", 
            value=f"${close_now:.2f}", 
            delta=f"{change:.2f}%",
            key=f"metric_brent_{refresh_count}"
        )
    else:
        st.metric(label="Petróleo Brent", value="N/D", key=f"metric_brent_{refresh_count}")

st.divider()

# --- ÁREA DE TABELAS E GRÁFICOS ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📈 Histórico Recente - EWZ (Gráfico 5m)")
    ewz_hist = fetch_tv_data("EWZ", "AMEX", interval=Interval.in_5_minute, n_bars=30)
    if ewz_hist is not None:
        # Exibe os dados do EWZ formatados
        chart_data = ewz_hist[['open', 'high', 'low', 'close']]
        st.line_chart(chart_data['close'], key=f"chart_ewz_{refresh_count}")
    else:
        st.info("Aguardando carregamento dos dados de cotação...")

with col_right:
    st.subheader("📋 Tabela de Monitoramento")
    if ewz_hist is not None:
        st.dataframe(
            ewz_hist[['open', 'high', 'low', 'close']].tail(10),
            use_container_width=True,
            key=f"table_ewz_{refresh_count}"
        )

# Dica importante no rodapé para evitar o erro de tradução do navegador
st.caption("📌 **Nota:** Se você visualizar algum erro de renderização, certifique-se de que a **tradução automática do navegador esteja DESATIVADA** para este site.")
