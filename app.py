import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Importação segura do TvDatafeed (compatível com instalação via Git)
try:
    from tvdatafeed import TvDatafeed, Interval
except ImportError:
    from tvdatafeed.main import TvDatafeed, Interval

# Configuração da página
st.set_page_config(page_title="Cenário Macro", layout="wide")

st.title("📊 Monitor de Cenário Macroeconômico")

# Exemplo de inicialização e tratamento do TvDatafeed
@st.cache_resource
def init_tvdatafeed():
    try:
        # Inicializa em modo anônimo (sem necessidade de login/senha)
        return TvDatafeed()
    except Exception as e:
        st.error(f"Erro ao conectar com TradingView: {e}")
        return None

tv = init_tvdatafeed()

# Layout em colunas para os cards de métricas
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="USD/BRL (Dólar)", value="R$ 5,05", delta="-0.25%")

with col2:
    st.metric(label="IBOVESPA", value="128.500 pts", delta="+0.80%")

with col3:
    st.metric(label="S&P 500", value="5.100 pts", delta="+0.15%")

st.divider()

# Exemplo de gráfico utilizando Plotly
st.subheader("📈 Visão de Curva e Tendência")

# Criando dados demonstrativos para o gráfico
dates = pd.date_range(start="2026-01-01", periods=100)
values = np.random.randn(100).cumsum() + 100

fig = go.Figure()
fig.add_trace(go.Scatter(x=dates, y=values, mode='lines', name='Índice'))
fig.update_layout(
    margin=dict(l=20, r=20, t=30, b=20),
    template="plotly_dark",
    height=400
)

# Atualizado para a nova sintaxe do Streamlit (width='stretch' evita warnings do log)
st.plotly_chart(fig, width='stretch')
