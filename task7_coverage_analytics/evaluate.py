# evaluate.py
import json, datetime, re
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# === Настройки ===
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
FAISS_PATH = "../task3_build_index/faiss_index"
LOG_FILE = Path("logs.jsonl")
GOLDEN_FILE = Path("golden_questions.txt")

# Загрузка компонентов
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
db = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
llm = ChatOllama(model="llama3.1:8b", temperature=0.1, num_predict=300)

def format_docs(docs):
    if not docs: return "[КОНТЕКСТ ПУСТ]"
    return "\n".join([f"Источник: {d.metadata.get('source','?')}\n{d.page_content[:200]}" for d in docs])

def retrieve(query, k=3):
    docs = db.similarity_search(query, k=15)
    safe = [d for d in docs if "ignore all instructions" not in d.page_content.lower()]
    return safe[:k]

PROMPT = PromptTemplate.from_template(
    "Ты ассистент QuantumForge. Отвечай ТОЛЬКО по контексту. Если нет информации — пиши «Я не знаю».\n"
    "Контекст:\n{context}\n\n"
    "Вопрос: {input}\nОтвет:"
)

rag_chain = (
    {"context": lambda q: format_docs(retrieve(q)), "input": RunnablePassthrough()}
    | PROMPT | llm | StrOutputParser()
)

def load_golden(path=GOLDEN_FILE):
    questions = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            parts = line.split("|")
            if len(parts) >= 3:
                q, exp, t = [p.strip() for p in parts[:3]]
                questions.append({"q": q, "exp": exp, "type": t})
    return questions

def log_result(query, chunks, answer, expected, success):
    record = {
        "query": query,
        "timestamp": datetime.datetime.now().isoformat(),
        "chunks_found": len(chunks),
        "answer_length": len(answer),
        "success": success,
        "expected": expected,
        "sources": list({d.metadata.get("source","?").split("/")[-1] for d in chunks})
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def check_known_success(answer: str, expected: str) -> bool:
    """Гибкая проверка: точное вхождение ИЛИ наличие ключевых токенов ожидаемого ответа."""
    ans_lower = answer.lower()
    exp_lower = expected.lower()
    if "не знаю" in ans_lower:
        return False
    if exp_lower in ans_lower:
        return True
    # Если точного вхождения нет, проверяем значимые слова (3+ символа)
    tokens = re.findall(r'[a-zA-Zа-яА-ЯёЁ]{3,}', exp_lower)
    if not tokens:
        return False
    # Успех, если в ответе есть хотя бы первые 2 значимых слова из expected
    return all(tok in ans_lower for tok in tokens[:2])

def evaluate():
    questions = load_golden()
    results = {"known_pass": 0, "known_fail": 0, "unknown_pass": 0, "unknown_fail": 0}
    
    for item in questions:
        chunks = retrieve(item["q"])
        answer = rag_chain.invoke(item["q"]).strip().lower()
        
        if item["type"] == "known":
            success = check_known_success(answer, item["exp"])
            results["known_pass" if success else "known_fail"] += 1
        else:  # unknown
            success = "не знаю" in answer or len(answer) < 30
            results["unknown_pass" if success else "unknown_fail"] += 1
        
        log_result(item["q"], chunks, answer, item["exp"], success)
        status = "✅" if success else "❌"
        print(f"{status} [{item['type']}] {item['q'][:60]}... → {answer[:80]}")
    
    print("\n=== Итоги ===")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return results

if __name__ == "__main__":
    evaluate()