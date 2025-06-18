from finance_utils import adicionar_transacao, CATEGORIAS

print("=== Cadastro de Transações via Terminal ===")

# Validação do Valor
while True:
    try:
        valor_str = input("Valor da transação (use '-' para despesa): R$ ").replace(',', '.')
        valor = float(valor_str)
        break
    except ValueError:
        print("Erro: Por favor, digite um número válido (ex: 50.25 ou -100).")

# Validação da Categoria
print("\nCategorias disponíveis:", ", ".join(CATEGORIAS))
while True:
    categoria = input("Categoria: ").strip().title()
    if categoria in CATEGORIAS:
        break
    else:
        print(f"Erro: Categoria '{categoria}' inválida. Por favor, escolha uma da lista acima.")

descricao = input("Descrição: ").strip()

# Adiciona a transação usando a função centralizada
adicionar_transacao(valor=valor, categoria=categoria, descricao=descricao)

print("\nTransação salva com sucesso!")
