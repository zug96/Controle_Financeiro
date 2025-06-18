import pandas as pd
from datetime import datetime

# 🔁 DADOS FINANCEIROS (atualize conforme quiser)
dados = {
    "Data": [
        "2025-06-18", "2025-06-23", "2025-06-30", "2025-06-28", "2025-07-04",
        "2025-06-18", "2025-06-18", "2025-06-18", "2025-06-18"
    ],
    "Descrição": [
        "Terapia Individual", "Terapia de Casal", "Terapia de Casal", "Parcela Viagem (Duda)",
        "INSS (Auxílio)", "Google One", "Ração Bimo", "Remédios Mensais", "Férias + 1/3 (Líquido)"
    ],
    "Valor": [
        -200.00, -250.00, -250.00, -144.00, 2302.60, -96.99, -120.00, -280.00, 2687.99
    ],
    "Categoria": [
        "Terapia", "Terapia", "Terapia", "Dívidas", "Receita", "Assinaturas",
        "Pets", "Saúde", "Receita"
    ],
    "Forma de Pagamento": [
        "PIX", "PIX", "PIX", "PIX", "Depósito", "Cartão", "Débito", "Débito", "Depósito"
    ],
    "Tipo": [
        "Despesa", "Despesa", "Despesa", "Despesa", "Receita", "Despesa",
        "Despesa", "Despesa", "Receita"
    ]
}

# 📁 Criação do DataFrame
df = pd.DataFrame(dados)

# 📊 Projeção por categoria
df_projecoes = df.groupby("Categoria").agg({
    "Valor": ["sum", "count"]
}).reset_index()
df_projecoes.columns = ["Categoria", "Total Gasto", "Número de Lançamentos"]
df_projecoes["Total Gasto"] = df_projecoes["Total Gasto"].round(2)

# 💾 Exportar para planilha Excel com abas
file_name = "Controle_Financeiro_Gus_Completo.xlsx"
with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:
    df.to_excel(writer, sheet_name="Lançamentos", index=False)
    df_projecoes.to_excel(writer, sheet_name="Projeções", index=False)

print(f"✅ Planilha salva como: {file_name}")
