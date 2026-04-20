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


# Параметры
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
FAISS_PATH = "../task3_build_index/faiss_index"
LLM_MODEL = "gpt-3.5-turbo"

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
    temperature=0.2,          # Немного случайности
    repeat_penalty=1.1,       # Штраф за повторения
    num_predict=512,          # Ограничить длину ответа
    stop=["\n\nЗапрос:", "Запрос:"]  # Стоп-токены
)

# Вариант 2: Hugging Face (бесплатно, но медленнее) GGUF ~4.1–4.8 ГБ Мультиязычность: Преимущественно английский
# llm = HuggingFaceEndpoint(repo_id="mistralai/Mistral-7B-Instruct-v0.2")


# 3. Промпт (Few-shot + Chain-of-Thought)
PROMPT_TEMPLATE = """System: Ты помощник, который сначала размышляет, а потом отвечает. Всегда пиши свои шаги.
ВАЖНО: Отвечай на русском, но сохраняй оригинальные термины из базы (Xarn Velgor, Synth Flux, Phase Blade и т.д.).

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

rag_chain = (
    {"context": retriever | format_docs, "input": RunnablePassthrough()}
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
            res = rag_chain.invoke(q)
            print(res)
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()