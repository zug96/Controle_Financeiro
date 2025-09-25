import datetime
import uuid

# Banco de dados simulado em memória
USUARIOS = {}
SESSOES = {}
CATEGORIAS = ["Alimentação", "Transporte", "Pets", "Salário"]
TRANSACOES = {}
ORCAMENTOS = {}

PALAVRA_PASSE_GLOBAL = "GUS2025"


# --- Usuários ---

def registrar_novo_usuario(username: str, senha: str):
    username = username.lower()
    if username in USUARIOS:
        return False, "Usuário já existe."
    # Em um backend real, aqui faria hash da senha
    USUARIOS[username] = {
        "senha": senha,
        "data_criacao": datetime.datetime.now(),
        "id": str(uuid.uuid4()),
        "uso_funcionalidades": []
    }
    return True, "Usuário registrado com sucesso."


def verificar_senha(username: str, senha: str):
    user = USUARIOS.get(username.lower())
    if not user:
        return False
    return user["senha"] == senha


def alterar_senha(username: str, senha_antiga: str, senha_nova: str):
    user = USUARIOS.get(username.lower())
    if not user:
        return False, "Usuário não encontrado."
    if user["senha"] != senha_antiga:
        return False, "Senha antiga incorreta."
    user["senha"] = senha_nova
    return True, "Senha alterada com sucesso."


def get_usuario_info(username: str):
    user = USUARIOS.get(username.lower())
    if not user:
        return None
    return {
        "id": user["id"],
        "username": username.lower(),
        "data_criacao": user["data_criacao"].strftime("%Y-%m-%d %H:%M:%S"),
        "uso_funcionalidades": user["uso_funcionalidades"],
    }


# --- Categorias ---

def carregar_categorias():
    return [{"nome": c} for c in CATEGORIAS]


def adicionar_categoria(nome_categoria: str):
    nome = nome_categoria.strip().title()
    if nome in CATEGORIAS:
        return False, "Essa categoria já existe."
    CATEGORIAS.append(nome)
    return True, "Categoria adicionada com sucesso."


def deletar_categoria(nome_categoria: str):
    nome = nome_categoria.strip().title()
    if nome not in CATEGORIAS:
        return False, "Categoria não encontrada."
    CATEGORIAS.remove(nome)
    return True, "Categoria removida com sucesso."


def editar_categoria(nome_antigo: str, nome_novo: str):
    nome_antigo = nome_antigo.strip().title()
    nome_novo = nome_novo.strip().title()
    if nome_antigo not in CATEGORIAS:
        return False, "Categoria antiga não encontrada."
    if nome_novo in CATEGORIAS:
        return False, "Categoria nova já existe."
    idx = CATEGORIAS.index(nome_antigo)
    CATEGORIAS[idx] = nome_novo
    return True, "Categoria editada com sucesso."


# --- Transações ---

def carregar_dados(username: str):
    username = username.lower()
    user_transacoes = TRANSACOES.get(username, [])
    # Retorna lista de dicionários com as mesmas chaves do seu bot espera
    return user_transacoes


def adicionar_transacao(username: str, valor: float, categoria_nome: str, descricao: str, tipo: str, data_str=None):
    username = username.lower()
    if categoria_nome.title() not in CATEGORIAS:
        return False
    if username not in TRANSACOES:
        TRANSACOES[username] = []
    id_transacao = str(uuid.uuid4())
    data = data_str if data_str else datetime.datetime.now().strftime("%Y-%m-%d")
    transacao = {
        "id": id_transacao,
        "data": data,
        "valor": valor,
        "categoria": categoria_nome.title(),
        "descricao": descricao,
        "tipo": tipo
    }
    TRANSACOES[username].append(transacao)
    return True


def deletar_transacao(username: str, id_transacao: str):
    username = username.lower()
    if username not in TRANSACOES:
        return False
    transacoes_usuario = TRANSACOES[username]
    for i, t in enumerate(transacoes_usuario):
        if t["id"] == id_transacao:
            del transacoes_usuario[i]
            return True
    return False


def editar_transacao(username: str, id_transacao: str, novo_valor=None, nova_categoria=None, nova_descricao=None, novo_tipo=None, nova_data=None):
    username = username.lower()
    if username not in TRANSACOES:
        return False, "Nenhuma transação encontrada."
    for transacao in TRANSACOES[username]:
        if transacao["id"] == id_transacao:
            if novo_valor is not None:
                transacao["valor"] = novo_valor
            if nova_categoria is not None and nova_categoria.title() in CATEGORIAS:
                transacao["categoria"] = nova_categoria.title()
            if nova_descricao is not None:
                transacao["descricao"] = nova_descricao
            if novo_tipo is not None:
                transacao["tipo"] = novo_tipo
            if nova_data is not None:
                transacao["data"] = nova_data
            return True, "Transação editada com sucesso."
    return False, "Transação não encontrada."


# --- Orçamentos ---

def carregar_orcamentos(username: str):
    username = username.lower()
    return ORCAMENTOS.get(username, {})


def salvar_orcamentos(orcamentos: dict, username: str):
    username = username.lower()
    if username not in ORCAMENTOS:
        ORCAMENTOS[username] = {}
    for categoria, valor in orcamentos.items():
        ORCAMENTOS[username][categoria.title()] = valor
    return True


def remover_orcamento(username: str, categoria: str):
    username = username.lower()
    categoria = categoria.title()
    if username in ORCAMENTOS and categoria in ORCAMENTOS[username]:
        del ORCAMENTOS[username][categoria]
        return True
    return False


# --- Funções extras de rastreamento ---

def registrar_uso_funcionalidade(username: str, funcionalidade: str):
    username = username.lower()
    if username not in USUARIOS:
        return
    USUARIOS[username]["uso_funcionalidades"].append({
        "funcionalidade": funcionalidade,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# Função para validação da palavra-passe global (simples)
def validar_palavra_passe(palavra):
    return palavra.strip().upper() == PALAVRA_PASSE_GLOBAL

