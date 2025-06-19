import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
import glob

# Assumindo que finance_utils.py está no mesmo diretório e configurado para Supabase
from finance_utils import (
    carregar_dados, adicionar_transacao, deletar_transacao, carregar_orcamentos,
    salvar_orcamentos, carregar_categorias, verificar_senha, registrar_novo_usuario
)

st.set_page_config(page_title="Controle Financeiro", layout="wide", page_icon="🔐")

# --- LÓGICA DE LOGIN E REGISTRO ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = None

st.sidebar.title("Controle Financeiro")

if not st.session_state['logged_in']:
    st.sidebar.header("Acesso")
    login_ou_registro = st.sidebar.radio("Selecione uma opção", ["Login", "Registrar Nova Persona"])
    if login_ou_registro == "Login":
        with st.sidebar.form("login_form"):
            username = st.text_input("Nome da Persona", key="login_user").lower()
            password = st.text_input("Senha", type="password", key="login_pass")
            if st.form_submit_button("Entrar"):
                if verificar_senha(username, password):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.rerun()
                else:
                    st.sidebar.error("Persona ou senha incorreta.")
    elif login_ou_registro == "Registrar Nova Persona":
        with st.sidebar.form("register_form"):
            new_username = st.text_input("Escolha um nome para a Persona", key="reg_user").lower()
            new_password = st.text_input("Escolha uma Senha", type="password", key="reg_pass")
            confirm_password = st.text_input("Confirme a Senha", type="password", key="reg_pass_confirm")
            if st.form_submit_button("Registrar"):
                if not new_username or not new_password:
                    st.sidebar.warning("Por favor, preencha todos os campos.")
                elif new_password != confirm_password:
                    st.sidebar.error("As senhas não coincidem.")
                else:
                    success, message = registrar_novo_usuario(new_username, new_password)
                    if success: st.sidebar.success(message + " Você já pode fazer o login.")
                    else: st.sidebar.error(message)
    st.title("Bem-vindo ao Controle Financeiro")
    st.info("Por favor, faça o login ou registre uma nova persona na barra lateral para começar.")
else:
    username_logado = st.session_state['username']
    st.sidebar.header(f"Olá, {username_logado.title()}!")
    if st.sidebar.button("Sair (Logout)"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = None
        st.rerun()

    dados = carregar_dados(username_logado)
    df = pd.DataFrame(dados)
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        df = df.sort_values('data', ascending=False)

    st.sidebar.header("Filtros")
    categorias_data = carregar_categorias()
    categorias_disponiveis = [cat['nome'] for cat in categorias_data]
    categorias_selecionadas = st.sidebar.multiselect('Filtrar por Categoria', options=categorias_disponiveis, default=categorias_disponiveis)
    
    min_date = df['data'].min().date() if not df.empty else datetime.now().date()
    max_date = df['data'].max().date() if not df.empty else datetime.now().date()
    data_inicio = st.sidebar.date_input('Data Início', min_date, min_value=min_date, max_value=max_date)
    data_fim = st.sidebar.date_input('Data Fim', max_date, min_value=min_date, max_value=max_date)

    df_filtrado = df[df['categoria'].isin(categorias_selecionadas)] if not df.empty else df
    if not df_filtrado.empty:
        df_filtrado = df_filtrado[
            (pd.to_datetime(df_filtrado['data']).dt.date >= data_inicio) &
            (pd.to_datetime(df_filtrado['data']).dt.date <= data_fim)
        ]

    st.sidebar.header("Resumo do Período")
    if not df_filtrado.empty:
        receitas = df_filtrado[df_filtrado['valor'] > 0]['valor'].sum()
        despesas = df_filtrado[df_filtrado['valor'] < 0]['valor'].sum()
        saldo = receitas + despesas
        st.sidebar.metric("Receitas", f"R$ {receitas:,.2f}")
        st.sidebar.metric("Despesas", f"R$ {despesas:,.2f}", delta_color="inverse")
        st.sidebar.metric("Saldo", f"R$ {saldo:,.2f}")
    else:
        st.sidebar.info("Nenhum dado no período selecionado.")

    st.sidebar.header("Gerenciar Orçamentos")
    with st.sidebar.expander("Definir Limites Mensais"):
        orcamentos = carregar_orcamentos(username_logado)
        orcamentos_atualizados = {}
        categorias_despesa = [cat for cat in categorias_disponiveis if cat.lower() not in ["salário"]]
        for categoria in sorted(categorias_despesa):
            valor_atual = orcamentos.get(categoria, 0.0)
            novo_valor = st.number_input(f"Orçamento para {categoria}", key=f"orc_{categoria}", min_value=0.0, value=float(valor_atual), step=50.0, format="%.2f")
            orcamentos_atualizados[categoria] = novo_valor
        if st.button("Salvar Orçamentos"):
            if salvar_orcamentos(orcamentos_atualizados, username_logado):
                st.success("Orçamentos salvos com sucesso!")
                st.rerun()
            else:
                st.error("Erro ao salvar orçamentos.")
            
    st.title(f"Painel de Controle de {username_logado.title()}")
    st.markdown("Bem-vindo ao seu centro de controle financeiro pessoal.")

    st.markdown("---")
    st.write("#### Alertas de Orçamento do Mês Atual")
    orcamentos = carregar_orcamentos(username_logado)
    if not orcamentos:
        st.info("Você ainda não definiu nenhum orçamento. Vá em 'Gerenciar Orçamentos' na barra lateral para começar a receber alertas! 📊")
    else:
        # Lógica de alertas...
        pass
    st.markdown("---")

    st.subheader("Adicionar Nova Transação")
    with st.form("form_transacao", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1: data = st.date_input("Data", datetime.now())
        with col2: tipo_transacao = st.radio("Tipo", ('Necessidade', 'Desejo', 'Receita'), horizontal=True, label_visibility="collapsed")
        with col3: valor = st.number_input("Valor", step=0.01, format="%.2f", value=0.0)
        categoria = st.selectbox("Categoria", sorted(categorias_disponiveis))
        descricao = st.text_input("Descrição")
        if st.form_submit_button("Salvar Transação"):
            if valor != 0:
                valor_final = abs(valor) if tipo_transacao == 'Receita' else -abs(valor)
                if adicionar_transacao(username_logado, valor_final, categoria, descricao, tipo_transacao, data.strftime("%Y-%m-%d")):
                    st.success("Transação salva com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao salvar a transação.")
            else:
                st.warning("O valor não pode ser zero.")

    # --- SEÇÃO DOS GRÁFICOS ---
    st.subheader(f"📊 Análise do Período")
    if df_filtrado.empty:
        st.info("Nenhuma transação encontrada para os filtros selecionados.")
    else:
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.write("#### Gastos por Categoria")
            df_despesas = df_filtrado[df_filtrado['valor'] < 0].copy()
            if not df_despesas.empty:
                soma_categorias = abs(df_despesas.groupby("categoria")["valor"].sum())
                st.bar_chart(soma_categorias, color="#7928CA")
            else:
                st.write("Nenhuma despesa no período.")
        with col_graf2:
            st.write("#### Desejos vs. Necessidades")
            df_despesas = df_filtrado[df_filtrado['valor'] < 0].copy()
            if 'tipo' in df_despesas.columns:
                df_despesas_tipo = df_despesas.dropna(subset=['tipo'])
                soma_tipo = df_despesas_tipo.groupby("tipo")["valor"].sum().abs()
                if not soma_tipo.empty:
                    mapa_de_cores = {'Necessidade': '#1F77B4', 'Desejo': '#FF7F0E'}
                    fig = px.pie(soma_tipo, values=soma_tipo.values, names=soma_tipo.index,
                                 title='Distribuição de Gastos', color=soma_tipo.index,
                                 color_discrete_map=mapa_de_cores)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write("Nenhuma despesa classificada.")
            else:
                st.write("Nenhuma despesa classificada como Desejo/Necessidade.")

    # --- TABELA DE TRANSAÇÕES ---
    st.write("#### Histórico de Transações")
    # A linha abaixo foi removida no seu print, mas é importante para mostrar os dados
    st.dataframe(df_filtrado)

    with st.expander("🗑️ Apagar Transação"):
        if not df_filtrado.empty:
            transacoes_para_deletar = df_filtrado['id'].tolist()
            descricoes = [f"{row['data'].strftime('%d/%m/%Y')} - {row['descricao']} (R$ {row['valor']:.2f})" for idx, row in df_filtrado.iterrows()]
            mapa_desc_id = {desc: id_trans for desc, id_trans in zip(descricoes, transacoes_para_deletar)}
            
            selecionado = st.selectbox("Selecione a transação para apagar", options=[""] + descricoes)
            if st.button("Confirmar Deleção", type="primary"):
                if selecionado and deletar_transacao(username_logado, mapa_desc_id[selecionado]):
                    st.success("Transação deletada!")
                    st.rerun()
                else:
                    st.warning("Selecione uma transação.")
