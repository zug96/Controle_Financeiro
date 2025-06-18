import os
import streamlit as st
from supabase import create_client, Client
import bcrypt
from datetime import datetime

# --- CONEXÃO COM O SUPABASE ---
try:
    # Tenta pegar as variáveis de ambiente (para o deploy do bot)
    # Se não encontrar, tenta pegar do st.secrets (para o deploy do Streamlit)
    url: str = os.environ.get("SUPABASE_URL") or st.secrets["SUPABASE_URL"]
    key: str = os.environ.get("SUPABASE_KEY") or st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    # Se nenhuma das duas funcionar, mostra o erro no app Streamlit se ele estiver rodando
    if 'st' in globals():
        st.error("Erro fatal ao conectar com o Supabase. Verifique as credenciais de ambiente ou do secrets.toml")
    supabase = None

# --- FUNÇÕES DE AUTENTICAÇÃO E USUÁRIO ---

def registrar_novo_usuario(username, senha_texto_puro):
    username_lower = username.lower()
    response = supabase.table('usuarios').select('id').eq('username', username_lower).execute()
    if response.data:
        return False, "Usuário já existe."
    senha_bytes = senha_texto_puro.encode('utf-8')
    hash_senha = bcrypt.hashpw(senha_bytes, bcrypt.gensalt()).decode('utf-8')
    response_insert = supabase.table('usuarios').insert({'username': username_lower, 'senha_hash': hash_senha}).execute()
    return (True, "Usuário registrado com sucesso.") if response_insert.data else (False, "Erro ao registrar usuário.")

def verificar_senha(username, senha_texto_puro):
    username_lower = username.lower()
    response = supabase.table('usuarios').select('senha_hash').eq('username', username_lower).execute()
    if not response.data: return False
    hash_armazenado = response.data[0]['senha_hash'].encode('utf-8')
    senha_a_verificar = senha_texto_puro.encode('utf-8')
    return bcrypt.checkpw(senha_a_verificar, hash_armazenado)

def get_user_id(username):
    response = supabase.table('usuarios').select('id').eq('username', username.lower()).execute()
    return response.data[0]['id'] if response.data else None

# --- FUNÇÕES DE CATEGORIAS ---

def carregar_categorias():
    response = supabase.table('categorias').select('id, nome').order('nome').execute()
    return response.data if response.data else []

def get_categoria_id(nome_categoria):
    response = supabase.table('categorias').select('id').eq('nome', nome_categoria).execute()
    return response.data[0]['id'] if response.data else None

# --- FUNÇÕES DE DADOS FINANCEIROS ---

def carregar_dados(username: str):
    user_id = get_user_id(username)
    if not user_id: return []
    response = supabase.table('transacoes').select('id, data_transacao, valor, descricao, tipo, categorias(nome)').eq('user_id', user_id).order('data_transacao', desc=True).execute()
    dados_formatados = []
    if response.data:
        for item in response.data:
            dados_formatados.append({
                "id": item['id'], "data": item['data_transacao'], "valor": item['valor'],
                "categoria": item['categorias']['nome'] if item.get('categorias') else 'N/A',
                "descricao": item['descricao'], "tipo": item['tipo']
            })
    return dados_formatados

def adicionar_transacao(username: str, valor: float, categoria_nome: str, descricao: str, tipo: str, data_str=None):
    user_id = get_user_id(username)
    categoria_id = get_categoria_id(categoria_nome)
    if not user_id or not categoria_id: return False
    data_transacao = data_str if data_str else datetime.now().strftime("%Y-%m-%d")
    response = supabase.table('transacoes').insert({
        'user_id': user_id, 'categoria_id': categoria_id, 'valor': valor,
        'descricao': descricao, 'tipo': tipo, 'data_transacao': data_transacao
    }).execute()
    return True if response.data else False

def deletar_transacao(username: str, id_transacao: str):
    user_id = get_user_id(username)
    if not user_id: return False
    # Garante que um usuário só possa deletar suas próprias transações
    response = supabase.table('transacoes').delete().eq('id', id_transacao).eq('user_id', user_id).execute()
    return True if response.data else False

def carregar_orcamentos(username: str):
    user_id = get_user_id(username)
    if not user_id: return {}
    hoje = datetime.now()
    response = supabase.table('orcamentos').select('valor, categorias(nome)').eq('user_id', user_id).eq('ano', hoje.year).eq('mes', hoje.month).execute()
    orcamentos = {}
    if response.data:
        for item in response.data:
            orcamentos[item['categorias']['nome']] = item['valor']
    return orcamentos

def salvar_orcamentos(orcamentos: dict, username: str):
    user_id = get_user_id(username)
    if not user_id: return False
    hoje = datetime.now()
    
    registros_para_upsert = []
    for nome_cat, valor_orc in orcamentos.items():
        cat_id = get_categoria_id(nome_cat)
        if cat_id:
            registros_para_upsert.append({
                'user_id': user_id,
                'categoria_id': cat_id,
                'mes': hoje.month,
                'ano': hoje.year,
                'valor': valor_orc
            })
    
    if registros_para_upsert:
        # Upsert irá inserir novos ou atualizar existentes com base na chave única da tabela
        response = supabase.table('orcamentos').upsert(registros_para_upsert).execute()
        return True if response.data else False
    return True # Retorna True se não havia nada para salvar

# Adicione estas duas funções ao final de finance_utils.py

def get_user_from_telegram_id(telegram_id: int):
    """Busca o username de uma persona usando o ID do Telegram."""
    response = supabase.table('telegram_map').select('usuarios(username)').eq('telegram_id', telegram_id).execute()
    if response.data:
        return response.data[0]['usuarios']['username']
    return None

def map_telegram_id_to_user(telegram_id: int, username: str):
    """Associa um ID do Telegram a uma persona no banco de dados."""
    user_id = get_user_id(username)
    if not user_id:
        return False
    # Upsert para criar a associação ou atualizar se já existir
    response = supabase.table('telegram_map').upsert({'telegram_id': telegram_id, 'user_id': user_id}).execute()
    return True if response.data else False

# Adicione esta função ao final de finance_utils.py

def adicionar_categoria(nome_categoria: str):
    """Adiciona uma nova categoria no banco de dados, se ela não existir."""
    nome_formatado = nome_categoria.strip().title()

    # Verifica se a categoria já existe
    response_select = supabase.table('categorias').select('id').eq('nome', nome_formatado).execute()
    if response_select.data:
        return False, "Essa categoria já existe."

    # Insere a nova categoria
    response_insert = supabase.table('categorias').insert({'nome': nome_formatado}).execute()
    if response_insert.data:
        return True, "Categoria adicionada com sucesso."
    return False, "Erro ao adicionar categoria no banco de dados."
