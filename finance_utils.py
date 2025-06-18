import json
from pathlib import Path
from datetime import datetime
import uuid
import bcrypt # Importa a nova biblioteca

# --- ARQUIVOS DE DADOS ---
CATEGORIAS_ARQUIVO = Path("categorias.json")
CREDENCIAIS_ARQUIVO = Path("credenciais.json")


# --- FUNÇÕES GLOBAIS (Categorias) ---
def carregar_categorias():
    if CATEGORIAS_ARQUIVO.exists():
        with open(CATEGORIAS_ARQUIVO, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except json.JSONDecodeError: return []
    return []

def salvar_categorias(categorias):
    with open(CATEGORIAS_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(sorted(categorias), f, indent=2, ensure_ascii=False)


# --- FUNÇÕES DE AUTENTICAÇÃO E USUÁRIO ---
def _get_caminho_arquivo_usuario(tipo: str, username: str) -> Path:
    """Função interna para gerar nomes de arquivo padronizados."""
    if not username or not isinstance(username, str):
        raise ValueError("Username inválido.")
    return Path(f"{tipo}_{username.lower().strip()}.json")

def carregar_credenciais():
    """Carrega as credenciais de todos os usuários."""
    if CREDENCIAIS_ARQUIVO.exists():
        with open(CREDENCIAIS_ARQUIVO, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except json.JSONDecodeError: return {}
    return {}

def salvar_credenciais(credenciais):
    """Salva o dicionário de credenciais."""
    with open(CREDENCIAIS_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(credenciais, f, indent=2)

def registrar_novo_usuario(username, senha_texto_puro):
    """Registra um novo usuário com senha em hash."""
    credenciais = carregar_credenciais()
    username_lower = username.lower()

    if username_lower in credenciais:
        return False, "Usuário já existe."

    # Gera o hash da senha
    senha_bytes = senha_texto_puro.encode('utf-8')
    hash_senha = bcrypt.hashpw(senha_bytes, bcrypt.gensalt())
    
    # Armazena o hash como string (decodificando de bytes)
    credenciais[username_lower] = hash_senha.decode('utf-8')
    salvar_credenciais(credenciais)
    return True, "Usuário registrado com sucesso."

def verificar_senha(username, senha_texto_puro):
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    credenciais = carregar_credenciais()
    username_lower = username.lower()

    if username_lower not in credenciais:
        return False # Usuário não encontrado

    hash_armazenado_str = credenciais[username_lower]
    hash_armazenado_bytes = hash_armazenado_str.encode('utf-8')
    
    senha_bytes = senha_texto_puro.encode('utf-8')

    return bcrypt.checkpw(senha_bytes, hash_armazenado_bytes)

# --- FUNÇÕES POR USUÁRIO (Dados Financeiros) ---
def carregar_dados(username: str):
    arquivo_usuario = _get_caminho_arquivo_usuario("transacoes", username)
    if arquivo_usuario.exists():
        with open(arquivo_usuario, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except json.JSONDecodeError: return []
    return []

def salvar_dados(dados: list, username: str):
    arquivo_usuario = _get_caminho_arquivo_usuario("transacoes", username)
    with open(arquivo_usuario, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def adicionar_transacao(username: str, valor: float, categoria: str, descricao: str, tipo: str, data_str=None):
    dados = carregar_dados(username)
    data = data_str if data_str else datetime.now().strftime("%Y-%m-%d")
    nova_transacao = {"id": str(uuid.uuid4()), "data": data, "valor": valor, "categoria": categoria, "descricao": descricao, "tipo": tipo}
    dados.append(nova_transacao)
    salvar_dados(dados, username)
    print(f"Transação adicionada para {username}: {nova_transacao}")

def deletar_transacao(username: str, id_transacao: str):
    dados = carregar_dados(username)
    dados_filtrados = [t for t in dados if t.get('id') != id_transacao]
    if len(dados_filtrados) < len(dados):
        salvar_dados(dados_filtrados, username)
        return True
    return False

def carregar_orcamentos(username: str):
    arquivo_usuario = _get_caminho_arquivo_usuario("orcamentos", username)
    if arquivo_usuario.exists():
        with open(arquivo_usuario, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except json.JSONDecodeError: return {}
    return {}

def salvar_orcamentos(orcamentos: dict, username: str):
    arquivo_usuario = _get_caminho_arquivo_usuario("orcamentos", username)
    with open(arquivo_usuario, "w", encoding="utf-8") as f:
        json.dump(orcamentos, f, indent=2, ensure_ascii=False)
