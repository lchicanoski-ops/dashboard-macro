# ----------------------------------------------------
# LINHA 2: ADRs BRASILEIRAS E COMMODITIES/RISCO (AMBOS EM BARRAS)
# ----------------------------------------------------
col_adr, col_macro = st.columns(2, gap="medium")

# Lado Esquerdo: ADRs Brasileiras (Gráfico de Barras)
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
            cores_adr.append('#26a69a' if var >= 0 else '#ef5350')

    fig_adrs_bar = go.Figure(data=[
        go.Bar(
            x=tickers_adr,
            y=variacoes_adr,
            marker_color=cores_adr,
            text=[f"{v:+.2f}%" for v in variacoes_adr],
            textposition='auto',
            textfont=dict(color='white', size=10)
        )
    ])

    fig_adrs_bar.update_layout(
        template="plotly_dark",
        height=ALTURA_GRAFICO,
        yaxis=dict(title=None, zeroline=True, zerolinecolor='#444', zerolinewidth=1),
        xaxis=dict(title=None, tickfont=dict(size=9)),
        margin=dict(l=5, r=5, t=10, b=20)
    )

    st.plotly_chart(fig_adrs_bar, use_container_width=True)

# Lado Direito: EWZ, VIX & Commodities (Gráfico de Barras + Tabela Lateral)
with col_macro:
    st.markdown("###### EWZ, VIX & Commodities (Variação Diária %)")
    c_g3, c_t3 = st.columns([3, 1], gap="small")
    
    tickers_comm = []
    variacoes_comm = []
    cores_comm = []

    for ticker, nome in COMMODITIES_RISCO.items():
        if ticker in dados_var:
            var = dados_var[ticker]['var_pct']
            tickers_comm.append(nome)
            variacoes_comm.append(var)
            cores_comm.append('#26a69a' if var >= 0 else '#ef5350')

    with c_g3:
        fig_comm_bar = go.Figure(data=[
            go.Bar(
                x=tickers_comm,
                y=variacoes_comm,
                marker_color=cores_comm,
                text=[f"{v:+.2f}%" for v in variacoes_comm],
                textposition='auto',
                textfont=dict(color='white', size=10)
            )
        ])

        fig_comm_bar.update_layout(
            template="plotly_dark",
            height=ALTURA_GRAFICO,
            yaxis=dict(title=None, zeroline=True, zerolinecolor='#444', zerolinewidth=1),
            xaxis=dict(title=None, tickfont=dict(size=9)),
            margin=dict(l=5, r=5, t=10, b=20)
        )

        st.plotly_chart(fig_comm_bar, use_container_width=True)

    with c_t3:
        st.markdown("<h6 style='text-align: center;'>Risco / Comm</h6>", unsafe_allow_html=True)
        st.markdown(renderizar_tabela_lateral(COMMODITIES_RISCO, dados_var), unsafe_allow_html=True)
