import os

from langchain_postgres import PGVector
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from dotenv import load_dotenv

load_dotenv()

# Variáveis globais
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
PG_VECTOR_COLLECTION_NAME = os.getenv("PG_VECTOR_COLLECTION_NAME")
DATABASE_URL = os.getenv("DATABASE_URL")

OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-5-nano")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-large")
GOOGLE_CHAT_MODEL = os.getenv("GOOGLE_CHAT_MODEL", "gemini-2.5-flash-lite")
GOOGLE_EMBED_MODEL = os.getenv("GOOGLE_EMBED_MODEL", "models/embedding-001")
SEARCH_SIMILARITY_K = int(os.getenv("SEARCH_SIMILARITY_K", "10"))



PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.
- Se o CONTEXTO trouxer explicitamente o faturamento, responda exatamente no formato:
  "RESPOSTA: O faturamento foi de X reais."
- Substitua apenas X pelo valor exato encontrado no CONTEXTO.

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

def _build_llm(model: str):
  selected = (model or "local").strip().lower()
  if selected == "openai":
    print(f"Usando modelo OpenAI: {OPENAI_CHAT_MODEL}")
    return ChatOpenAI(model=OPENAI_CHAT_MODEL, temperature=0.5)
  if selected == "gemini":
    print(f"Usando modelo Gemini: {GOOGLE_CHAT_MODEL}")
    return ChatGoogleGenerativeAI(model=GOOGLE_CHAT_MODEL, temperature=0.5)
  print(f"Usando modelo Ollama: {OLLAMA_CHAT_MODEL}")
  return ChatOllama(model=OLLAMA_CHAT_MODEL, temperature=0.5)

def _build_embeddings(model: str):
  selected = (model or "local").strip().lower()
  if selected == "openai":
    print(f"Usando Embeddings OpenAI: {OPENAI_EMBED_MODEL}")
    return OpenAIEmbeddings(model=OPENAI_EMBED_MODEL)
  if selected == "gemini":
    print(f"Usando Embeddings Gemini: {GOOGLE_EMBED_MODEL}")
    return GoogleGenerativeAIEmbeddings(model=GOOGLE_EMBED_MODEL)
  print(f"Usando Embeddings Ollama: {OLLAMA_EMBED_MODEL}")
  return OllamaEmbeddings(model=OLLAMA_EMBED_MODEL)


def search_prompt(question=None, model="local"):
  embeddings = OllamaEmbeddings(model=OLLAMA_EMBED_MODEL)
  llm_en = _build_llm(model)

  store = PGVector(
    collection_name=PG_VECTOR_COLLECTION_NAME,
    connection=DATABASE_URL,
    embeddings=embeddings,
    use_jsonb=True
  )

  docs = store.similarity_search(question, k=10)

  # map_prompt = PromptTemplate.from_template(
  #   "Resuma de forma objetiva o trechoResponda à pergunta do usuário utilizando exclusivamente as informações do contexto, considerando valores como faturamento, números e dados financeiros exatamente como apresentados, sem adicionar qualquer informação externa. em portugues:\n\n{context}"
  # )
  map_prompt = PromptTemplate.from_template(
    "Resuma de forma objetiva o trecho abaixo em português, preservando fielmente valores, números e dados financeiros exatamente como aparecem no texto:\n\n{context}"
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
  return result
  

# Estava aqui para testar
# if __name__ == "__main__":
#   search_prompt("Qual o faturamento da Empresa SuperTechIABrazil?")
#   # search_prompt("Qual é a capital da França?")