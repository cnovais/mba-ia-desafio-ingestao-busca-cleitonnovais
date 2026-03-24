from search import search_prompt

def main():
    perguntas_prontas = {
        "1": "Qual o faturamento da Empresa SuperTechIABrazil?",
        "2": "Quantos clientes temos em 2024?",
    }

    while True:
        print("\nEscolha uma opcao:")
        print("Com contexto")
        print("1) Qual o faturamento da Empresa SuperTechIABrazil?")
        print("-" * 80)
        print("E sem contexto")
        print("2) Quantos clientes temos em 2024?")
        print("-" * 80)
        print("0) Digitar pergunta manualmente")
        print("Digite 'sair' para encerrar")

        escolha = input("Opcao: ").strip()
        if escolha.lower() in {"sair", "exit", "quit"}:
            print("Encerrando...")
            break

        if escolha == "0":
            pergunta = input("Você: ").strip()
        else:
            pergunta = perguntas_prontas.get(escolha, "")

        if not pergunta:
            print("Opcao invalida. Tente novamente.")
            continue

        resposta = search_prompt(pergunta)
        print("Sistema:", resposta)

if __name__ == "__main__":
    main()