import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
#LLM
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEndpoint
from sentence_transformers import CrossEncoder

# Параметры
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
FAISS_PATH = "../task3_build_index/faiss_index"
LLM_MODEL = "gpt-3.5-turbo"

# Загрузка модели (легкая, работает на CPU за ~50-100 мс)
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank_and_filter(query: str, docs: list, top_k: int = 3, threshold: float = 0.5):
    if not docs:
        return []
    
    # 1. Формируем пары [вопрос, текст_чанка]
    pairs = [[query, doc.page_content] for doc in docs]
    
    # 2. Получаем скоры релевантности
    scores = cross_encoder.predict(pairs)
    
    # 3. Фильтруем по порогу и сортируем
    scored_docs = list(zip(docs, scores))
    filtered = [doc for doc, score in scored_docs if score >= threshold]
    filtered.sort(key=lambda x: scores[docs.index(x[0])], reverse=True)
    
    return [doc for doc, _ in filtered[:top_k]]


# 1. Загрузка эмбеддингов и векторной БД
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
db = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)

# 2. LLM
#llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
# Вариант 1: Ollama (бесплатно, локально) GGUF ~1.8–2.2 ГБ Мультиязычность: 30+ языков
#ollama pull llama3.2:3b
#ollama run llama3.2:3b
llm = ChatOllama(
    model="llama3.2:3b",
    temperature=0.1,           # Чуть больше свободы
    repeat_penalty=1.05,       # Мягкий штраф
    num_predict=400,           # Чуть длиннее ответы
    stop=["\n\nЗапрос:"]       # Оставьте только один стоп-токен
)

# Вариант 2: Hugging Face (бесплатно, но медленнее) GGUF ~4.1–4.8 ГБ Мультиязычность: Преимущественно английский
# llm = HuggingFaceEndpoint(repo_id="mistralai/Mistral-7B-Instruct-v0.2")


# 3. Промпт (Few-shot + Chain-of-Thought)
PROMPT_TEMPLATE = """
System: Ты помощник, который сначала размышляет, а потом отвечает. Всегда пиши свои шаги.
ВАЖНО: 
- Отвечай ТОЛЬКО на основе Контекста ниже.
- Отвечай на русском, но сохраняй оригинальные термины из базы (Xarn Velgor, Synth Flux)
- Если в Контексте нет информации — пиши «Я не знаю». 
- Не используй знания извне, даже если вопрос кажется знакомым.

Контекст:
{context}

Примеры:
Вопрос: Кто такой Xarn Velgor?
Ответ: 1. Ищу в базе упоминание «Xarn Velgor». 2. Нахожу запись: «Бывший адепт Order of Lumin, перешедший на сторону Covenant of Ash». 3. Ответ: Xarn Velgor — бывший адепт Order of Lumin, ныне представитель Covenant of Ash.

Вопрос: Где находится столица Qolid Cazesa?
Ответ: 1. Анализирую запрос о столице. 2. В документации указано: «Zenith Prime — центр политического управления Qolid Cazesa». 3. Ответ: Столица — Zenith Prime.

Вопрос: Что такое Phase Blade?
Ответ: 1. Проверяю технические термины. 2. В мануале: «Phase Blade — энергетическое оружие адептов Order of Lumin, активируемое через Synth Flux». 3. Ответ: Phase Blade — энергетическое оружие адептов Order of Lumin, активируемое через Synth Flux.

Вопрос: {input}
Ответ: Дай краткий ответ. Не повторяй фразы."""

prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)

# 4. Сборка пайплайна RAG (LCEL API)
retriever = db.as_retriever(search_kwargs={"k": 3})

def format_docs(docs):
    return "\n\n".join([doc.page_content for doc in docs])

def retrieve_and_rerank(query: str):
    raw_docs = retriever.invoke(query)          # FAISS: быстро ищем 10 чанков
    filtered_docs = rerank_and_filter(query, raw_docs) # CrossEncoder: оставляем 3 лучших
    return format_docs(filtered_docs)

rag_chain = (
    {"context": RunnablePassthrough().assign(context=retrieve_and_rerank), 
     "input": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 5. REPL-интерфейс
def main():
    print("RAG-бот запущен. Введите 'выход' для остановки.")
    while True:
        q = input("\nЗапрос: ").strip()
        if q.lower() in ("выход", "exit"): break
        if not q: continue
        try:
            # 1. Проверяем, что нашёл retriever
            docs = retriever.invoke(q)
            print(f"\n[DEBUG] Найдено чанков: {len(docs)}")
            for i, d in enumerate(docs):
                source = d.metadata.get("source", "unknown")
                print(f"--- Чанк {i+1} ({source}) ---\n{d.page_content[:200]}...\n")

            # 2. Запускаем полную цепочку RAG
            res = rag_chain.invoke(q)
            print(res)
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()