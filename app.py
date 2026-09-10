import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ------------------------------------------------------------------
# CAPTURA DE MOEDAS E DXY (3 DIAS)
# ------------------------------------------------------------------
@st.cache_data(ttl=60)
def obter_dados_moedas_3d():
    # Tickers: Euro, Iene, Real, Peso Mex, DXY
    tickers = {
        '6E (Euro)': 'EURUSD=X',
        '6J (Iene)': 'JPY=X',
        '6L (Real)': 'BRL=X',
        '6M (Peso Mex)': 'MXN=X',
        'DXY': 'DX-Y.NYB'
    }
    
    df_list = []
    
    for nome, ticker in tickers.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="3d", interval="15m")
            if not hist.empty:
                df = hist[['Close']].copy()
                df.columns = [nome]
                
                # Inversao das cotações indiretas (JPY, BRL, MXN) para refletir valor da moeda frente ao USD
                if nome in ['6J (Iene)', '6L (Real)', '6M (Peso Mex)']:
                    df[nome] = 1.0 / df[nome]
                
                # Normalização em % a partir do 1º ponto do período de 3d
                base_val = df[nome].iloc[0]
                df[f"{nome}_pct"] = ((df[nome] - base_val) / base_val) * 100.0
                df_list.append(df[[f"{nome}_pct"]])
        except Exception:
            pass

    if df_list:
        df_final = pd.concat(df_list, axis=1).ffill().bfill()
        return df_final
    return pd.DataFrame()

# ------------------------------------------------------------------
# PLOT DO GRÁFICO COM BOTÕES/LEGENDA INTERATIVA
# ------------------------------------------------------------------
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
        
        # Define quais moedas iniciam visíveis
        vis = True if nome_limpo in moedas_visiveis else "legendonly"
        
        y_vals = df_moedas[col]
        last_val = y_vals.iloc[-1]
        
        # Linha da moeda
        fig.add_trace(go.Scatter(
            x=df_moedas.index,
            y=y_vals,
            mode='lines',
            name=nome_limpo,
            line=dict(color=cor, width=2),
            visible=vis
        ))
        
        # Rótulo de cotação final no gráfico (ajustado para não cobrir linhas)
        if vis is True:
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
        margin=dict(l=10, r=80, t=30, b=10),
        xaxis=dict(showgrid=True, gridcolor="#222"),
        yaxis=dict(showgrid=True, gridcolor="#222", title="Variação %"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=11),
            itemclick="toggle",          # Clicar esconde/mostra a linha individual
            itemdoubleclick="toggleothers" # Duplo clique isola a moeda selecionada
        )
    )

    return fig

# ------------------------------------------------------------------
# INTERFACE
# ------------------------------------------------------------------
df_moedas = obter_dados_moedas_3d()

if not df_moedas.empty:
    col_ctrl, col_vazio = st.columns([3, 1])
    with col_ctrl:
        # Botão seletor nativo para ocultar/exibir rápido
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
                f"<div style='display:flex; justify-between:space-between; font-size:1.1rem; margin-bottom:8px;'>"
                f"<b>{nome_limpo}!</b> <span style='color:{cor_txt}; font-weight:bold;'>{val:+.2f}%</span>"
                f"</div>", 
                unsafe_allow_html=True
            )
