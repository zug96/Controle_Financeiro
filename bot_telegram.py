import logging
import re
import json
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Importamos todas as funções necessárias do nosso backend
from finance_utils import (
    adicionar_transacao,
    carregar_categorias,
    salvar_categorias,
    registrar_novo_usuario, # Importante!
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONSTANTES DE CONFIGURAÇÃO ---
TOKEN = "8157010184:AAH1tOloCjmcXl5820q-DzSADFOpjK8CFwQ"
PALAVRA_PASSE_GLOBAL = "GUS LINDAO" # Mude para uma senha de sua escolha

# --- ESTADOS DA CONVERSA DE REGISTRO ---
# Usamos números para definir cada passo da conversa
ASK_PASSPHRASE, ASK_USERNAME, ASK_PASSWORD = range(3)

# --- FUNÇÕES AUXILIARES PARA MAPEAMENTO DE USUÁRIOS ---
MAPA_USUARIOS_ARQUIVO = Path("usuarios_telegram.json")

# Versão Nova e Corrigida
def carregar_mapa_usuarios():
    if MAPA_USUARIOS_ARQUIVO.exists():
        # Verifica se o arquivo não está vazio antes de tentar carregar
        if MAPA_USUARIOS_ARQUIVO.stat().st_size == 0:
            return {}
        with open(MAPA_USUARIOS_ARQUIVO, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # O arquivo existe, mas está corrompido ou se tornou vazio
                return {}
    return {}

# --- LÓGICA DO BOT ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia a interação. Verifica se o usuário já é conhecido ou inicia o registro."""
    user_id = str(update.effective_user.id)
    mapa_usuarios = carregar_mapa_usuarios()

    if user_id in mapa_usuarios:
        username = mapa_usuarios[user_id]
        await update.message.reply_text(
            f"Olá de volta, {username.title()}! 👋\n"
            "Estou pronto para registrar suas transações. É só me mandar uma mensagem como `gastei 50 no mercado`."
        )
        return ConversationHandler.END # Encerra a conversa, pois o usuário já é conhecido
    else:
        await update.message.reply_text(
            "Olá! Bem-vindo ao Controle Financeiro familiar.\n"
            "Para garantir que apenas pessoas autorizadas entrem, por favor, digite a palavra-passe de acesso."
        )
        return ASK_PASSPHRASE # Avança para o primeiro passo do registro

async def receber_passphrase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Verifica a palavra-passe geral."""
    if update.message.text.strip().upper() == PALAVRA_PASSE_GLOBAL.upper():
        await update.message.reply_text("Ótimo! Acesso concedido. Agora, vamos criar sua persona.\n\nComo você gostaria de ser chamado(a)? (ex: Gus, Maria, etc.)")
        return ASK_USERNAME # Avança para o próximo passo
    else:
        await update.message.reply_text("Palavra-passe incorreta. Acesso negado. ⛔")
        return ConversationHandler.END

async def receber_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o nome da persona e pede a senha pessoal."""
    context.user_data['username'] = update.message.text.strip().lower()
    await update.message.reply_text(f"Entendido, {context.user_data['username'].title()}! Agora, por favor, crie uma senha pessoal para sua conta. Esta senha será usada no aplicativo web.")
    return ASK_PASSWORD

async def receber_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a senha pessoal, finaliza o registro e salva tudo."""
    username = context.user_data['username']
    password = update.message.text
    user_id = str(update.effective_user.id)
    
    success, message = registrar_novo_usuario(username, password)
    
    if success:
        mapa_usuarios = carregar_mapa_usuarios()
        mapa_usuarios[user_id] = username
        salvar_mapa_usuarios(mapa_usuarios)
        
        await update.message.reply_text(f"✅ Perfeito! Sua persona '{username.title()}' foi criada com sucesso. A partir de agora, eu te reconhecerei automaticamente.\n\nPode começar a registrar suas transações!")
        return ConversationHandler.END
    else:
        # Caso o usuário tente registrar um nome que já existe no sistema
        await update.message.reply_text(f"❌ Erro: {message} Por favor, inicie o processo novamente com /start e escolha outro nome.")
        return ConversationHandler.END

async def registrar_transacao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Registra uma transação para um usuário já conhecido."""
    user_id = str(update.effective_user.id)
    mapa_usuarios = carregar_mapa_usuarios()
    
    if user_id not in mapa_usuarios:
        await update.message.reply_text("Não te reconheci. Por favor, use o comando /start para se registrar.")
        return

    username = mapa_usuarios[user_id]
    # O resto da lógica de registro de transação que já tínhamos...
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

    # Lógica para encontrar categoria (pode ser melhorada no futuro)
    categoria_encontrada = "Extras" # Categoria padrão se nenhuma for encontrada
    for palavra_chave, categoria in KEYWORD_TO_CATEGORY.items():
        if palavra_chave in texto:
            categoria_encontrada = categoria
            break
    
    adicionar_transacao(username, valor, categoria_encontrada, update.message.text, tipo)
    valor_formatado = f"R$ {abs(valor):.2f}".replace('.', ',')
    tipo_str = "Receita" if valor > 0 else "Despesa"
    await update.message.reply_text(f"✅ Transação registrada para {username.title()}!\n<b>{tipo_str}</b>: {valor_formatado} em {categoria_encontrada}", parse_mode='HTML')


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela o processo de registro."""
    await update.message.reply_text("Processo de registro cancelado.")
    return ConversationHandler.END


def main() -> None:
    """Inicia o bot."""
    application = Application.builder().token(TOKEN).build()

    # Handler da conversa de registro
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
    
    # Handler para registrar transações (para usuários já logados)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, registrar_transacao))

    print("Bot iniciado com sucesso! Pressione Ctrl+C para parar.")
    application.run_polling()


if __name__ == "__main__":
    main()
