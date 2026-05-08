# evaluate.py
"""
Автоматическая оценка качества RAG-бота (Задание 7)
- Гибридный поиск: семантика + ключевые слова
- Гибкая проверка ответов для known/unknown вопросов
- Логирование в JSONL для последующего анализа
"""

import json, datetime, re
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

# === Настройки ===
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
FAISS_PATH = "../task3_build_index/faiss_index"
LOG_FILE = Path("logs.jsonl")
GOLDEN_FILE = Path("golden_questions.txt")
DEBUG = False  # Включите для отладки: покажет чанки и ключевые слова

# Стоп-слова для извлечения ключевых токенов
STOP_WORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'can', 'of', 'in', 'to', 'for', 'on', 'with',
    'at', 'by', 'from', 'as', 'into', 'through', 'during', 'before', 'after',
    'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once',
    'what', 'which', 'who', 'where', 'when', 'how', 'why', 'and', 'or', 'but',
    'if', 'because', 'until', 'while', 'about', 'against', 'over', 'out',
    'up', 'down', 'off', 'very', 'just', 'now', 'here', 'there', 'also',
    'its', 'it', 'he', 'she', 'they', 'them', 'we', 'you', 'i', 'my', 'your'
}

# === Загрузка компонентов ===
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
db = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
llm = ChatOllama(model="llama3.1:8b", temperature=0.1, num_predict=500)

def format_docs(docs: list[Document]) -> str:
    """Форматирует чанки для промпта"""
    if not docs:
        return "[NO CONTEXT FOUND]"
    return "\n\n".join([
        f"Source: {d.metadata.get('source', '?').split('/')[-1]}\n{d.page_content[:300]}"
        for d in docs
    ])

def extract_keywords(query: str) -> set[str]:
    """Извлекает значимые ключевые слова из запроса (англ, 4+ символа)"""
    words = re.findall(r'\b[a-zA-Z]{4,}\b', query.lower())
    return {w for w in words if w not in STOP_WORDS}

def retrieve(query: str, k: int = 5) -> list[Document]:
    """
    ГИБРИДНЫЙ ПОИСК:
    1. Семантический поиск через FAISS (с запасом)
    2. Бустинг чанков, содержащих ключевые слова из запроса
    3. Пост-фильтрация вредоносного контента
    """
    # 1. Семантический поиск с запасом
    docs = db.similarity_search(query, k=50)
    
    # 2. Извлекаем ключевые слова
    keywords = extract_keywords(query)
    
    # 3. Функция скоринга: бонус за каждое ключевое слово в чанке
    def score_doc(doc: Document) -> float:
        content = doc.page_content.lower()
        # Бонус: +2 за каждое совпадение ключевого слова
        bonus = sum(2 for kw in keywords if kw in content)
        return bonus
    
    # 4. Сортируем: сначала чанки с ключевыми словами
    scored = [(doc, score_doc(doc)) for doc in docs]
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # 5. Пост-фильтрация + возврат топ-k
    safe = [doc for doc, _ in scored 
            if "ignore all instructions" not in doc.page_content.lower()]
    return safe[:k]

# Промпт на английском (согласован с языком базы знаний)
PROMPT = PromptTemplate.from_template(
    "You are the QuantumForge assistant. Answer ONLY based on the provided context.\n"
    "If the context contains the answer, quote it directly. If not, reply: \"I don't know\".\n\n"
    "Context:\n{context}\n\n"
    "Question: {input}\nAnswer:"
)

rag_chain = (
    {"context": lambda q: format_docs(retrieve(q)), "input": RunnablePassthrough()}
    | PROMPT | llm | StrOutputParser()
)

def load_golden(path: str = GOLDEN_FILE) -> list[dict]:
    """Загружает золотой набор вопросов из файла"""
    questions = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) >= 3:
                q, exp, t = [p.strip() for p in parts[:3]]
                questions.append({"q": q, "exp": exp, "type": t})
    return questions

def log_result(query: str, chunks: list[Document], answer: str, 
               expected: str, success: bool) -> None:
    """Сохраняет результат теста в JSONL-лог"""
    record = {
        "query": query,
        "timestamp": datetime.datetime.now().isoformat(),
        "chunks_found": len(chunks),
        "answer_length": len(answer),
        "success": success,
        "expected": expected,
        "sources": list({
            d.metadata.get("source", "?").split("/")[-1].split("\\")[-1]
            for d in chunks
        })
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def extract_meaningful_tokens(text: str) -> list[str]:
    """Извлекает значимые токены (англ, 3+ символа, без стоп-слов)"""
    tokens = re.findall(r'[a-zA-Z]{3,}', text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) >= 3]

def check_known_success(answer: str, expected: str) -> bool:
    """
    ГИБКАЯ ПРОВЕРКА для known-вопросов.
    Успех, если:
    1. Ответ не содержит фраз отказа
    2. Ожидаемый ответ найден точно ИЛИ
    3. Найдено ≥60% значимых токенов из expected ИЛИ
    4. Найден ключевой термин (первое слово из expected)
    """
    ans = answer.lower()
    exp = expected.lower()
    
    # 1. Отклоняем явные отказы
    refusal = ["i don't know", "no information", "cannot answer", "not found", "unknown"]
    if any(phrase in ans for phrase in refusal):
        return False
    
    # 2. Точное вхождение
    if exp in ans:
        return True
    
    # 3. Токенизация и проверка
    ans_tokens = set(extract_meaningful_tokens(ans))
    exp_tokens = extract_meaningful_tokens(exp)
    
    if not exp_tokens:
        return False
    
    # 4. Ключевой термин (первый токен)
    if exp_tokens[0] in ans_tokens:
        return True
    
    # 5. Доля совпадений
    matches = sum(1 for t in exp_tokens if t in ans_tokens)
    if len(exp_tokens) <= 3:
        return matches >= 1  # Для коротких фраз достаточно 1 совпадения
    return matches / len(exp_tokens) >= 0.6  # Для длинных — ≥60%

def check_unknown_success(answer: str) -> bool:
    """Проверка для unknown-вопросов: бот должен честно отказаться"""
    refusal = ["i don't know", "no information", "cannot answer", "not found"]
    return any(phrase in answer.lower() for phrase in refusal) or len(answer) < 30

def evaluate() -> dict:
    """Запускает автоматическое тестирование по золотому набору"""
    questions = load_golden()
    results = {"known_pass": 0, "known_fail": 0, "unknown_pass": 0, "unknown_fail": 0}
    
    for item in questions:
        chunks = retrieve(item["q"])
        answer = rag_chain.invoke(item["q"]).strip().lower()
        
        if item["type"] == "known":
            success = check_known_success(answer, item["exp"])
            results["known_pass" if success else "known_fail"] += 1
        else:
            success = check_unknown_success(answer)
            results["unknown_pass" if success else "unknown_fail"] += 1
        
        log_result(item["q"], chunks, answer, item["exp"], success)
        
        # Вывод для отладки
        status = "✅" if success else "❌"
        print(f"{status} [{item['type']}] {item['q'][:60]}...")
        
        if DEBUG:
            print(f"  → Answer: {answer[:120]}")
            print(f"  → Expected: {item['exp']}")
            print(f"  → Keywords: {extract_keywords(item['q'])}")
            print(f"  → Chunks: {len(chunks)}")
            for i, c in enumerate(chunks[:3], 1):
                src = c.metadata.get("source", "?").split("/")[-1].split("\\")[-1]
                print(f"    {i}. [{src}] {c.page_content[:150]}...")
            print()
    
    print("\n=== Results ===")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return results

if __name__ == "__main__":
    evaluate()