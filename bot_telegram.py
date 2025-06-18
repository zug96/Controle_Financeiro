import logging
import re
import json
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)

# Agora importamos todas as funções que o bot irá precisar
from finance_utils import (
    adicionar_transacao,
    carregar_categorias,
    adicionar_categoria, # <-- Importante para o novo comando
    registrar_novo_usuario,
    get_user_from_telegram_id,
    map_telegram_id_to_user
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONSTANTES DE CONFIGURAÇÃO ---
TOKEN = "8157010184:AAH1tOloCjmcXl5820q-DzSADFOpjK8CFwQ"
PALAVRA_PASSE_GLOBAL = "GUS2025" # Mude para sua senha de acesso

# --- ESTADOS DA CONVERSA DE REGISTRO ---
ASK_PASSPHRASE, ASK_USERNAME, ASK_PASSWORD = range(3)

# --- FUNÇÕES AUXILIARES (Movidas para finance_utils, mas deixadas aqui caso precise) ---
MAPA_USUARIOS_ARQUIVO = Path("usuarios_telegram.json")
def carregar_mapa_usuarios():
    if MAPA_USUARIOS_ARQUIVO.exists():
        if MAPA_USUARIOS_ARQUIVO.stat().st_size == 0: return {}
        with open(MAPA_USUARIOS_ARQUIVO, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except json.JSONDecodeError: return {}
    return {}

def salvar_mapa_usuarios(mapa):
    with open(MAPA_USUARIOS_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(mapa, f, indent=2)

# --- LÓGICA DO BOT ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    username = get_user_from_telegram_id(user_id)
    if username:
        await update.message.reply_text(f"Olá de volta, {username.title()}! 👋\nEstou pronto para registrar suas transações.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Olá! Bem-vindo ao Controle Financeiro. Para começar, digite a palavra-passe de acesso.")
        return ASK_PASSPHRASE

async def receber_passphrase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.strip().upper() == PALAVRA_PASSE_GLOBAL.upper():
        await update.message.reply_text("Ótimo! Acesso concedido.\n\nComo você gostaria de ser chamado(a) no sistema?")
        return ASK_USERNAME
    else:
        await update.message.reply_text("Palavra-passe incorreta. Acesso negado. ⛔")
        return ConversationHandler.END

async def receber_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['username'] = update.message.text.strip().lower()
    await update.message.reply_text(f"Entendido, {context.user_data['username'].title()}! Agora, crie uma senha pessoal para usar no app web.")
    return ASK_PASSWORD

async def receber_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    username = context.user_data['username']
    password = update.message.text
    user_id = update.effective_user.id
    success, message = registrar_novo_usuario(username, password)
    if success:
        map_telegram_id_to_user(user_id, username)
        await update.message.reply_text(f"✅ Perfeito! Sua persona '{username.title()}' foi criada. A partir de agora, eu te reconhecerei automaticamente. Pode começar a registrar transações!")
        return ConversationHandler.END
    else:
        await update.message.reply_text(f"❌ Erro: {message} Por favor, inicie o processo novamente com /start e escolha outro nome.")
        return ConversationHandler.END

async def registrar_transacao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = get_user_from_telegram_id(user_id)
    if not username:
        await update.message.reply_text("Não te reconheci. Por favor, use /start para se registrar.")
        return
    texto = update.message.text.lower()
    match_valor = re.search(r'[\d,.]+', texto)
    if not match_valor:
        await update.message.reply_text("Não consegui encontrar um valor numérico na sua mensagem. 😕")
        return
    valor_str = match_valor.group().replace(',', '.')
    valor = float(valor_str)
    palavras_receita = ['recebi', 'salario', 'salário', 'ganhei']
    tipo = "Receita" if any(p in texto for p in palavras_receita) else "Desejo"
    if tipo != "Receita": valor = -abs(valor)
    categorias_db = carregar_categorias()
    categorias_nomes = [cat['nome'] for cat in categorias_db]
    categoria_encontrada = "Extras"
    for cat in categorias_nomes:
        if cat.lower() in texto:
            categoria_encontrada = cat
            break
    if adicionar_transacao(username, valor, categoria_encontrada, update.message.text, tipo):
        valor_formatado = f"R$ {abs(valor):.2f}".replace('.', ',')
        tipo_str = "Receita" if valor > 0 else "Despesa"
        await update.message.reply_text(f"✅ Transação registrada para {username.title()}!\n<b>{tipo_str}</b>: {valor_formatado} em {categoria_encontrada}", parse_mode='HTML')
    else:
        await update.message.reply_text("Ocorreu um erro ao salvar sua transação no banco de dados.")

# --- NOVAS FUNÇÕES DE CATEGORIA ---

async def listar_categorias(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lista todas as categorias disponíveis no banco de dados."""
    categorias_db = carregar_categorias()
    if not categorias_db:
        await update.message.reply_text("Nenhuma categoria cadastrada ainda. Use /novacategoria <Nome> para adicionar uma.")
        return
    
    nomes_categorias = [cat['nome'] for cat in categorias_db]
    categorias_str = "\n - ".join(sorted(nomes_categorias))
    await update.message.reply_text(f"📋 Categorias disponíveis:\n - {categorias_str}")

async def nova_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Adiciona uma nova categoria via comando do bot."""
    # Verifica se o usuário está 'logado' no bot (se já se registrou)
    user_id = update.effective_user.id
    username = get_user_from_telegram_id(user_id)
    if not username:
        await update.message.reply_text("Você precisa se registrar primeiro. Use /start para começar.")
        return

    if not context.args:
        await update.message.reply_text("Uso: /novacategoria <Nome da Categoria>")
        return

    nome_categoria = " ".join(context.args)
    success, message = adicionar_categoria(nome_categoria)
    
    if success:
        await update.message.reply_text(f"✅ Categoria '{nome_categoria.title()}' adicionada com sucesso!")
    else:
        await update.message.reply_text(f"ℹ️ {message}")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Processo de registro cancelado.")
    return ConversationHandler.END


def main() -> None:
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_PASSPHRASE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_passphrase)],
            ASK_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_username)],
            ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    # Adicionando os handlers para os comandos de categoria
    application.add_handler(CommandHandler("listarcategorias", listar_categorias))
    application.add_handler(CommandHandler("novacategoria", nova_categoria))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, registrar_transacao))

    print("Bot finalizado e pronto para produção! Pressione Ctrl+C para parar.")
    application.run_polling()


if __name__ == "__main__":
    main()
