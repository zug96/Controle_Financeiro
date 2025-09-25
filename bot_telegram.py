import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)
import re
import backend  # Nosso backend mock local, substitua pelo real quando quiser

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Estados para ConversationHandler
(
    ASK_PASSPHRASE, ASK_USERNAME, ASK_PASSWORD,
    MENU, SUBMENU_CATEGORIAS, SUBMENU_ORCAMENTOS, SUBMENU_TRANSACOES,
    REGISTRAR_TRANSACAO_VALOR, REGISTRAR_TRANSACAO_CATEGORIA, REGISTRAR_TRANSACAO_DESCRICAO, REGISTRAR_TRANSACAO_TIPO,
    EDITAR_SENHA_OLD, EDITAR_SENHA_NEW, EDITAR_SENHA_CONFIRM,
    ADICIONAR_CATEGORIA_NOME, EDITAR_CATEGORIA_ANTIGO, EDITAR_CATEGORIA_NOVO,
    REMOVER_CATEGORIA_NOME,
    VISUALIZAR_TRANSACOES, ESCOLHER_TRANSACAO_EDITAR, EDITAR_TRANSACAO_CAMPO, EDITAR_TRANSACAO_VALOR, EDITAR_TRANSACAO_CATEGORIA,
    EDITAR_TRANSACAO_DESCRICAO, EDITAR_TRANSACAO_TIPO, EDITAR_TRANSACAO_DATA,
    REMOVER_TRANSACAO_ESCOLHA,
    GERENCIAR_ORCAMENTOS,
    # Outros estados podem ser adicionados conforme necessidade
) = range(28)

# Utilitário para criar teclado inline a partir de lista de opções [(texto, callback_data)]
def build_keyboard(options):
    keyboard = []
    for text, callback_data in options:
        keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    return InlineKeyboardMarkup(keyboard)


# Função para iniciar o bot /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = context.user_data.get("username")

    if username and username in backend.USUARIOS:
        await update.message.reply_text(
            f"Olá de novo, {username.title()}! Vamos para o menu principal.",
        )
        return await menu_principal(update, context)
    else:
        await update.message.reply_text(
            "Olá! Bem-vindo ao Controle Financeiro.\nPor favor, digite a palavra-passe para continuar."
        )
        return ASK_PASSPHRASE


# Recebe e valida a palavra-passe global
async def receber_passphrase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if backend.validar_palavra_passe(texto):
        await update.message.reply_text("Palavra-passe correta! Agora escolha seu nome de usuário:")
        return ASK_USERNAME
    else:
        await update.message.reply_text("Palavra-passe incorreta. Tente novamente ou /cancel para sair.")
        return ASK_PASSPHRASE


# Recebe nome de usuário para cadastro
async def receber_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().lower()
    if username in backend.USUARIOS:
        await update.message.reply_text("Este nome já está em uso. Por favor, escolha outro.")
        return ASK_USERNAME
    context.user_data["username"] = username
    await update.message.reply_text("Ótimo! Agora, escolha uma senha para seu login:")
    return ASK_PASSWORD


# Recebe a senha para cadastro
async def receber_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    senha = update.message.text.strip()
    username = context.user_data.get("username")
    success, msg = backend.registrar_novo_usuario(username, senha)
    if success:
        await update.message.reply_text(f"Usuário '{username}' criado com sucesso! Faça login com /login.")
        return ConversationHandler.END
    else:
        await update.message.reply_text(f"Erro no cadastro: {msg}. Tente /start novamente.")
        return ConversationHandler.END


# Comando /login para autenticar usuário existente
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("username"):
        await update.message.reply_text(f"Você já está logado como {context.user_data['username']}. Use /menu para opções.")
        return ConversationHandler.END
    await update.message.reply_text("Por favor, digite seu nome de usuário:")
    return ASK_USERNAME


# Recebe usuário no login
async def receber_username_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().lower()
    if username not in backend.USUARIOS:
        await update.message.reply_text("Usuário não encontrado. Use /start para criar uma nova conta.")
        return ConversationHandler.END
    context.user_data["username"] = username
    await update.message.reply_text("Agora digite sua senha:")
    return ASK_PASSWORD


# Recebe senha no login
async def receber_password_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    senha = update.message.text.strip()
    username = context.user_data.get("username")
    if backend.verificar_senha(username, senha):
        await update.message.reply_text(f"Login efetuado com sucesso! Bem-vindo, {username.title()}!")
        return await menu_principal(update, context)
    else:
        await update.message.reply_text("Senha incorreta. Tente novamente ou use /start para reiniciar.")
        return ConversationHandler.END


# Menu principal
async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "=== MENU PRINCIPAL ===\n"
        "Escolha uma opção:\n\n"
        "1️⃣ Sobre o Projeto\n"
        "2️⃣ Categorias\n"
        "3️⃣ Orçamentos\n"
        "4️⃣ Transações\n"
        "5️⃣ Meu Login\n"
        "6️⃣ Sair (/cancel)"
    )
    keyboard = build_keyboard([
        ("Sobre o Projeto", "sobre_projeto"),
        ("Categorias", "menu_categorias"),
        ("Orçamentos", "menu_orcamentos"),
        ("Transações", "menu_transacoes"),
        ("Meu Login", "menu_login"),
        ("Sair", "sair"),
    ])
    if update.callback_query:
        await update.callback_query.edit_message_text(texto, reply_markup=keyboard)
    else:
        await update.message.reply_text(texto, reply_markup=keyboard)
    return MENU


# Callback handler para menu principal e submenus
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    username = context.user_data.get("username")

    if not username:
        await query.edit_message_text("Você precisa estar logado para usar o bot. Use /start para começar.")
        return ConversationHandler.END

    # Menu principal
    if data == "sobre_projeto":
        texto = (
            "💡 Projeto Controle Financeiro\n"
            "Feito para ajudar você a controlar suas finanças com simplicidade.\n"
            "Funciona no Telegram e no app Streamlit.\n"
            "Desenvolvido por Gus. 🚀"
        )
        await query.edit_message_text(texto)
        return MENU

    elif data == "menu_categorias":
        texto = "📂 Categorias:\nEscolha uma opção:"
        keyboard = build_keyboard([
            ("Listar Categorias", "listar_categorias"),
            ("Adicionar Nova Categoria", "adicionar_categoria"),
            ("Editar Categoria", "editar_categoria"),
            ("Remover Categoria", "remover_categoria"),
            ("Voltar ao Menu Principal", "voltar_menu"),
        ])
        await query.edit_message_text(texto, reply_markup=keyboard)
        return SUBMENU_CATEGORIAS

    elif data == "menu_orcamentos":
        texto = "📊 Orçamentos:\nEscolha uma opção:"
        keyboard = build_keyboard([
            ("Listar Orçamentos", "listar_orcamentos"),
            ("Editar Orçamentos", "editar_orcamentos"),
            ("Visualizar Alertas", "alertas_orcamentos"),
            ("Voltar ao Menu Principal", "voltar_menu"),
        ])
        await query.edit_message_text(texto, reply_markup=keyboard)
        return SUBMENU_ORCAMENTOS

    elif data == "menu_transacoes":
        texto = "💰 Transações:\nEscolha uma opção:"
        keyboard = build_keyboard([
            ("Visualizar Extrato", "visualizar_extrato"),
            ("Adicionar Nova Transação", "adicionar_transacao"),
            ("Editar Transação", "editar_transacao"),
            ("Remover Transação", "remover_transacao"),
            ("Voltar ao Menu Principal", "voltar_menu"),
        ])
        await query.edit_message_text(texto, reply_markup=keyboard)
        return SUBMENU_TRANSACOES

    elif data == "menu_login":
        texto = "👤 Meu Login:\nEscolha uma opção:"
        keyboard = build_keyboard([
            ("Exibir Nome de Usuário/Persona", "exibir_usuario"),
            ("Alterar Senha", "alterar_senha"),
            ("Informações da Conta", "info_conta"),
            ("Voltar ao Menu Principal", "voltar_menu"),
        ])
        await query.edit_message_text(texto, reply_markup=keyboard)
        return MENU

    elif data == "sair":
        await query.edit_message_text("Você saiu do bot. Para voltar, use /start.")
        context.user_data.clear()
        return ConversationHandler.END

    elif data == "voltar_menu":
        return await menu_principal(update, context)


    # --- SUBMENU CATEGORIAS ---
    if data == "listar_categorias":
        categorias = backend.carregar_categorias()
        if categorias:
            texto = "Categorias atuais:\n" + "\n".join(f"- {c['nome']}" for c in categorias)
        else:
            texto = "Nenhuma categoria cadastrada."
        await query.edit_message_text(texto)
        return SUBMENU_CATEGORIAS

    elif data == "adicionar_categoria":
        await query.edit_message_text("Digite o nome da nova categoria:")
        return ADICIONAR_CATEGORIA_NOME

    elif data == "editar_categoria":
        await query.edit_message_text("Digite o nome da categoria que deseja editar:")
        return EDITAR_CATEGORIA_ANTIGO

    elif data == "remover_categoria":
        await query.edit_message_text("Digite o nome da categoria que deseja remover:")
        return REMOVER_CATEGORIA_NOME

    # --- SUBMENU ORÇAMENTOS ---
    elif data == "listar_orcamentos":
        orcamentos = backend.carregar_orcamentos(username)
        if orcamentos:
            texto = "Orçamentos atuais:\n" + "\n".join(f"- {cat}: R$ {valor:.2f}" for cat, valor in orcamentos.items())
        else:
            texto = "Nenhum orçamento definido."
        await query.edit_message_text(texto)
        return SUBMENU_ORCAMENTOS

    elif data == "editar_orcamentos":
        await query.edit_message_text("Editar orçamentos ainda não implementado via bot. Use o app web para isso.")
        return SUBMENU_ORCAMENTOS

    elif data == "alertas_orcamentos":
        await query.edit_message_text("Alertas de orçamentos ainda não implementados via bot. Use o app web para isso.")
        return SUBMENU_ORCAMENTOS


    # --- SUBMENU TRANSACOES ---
    elif data == "visualizar_extrato":
        transacoes = backend.carregar_dados(username)
        if not transacoes:
            texto = "Nenhuma transação encontrada."
        else:
            texto = "Extrato (últimas 10 transações):\n"
            for t in transacoes[-10:]:
                texto += f"- {t['data']} | {t['categoria']} | R$ {t['valor']:.2f} | {t['descricao']} | {t['tipo']}\n"
        await query.edit_message_text(texto)
        return SUBMENU_TRANSACOES

    elif data == "adicionar_transacao":
        await query.edit_message_text("Vamos adicionar uma nova transação!\nDigite o valor (use negativo para despesa):")
        return REGISTRAR_TRANSACAO_VALOR

    elif data == "editar_transacao":
        transacoes = backend.carregar_dados(username)
        if not transacoes:
            await query.edit_message_text("Nenhuma transação para editar.")
            return SUBMENU_TRANSACOES
        texto = "Escolha a transação para editar (responda com o número):\n"
        for idx, t in enumerate(transacoes, 1):
            texto += f"{idx}. {t['data']} | {t['categoria']} | R$ {t['valor']:.2f} | {t['descricao']}\n"
        context.user_data["transacoes_para_editar"] = transacoes
        await query.edit_message_text(texto)
        return ESCOLHER_TRANSACAO_EDITAR

    elif data == "remover_transacao":
        transacoes = backend.carregar_dados(username)
        if not transacoes:
            await query.edit_message_text("Nenhuma transação para remover.")
            return SUBMENU_TRANSACOES
        texto = "Escolha a transação para remover (responda com o número):\n"
        for idx, t in enumerate(transacoes, 1):
            texto += f"{idx}. {t['data']} | {t['categoria']} | R$ {t['valor']:.2f} | {t['descricao']}\n"
        context.user_data["transacoes_para_remover"] = transacoes
        await query.edit_message_text(texto)
        return REMOVER_TRANSACAO_ESCOLHA


    # --- SUBMENU LOGIN ---
    elif data == "exibir_usuario":
        info = backend.get_usuario_info(username)
        if info:
            texto = f"Seu nome de usuário: {info['username']}\nID: {info['id']}\nCriado em: {info['data_criacao']}"
        else:
            texto = "Informações do usuário não encontradas."
        await query.edit_message_text(texto)
        return MENU

    elif data == "alterar_senha":
        await query.edit_message_text("Digite sua senha atual:")
        return EDITAR_SENHA_OLD

    elif data == "info_conta":
        info = backend.get_usuario_info(username)
        texto = f"ID: {info['id']}\nData de criação: {info['data_criacao']}\nUso das funcionalidades:\n"
        for uso in info.get("uso_funcionalidades", []):
            texto += f"- {uso['funcionalidade']} em {uso['timestamp']}\n"
        await query.edit_message_text(texto)
        return MENU

    # Se não bater com nada:
    await query.edit_message_text("Opção não reconhecida, retornando ao menu principal.")
    return await menu_principal(update, context)


# --- Conversas para transações ---

async def reg_trans_valor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip().replace(",", ".")
    try:
        valor = float(texto)
        context.user_data["nova_trans_valor"] = valor
        await update.message.reply_text("Agora digite a categoria:")
        return REGISTRAR_TRANSACAO_CATEGORIA
    except:
        await update.message.reply_text("Valor inválido. Digite um número válido (ex: 100 ou -50):")
        return REGISTRAR_TRANSACAO_VALOR


async def reg_trans_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categoria = update.message.text.strip().title()
    if categoria not in backend.CATEGORIAS:
        await update.message.reply_text(f"Categoria '{categoria}' inválida. Tente novamente:")
        return REGISTRAR_TRANSACAO_CATEGORIA
    context.user_data["nova_trans_categoria"] = categoria
    await update.message.reply_text("Digite uma descrição (ou deixe em branco):")
    return REGISTRAR_TRANSACAO_DESCRICAO


async def reg_trans_descricao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    descricao = update.message.text.strip()
    context.user_data["nova_trans_descricao"] = descricao
    await update.message.reply_text("Por fim, escolha o tipo: Necessidade, Desejo ou Receita")
    return REGISTRAR_TRANSACAO_TIPO


async def reg_trans_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tipo = update.message.text.strip().title()
    if tipo not in ["Necessidade", "Desejo", "Receita"]:
        await update.message.reply_text("Tipo inválido. Digite Necessidade, Desejo ou Receita:")
        return REGISTRAR_TRANSACAO_TIPO
    context.user_data["nova_trans_tipo"] = tipo
    # Agora salva a transação
    username = context.user_data.get("username")
    valor = context.user_data.get("nova_trans_valor")
    categoria = context.user_data.get("nova_trans_categoria")
    descricao = context.user_data.get("nova_trans_descricao")
    success = backend.adicionar_transacao(username, valor, categoria, descricao, tipo)
    if success:
        await update.message.reply_text("Transação adicionada com sucesso!")
    else:
        await update.message.reply_text("Erro ao adicionar transação.")
    return await menu_principal(update, context)


# --- Conversas para editar senha ---

async def senha_antiga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["senha_antiga"] = update.message.text.strip()
    await update.message.reply_text("Digite a nova senha:")
    return EDITAR_SENHA_NEW


async def senha_nova(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["senha_nova"] = update.message.text.strip()
    await update.message.reply_text("Confirme a nova senha:")
    return EDITAR_SENHA_CONFIRM


async def senha_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nova = context.user_data.get("senha_nova")
    confirm = update.message.text.strip()
    username = context.user_data.get("username")
    antiga = context.user_data.get("senha_antiga")
    if nova != confirm:
        await update.message.reply_text("As senhas não coincidem. Tente novamente /menu e Alterar Senha.")
        return ConversationHandler.END
    success, msg = backend.alterar_senha(username, antiga, nova)
    if success:
        await update.message.reply_text("Senha alterada com sucesso!")
    else:
        await update.message.reply_text(f"Erro: {msg}")
    return await menu_principal(update, context)


# --- Conversas para categorias ---

async def adicionar_categoria_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = update.message.text.strip()
    success, msg = backend.adicionar_categoria(nome)
    await update.message.reply_text(msg)
    return await menu_principal(update, context)


async def editar_categoria_antigo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome_antigo = update.message.text.strip()
    context.user_data["editar_categoria_antigo"] = nome_antigo
    await update.message.reply_text("Digite o novo nome para a categoria:")
    return EDITAR_CATEGORIA_NOVO


async def editar_categoria_novo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome_novo = update.message.text.strip()
    nome_antigo = context.user_data.get("editar_categoria_antigo")
    success, msg = backend.editar_categoria(nome_antigo, nome_novo)
    await update.message.reply_text(msg)
    return await menu_principal(update, context)


async def remover_categoria_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = update.message.text.strip()
    success, msg = backend.deletar_categoria(nome)
    await update.message.reply_text(msg)
    return await menu_principal(update, context)


# --- Conversas para remover transação ---

async def remover_transacao_escolha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    transacoes = context.user_data.get("transacoes_para_remover", [])
    try:
        idx = int(texto) - 1
        if 0 <= idx < len(transacoes):
            id_para_remover = transacoes[idx]["id"]
            username = context.user_data.get("username")
            sucesso = backend.deletar_transacao(username, id_para_remover)
            if sucesso:
                await update.message.reply_text("Transação removida com sucesso!")
            else:
                await update.message.reply_text("Erro ao remover transação.")
        else:
            await update.message.reply_text("Número inválido, tente novamente.")
            return REMOVER_TRANSACAO_ESCOLHA
    except:
        await update.message.reply_text("Número inválido, tente novamente.")
        return REMOVER_TRANSACAO_ESCOLHA
    return await menu_principal(update, context)


# --- Conversas para escolher transação para editar ---

async def escolher_transacao_editar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    transacoes = context.user_data.get("transacoes_para_editar", [])
    try:
        idx = int(texto) - 1
        if 0 <= idx < len(transacoes):
            transacao = transacoes[idx]
            context.user_data["transacao_edicao"] = transacao
            # Menu campo para editar
            teclado = build_keyboard([
                ("Valor", "edit_valor"),
                ("Categoria", "edit_categoria"),
                ("Descrição", "edit_descricao"),
                ("Tipo", "edit_tipo"),
                ("Data", "edit_data"),
                ("Cancelar", "cancelar_edicao"),
            ])
            await update.message.reply_text("Escolha o campo para editar:", reply_markup=teclado)
            return EDITAR_TRANSACAO_CAMPO
        else:
            await update.message.reply_text("Número inválido, tente novamente.")
            return ESCOLHER_TRANSACAO_EDITAR
    except:
        await update.message.reply_text("Número inválido, tente novamente.")
        return ESCOLHER_TRANSACAO_EDITAR


# --- Callbacks para editar campos da transação ---

async def editar_transacao_campo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    escolha = query.data
    if escolha == "cancelar_edicao":
        await query.edit_message_text("Edição cancelada.")
        return await menu_principal(update, context)

    context.user_data["campo_para_editar"] = escolha
    await query.edit_message_text(f"Digite o novo valor para {escolha.replace('edit_', '')}:")
    return {
        "edit_valor": EDITAR_TRANSACAO_VALOR,
        "edit_categoria": EDITAR_TRANSACAO_CATEGORIA,
        "edit_descricao": EDITAR_TRANSACAO_DESCRICAO,
        "edit_tipo": EDITAR_TRANSACAO_TIPO,
        "edit_data": EDITAR_TRANSACAO_DATA,
    }[escolha]


async def editar_transacao_valor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip().replace(",", ".")
    try:
        valor = float(texto)
        transacao = context.user_data.get("transacao_edicao")
        username = context.user_data.get("username")
        campo = context.user_data.get("campo_para_editar")
        success, msg = backend.editar_transacao(username, transacao["id"], novo_valor=valor)
        await update.message.reply_text(msg if success else "Erro ao editar valor.")
    except:
        await update.message.reply_text("Valor inválido, tente novamente.")
        return EDITAR_TRANSACAO_VALOR
    return await menu_principal(update, context)


async def editar_transacao_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categoria = update.message.text.strip().title()
    if categoria not in backend.CATEGORIAS:
        await update.message.reply_text("Categoria inválida, tente novamente.")
        return EDITAR_TRANSACAO_CATEGORIA
    transacao = context.user_data.get("transacao_edicao")
    username = context.user_data.get("username")
    success, msg = backend.editar_transacao(username, transacao["id"], nova_categoria=categoria)
    await update.message.reply_text(msg if success else "Erro ao editar categoria.")
    return await menu_principal(update, context)


async def editar_transacao_descricao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    descricao = update.message.text.strip()
    transacao = context.user_data.get("transacao_edicao")
    username = context.user_data.get("username")
    success, msg = backend.editar_transacao(username, transacao["id"], nova_descricao=descricao)
    await update.message.reply_text(msg if success else "Erro ao editar descrição.")
    return await menu_principal(update, context)


async def editar_transacao_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tipo = update.message.text.strip().title()
    if tipo not in ["Necessidade", "Desejo", "Receita"]:
        await update.message.reply_text("Tipo inválido, tente novamente (Necessidade, Desejo, Receita):")
        return EDITAR_TRANSACAO_TIPO
    transacao = context.user_data.get("transacao_edicao")
    username = context.user_data.get("username")
    success, msg = backend.editar_transacao(username, transacao["id"], novo_tipo=tipo)
    await update.message.reply_text(msg if success else "Erro ao editar tipo.")
    return await menu_principal(update, context)


async def editar_transacao_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data_str = update.message.text.strip()
    # Validação simples da data no formato YYYY-MM-DD
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", data_str):
        await update.message.reply_text("Data inválida, use o formato YYYY-MM-DD:")
        return EDITAR_TRANSACAO_DATA
    transacao = context.user_data.get("transacao_edicao")
    username = context.user_data.get("username")
    success, msg = backend.editar_transacao(username, transacao["id"], nova_data=data_str)
    await update.message.reply_text(msg if success else "Erro ao editar data.")
    return await menu_principal(update, context)


# Comando /cancel para sair da conversa
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operação cancelada. Use /menu para voltar ao menu principal.")
    return ConversationHandler.END


def main():
    TOKEN = "8157010184:AAH1tOloCjmcXl5820q-DzSADFOpjK8CFwQ"

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("login", login)],
        states={
            ASK_PASSPHRASE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_passphrase)],
            ASK_USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_username),
                # login
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_username_login),
            ],
            ASK_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_password),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_password_login),
            ],
            MENU: [
                CallbackQueryHandler(menu_callback)
            ],
            SUBMENU_CATEGORIAS: [
                CallbackQueryHandler(menu_callback),
                MessageHandler(filters.TEXT & ~filters.COMMAND, adicionar_categoria_nome),
                MessageHandler(filters.TEXT & ~filters.COMMAND, editar_categoria_antigo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, remover_categoria_nome),
            ],
            SUBMENU_ORCAMENTOS: [CallbackQueryHandler(menu_callback)],
            SUBMENU_TRANSACOES: [
                CallbackQueryHandler(menu_callback),
                MessageHandler(filters.TEXT & ~filters.COMMAND, escolher_transacao_editar),
                MessageHandler(filters.TEXT & ~filters.COMMAND, remover_transacao_escolha),
            ],
            REGISTRAR_TRANSACAO_VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_trans_valor)],
            REGISTRAR_TRANSACAO_CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_trans_categoria)],
            REGISTRAR_TRANSACAO_DESCRICAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_trans_descricao)],
            REGISTRAR_TRANSACAO_TIPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_trans_tipo)],
            EDITAR_SENHA_OLD: [MessageHandler(filters.TEXT & ~filters.COMMAND, senha_antiga)],
            EDITAR_SENHA_NEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, senha_nova)],
            EDITAR_SENHA_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, senha_confirm)],
            EDITAR_CATEGORIA_ANTIGO: [MessageHandler(filters.TEXT & ~filters.COMMAND, editar_categoria_antigo)],
            EDITAR_CATEGORIA_NOVO: [MessageHandler(filters.TEXT & ~filters.COMMAND, editar_categoria_novo)],
            REMOVER_CATEGORIA_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, remover_categoria_nome)],
            REMOVER_TRANSACAO_ESCOLHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, remover_transacao_escolha)],
            ESCOLHER_TRANSACAO_EDITAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, escolher_transacao_editar)],
            EDITAR_TRANSACAO_CAMPO: [CallbackQueryHandler(editar_transacao_campo_callback)],
            EDITAR_TRANSACAO_VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, editar_transacao_valor)],
            EDITAR_TRANSACAO_CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, editar_transacao_categoria)],
            EDITAR_TRANSACAO_DESCRICAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, editar_transacao_descricao)],
            EDITAR_TRANSACAO_TIPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, editar_transacao_tipo)],
            EDITAR_TRANSACAO_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, editar_transacao_data)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)

    app.run_polling()


if __name__ == "__main__":
    main()
