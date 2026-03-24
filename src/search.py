import os

from langchain_postgres import PGVector
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from dotenv import load_dotenv

load_dotenv()

# Variáveis globais
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
PG_VECTOR_COLLECTION_NAME = os.getenv("PG_VECTOR_COLLECTION_NAME")
DATABASE_URL = os.getenv("DATABASE_URL")




PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""

def search_prompt(question=None):
  embeddings = OllamaEmbeddings(model=OLLAMA_EMBED_MODEL)
  llm_en = ChatOllama(model="llama3", temperature=0.5)

  store = PGVector(
    collection_name=PG_VECTOR_COLLECTION_NAME,
    connection=DATABASE_URL,
    embeddings=embeddings,
    use_jsonb=True
  )

  docs = store.similarity_search(question, k=10)

  map_prompt = PromptTemplate.from_template(
    "Resuma de forma objetiva o trecho abaixo em portugues:\n\n{context}"
  )
  map_chain = map_prompt | llm_en | StrOutputParser()
  #print(f"map_chain: {map_chain}")
  #print("=" * 80)

  prepare_map_inputs = RunnableLambda(
    lambda retrieved_docs: [{"context": doc.page_content} for doc in retrieved_docs]
  )
  #print(f"prepare_map_inputs: {prepare_map_inputs}")
  #print("=" * 80)
  map_stage = prepare_map_inputs | map_chain.map()
  #print(f"map_stage: {map_stage}")
  #print("=" * 80)
  # Aqui {pergunta} e {contexto} do PROMPT_TEMPLATE sao preenchidos.
  reduce_prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
  reduce_chain = reduce_prompt | llm_en | StrOutputParser()
  #print(f"reduce_chain: {reduce_chain}")
  #print("=" * 80)
  prepare_reduce_inputs = RunnableLambda(
    lambda summaries: {
      "contexto": "\n\n".join(summaries),
      "pergunta": question,
    }
  )

  #print(f"prepare_reduce_inputs: {prepare_reduce_inputs}")
  #print("=" * 80)
  
  pipeline = map_stage | prepare_reduce_inputs | reduce_chain
  result = pipeline.invoke(docs)
  print(result)
  return result
  

if __name__ == "__main__":
  #search_prompt("Qual o faturamento da Empresa SuperTechIABrazil?")
  search_prompt("Qual é a capital da França?")