# ----------------------------------------------------
# SEÇÃO 3: ADRs BRASILEIRAS (LAYOUT COMPACTO E DENSO)
# ----------------------------------------------------
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("###### ADRs Brasileiras (Variação Diária %)")

col_adr_grafico, col_adr_tabela = st.columns(2, gap="medium")

tickers_adr = []
variacoes_adr = []
cores_adr = []

for ticker in ADRS.keys():
    if ticker in dados_var:
        var = dados_var[ticker]['var_pct']
        tickers_adr.append(ticker)
        variacoes_adr.append(var)
        cores_adr.append('#26a69a' if var >= 0 else '#ef5350')

# Coluna da Esquerda: Gráfico cobrindo metade da tela
with col_adr_grafico:
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
        height=220,
        yaxis=dict(title=None, zeroline=True, zerolinecolor='#444', zerolinewidth=1),
        xaxis=dict(title=None, tickfont=dict(size=9)),
        margin=dict(l=5, r=5, t=15, b=5)
    )

    st.plotly_chart(fig_adrs_bar, use_container_width=True)

# Coluna da Direita: Tabela lateral compacta sem preços (apenas % de variação em 2 colunas)
with col_adr_tabela:
    # Divide as 10 ADRs em duas colunas internas de 5 para ficar idêntico ao padrão
    metade = len(ADRS) // 2
    adrs_col1 = dict(list(ADRS.items())[:metade])
    adrs_col2 = dict(list(ADRS.items())[metade:])

    c_t_adr1, c_t_adr2 = st.columns(2, gap="small")
    with c_t_adr1:
        st.markdown(renderizar_tabela_lateral(adrs_col1, dados_var), unsafe_allow_html=True)
    with c_t_adr2:
        st.markdown(renderizar_tabela_lateral(adrs_col2, dados_var), unsafe_allow_html=True)
