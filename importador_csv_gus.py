import pandas as pd
from finance_utils import adicionar_transacao, CATEGORIAS
from datetime import datetime
import re

# --- Palavras-chave para classificação automática ---
REGRAS_CATEGORIAS = {
    "Remédios": ["droga", "farmácia", "medic"],
    "Terapia": ["psicóloga", "terapia", "consultório"],
    "Gatos": ["pet", "ração", "bicho", "gato"],
    "Alimentação": ["mercado", "pão", "ifood", "restaurante", "lanchonete"],
    "Assinaturas": ["netflix", "spotify", "google one", "prime"],
    "Estudos": ["curso", "dio", "plataforma"],
    "Viagem": ["passagem", "viagem", "hotel"],
    "Extras": ["presente", "loja", "diversos"],
    "Transporte": ["uber", "99", "ônibus", "combustível"],
    "Salário": ["salário", "pagamento"],
    "INSS": ["inss"],
    "VR": ["caju", "vr"]
}

def classificar_categoria(descricao):
    desc = descricao.lower()
    for categoria, palavras in REGRAS_CATEGORIAS.items():
        if any(p in desc for p in palavras):
            return categoria
    return "Extras"  # categoria padrão


def importar_extrato_csv(caminho_csv):
    df = pd.read_csv(caminho_csv)

    # Ajuste de nomes de colunas se necessário
    colunas_esperadas = ["data", "descricao", "valor"]
    if not all(c in df.columns for c in colunas_esperadas):
        raise ValueError(f"O arquivo CSV deve conter as colunas: {colunas_esperadas}")

    # Limpeza e importação
    for _, row in df.iterrows():
        try:
            data = pd.to_datetime(row["data"]).strftime("%Y-%m-%d")
            valor = float(str(row["valor"]).replace(",", "."))
            descricao = str(row["descricao"]).strip()
            categoria = classificar_categoria(descricao)
            adicionar_transacao(valor=valor, categoria=categoria, descricao=descricao, data_str=data)
        except Exception as e:
            print(f"Erro ao importar linha: {row} => {e}")

    print("Importação concluída com sucesso!")


if __name__ == "__main__":
    caminho = input("Caminho do CSV para importar: ")
    importar_extrato_csv(caminho)
