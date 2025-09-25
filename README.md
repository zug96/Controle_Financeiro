# 📊 Controle Financeiro Pessoal

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-orange?style=for-the-badge&logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.2+-blueviolet?style=for-the-badge&logo=pandas&logoColor=white)

Um projeto completo de controle financeiro pessoal desenvolvido em Python, com uma interface web interativa criada com Streamlit e integração com um bot do Telegram para lançamento de transações.

## 🌟 Funcionalidades Principais

-   **Dashboard Interativo:** Visualize suas finanças com gráficos e tabelas através de uma aplicação web (Streamlit).
-   **Importação de Dados:** Carregue transações a partir de arquivos CSV de forma simplificada.
-   **Lançamento via Telegram:** Adicione novas despesas e receitas de forma rápida através de um bot no Telegram.
-   **Análise e Persistência:** Os dados são processados com Pandas e salvos em uma planilha Excel para persistência.
-   **Script de Terminal:** Permite a interação e execução de rotinas diretamente pelo terminal.

## 🛠️ Tecnologias Utilizadas

-   **Linguagem:** Python
-   **Interface Web:** Streamlit
-   **Manipulação de Dados:** Pandas
-   **Bot de Mensagens:** python-telegram-bot
-   **Persistência de Dados:** Openpyxl (para manipulação de arquivos Excel)

## 🚀 Como Instalar e Configurar

Siga os passos abaixo para configurar o ambiente e executar o projeto.

**1. Clone o repositório:**
```bash
git clone [https://github.com/zug96/Controle_Financeiro.git](https://github.com/zug96/Controle_Financeiro.git)
cd Controle_Financeiro
```

**2. Crie e ative um ambiente virtual:**
```bash
# Para Windows
python -m venv venv
venv\Scripts\activate

# Para macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

**3. Instale as dependências:**
```bash
pip install -r requirements.txt
```

**4. Configure as variáveis de ambiente (Opcional, para o Bot):**
Se for utilizar o bot do Telegram, você precisará de um token de API. Recomendo o uso de um arquivo `.env` para armazenar essa chave de forma segura.

## ▶️ Como Executar o Projeto

Você pode interagir com o projeto de três formas diferentes:

**1. Através da Aplicação Web (Streamlit):**
Para iniciar o dashboard interativo, execute o comando:
```bash
streamlit run streamlit_app.py
```
Abra o navegador no endereço local que aparecerá no terminal.

**2. Através do Bot do Telegram:**
Para iniciar o bot e permitir que ele receba mensagens, execute:
```bash
python bot_telegram.py
```

**3. Através do Script de Terminal:**
Para usar as funcionalidades via linha de comando, execute:
```bash
python script_terminal.py
```

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.