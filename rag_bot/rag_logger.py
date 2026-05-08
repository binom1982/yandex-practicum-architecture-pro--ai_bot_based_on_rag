# rag_logger.py
import json
import datetime
from pathlib import Path

LOG_FILE = Path("logs.jsonl")

def log_query(query: str, chunks: list, answer: str):
    # Критерий успеха: ответ достаточно длинный и не содержит стандартного отказа
    success = len(answer) > 20 and "не знаю" not in answer.lower()
    
    # Извлекаем уникальные источники из метаданных чанков
    sources = list({d.metadata.get("source", "unknown") for d in chunks}) if chunks else []
    
    record = {
        "query": query,
        "timestamp": datetime.datetime.now().isoformat(),
        "chunks_found": len(chunks),
        "answer_length": len(answer),
        "success": success,
        "sources": sources
    }
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
# Пример вызова в вашем RAG-пайплайне:
# log_query(user_query, retrieved_chunks, llm_answer)