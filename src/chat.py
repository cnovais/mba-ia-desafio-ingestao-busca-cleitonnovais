from search import search_prompt

def main():
    
    resposta = search_prompt(question="Quantos clientes temos em 2024?")
    # resposta = search_prompt(question="Qual o faturamento da Empresa SuperTechIABrazil?")
    print("Sistema:", resposta)

    if not resposta:
        print("Não foi possível iniciar o chat. Verifique os erros de inicialização.")
        return

if __name__ == "__main__":
    main()