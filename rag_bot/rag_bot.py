import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
from sentence_transformers import CrossEncoder

# Параметры
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
FAISS_PATH = "../task3_build_index/faiss_index"

# 1. Загрузка эмбеддингов и векторной БД
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
db = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)

# 2. LLM
llm = ChatOllama(
    # model="llama3.2:3b",
    model="llama3.1:8b",
    temperature=0.1,
    repeat_penalty=1.05,
    num_predict=400,
    stop=["\n\nЗапрос:"]
)

# 3. CrossEncoder для ре-ранжирования
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank_docs(query: str, docs, top_k: int = 3, threshold: float = 0.3):
    if not docs:
        return []
    pairs = [[query, doc.page_content] for doc in docs]
    scores = cross_encoder.predict(pairs)
    scored = list(zip(docs, scores))
    # Фильтр + сортировка
    filtered = sorted(
        [doc for doc, score in scored if score >= threshold],
        key=lambda d: scores[docs.index(d)],
        reverse=True
    )
    return filtered[:top_k]

def format_docs(docs):
    if not docs:
        return "Нет релевантной информации."
    return "\n\n".join([
        f"Документ: {doc.metadata.get('source', '?').split('/')[-1]}\n{doc.page_content.strip()}"
        for doc in docs
    ])

# 4. Функция: поиск → ре-ранж → форматирование
def retrieve_and_format(query: str):
    raw_docs = db.as_retriever(search_kwargs={"k": 10}).invoke(query)  # берём с запасом
    reranked = rerank_docs(query, raw_docs, top_k=3)
    return format_docs(reranked)

# 5. Промпт
PROMPT_TEMPLATE = """System: Ты помощник, который сначала размышляет, а потом отвечает. 
Всегда пиши свои шаги.

ВАЖНО:
- Контекст может быть на английском — извлекай факты из него и отвечай на русском.
- Сохраняй оригинальные термины (Synth Flux, Xarn Velgor).
- Пиши «Я не знаю» ТОЛЬКО если в контексте действительно нет упоминаний по теме.

Контекст:
{context}

Примеры:
Вопрос: Кто такой Xarn Velgor?
Ответ: 1. Ищу в контексте «Xarn Velgor». 2. Нахожу: «sent Xarn Velgor to personally handle...». 3. Ответ: Xarn Velgor — персона, отправленная для работы с повстанческой группой.

Вопрос: Где находится столица Qolid Cazesa?
Ответ: 1. Ищу «Qolid Cazesa» в контексте. 2. Нахожу упоминание «Zenith Prime — центр политического управления». 3. Ответ: Столица — Zenith Prime.

Вопрос: Что такое Phase Blade?
Ответ: 1. Ищу «Phase Blade» в контексте. 2. Нахожу описание оружия. 3. Ответ: Phase Blade — энергетическое оружие адептов Order of Lumin.

Вопрос: {input}
Ответ: Дай краткий ответ на русском. Не повторяй фразы."""

prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)

# 6. Сборка цепочки (простая и надёжная)
rag_chain = (
    {"context": lambda q: retrieve_and_format(q), "input": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 7. REPL
def main():
    print("RAG-бот запущен. Введите 'выход' для остановки.")
    while True:
        q = input("\nЗапрос: ").strip()
        if q.lower() in ("выход", "exit"): break
        if not q: continue
        try:
            # Отладка: показываем найденные чанки
            raw_docs = db.as_retriever(search_kwargs={"k": 10}).invoke(q)
            reranked = rerank_docs(q, raw_docs, top_k=3)
            print(f"\n[DEBUG] После ре-ранжа: {len(reranked)} чанков")
            for i, d in enumerate(reranked, 1):
                src = d.metadata.get("source", "?").split("\\")[-1]
                print(f"{i}. [{src}] {d.page_content[:120]}...")

            # Ответ
            print("\nОтвет:", rag_chain.invoke(q))
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()