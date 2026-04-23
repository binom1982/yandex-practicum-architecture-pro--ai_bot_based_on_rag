import os
import json
import time
import argparse
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import shutil

# Параметры по умолчанию
DEFAULT_KNOWLEDGE_BASE_DIR = "../rag_project/knowledge_base"
DEFAULT_INDEX_OUTPUT_PATH = "faiss_index"
DEFAULT_CHUNK_SIZE = 300
DEFAULT_CHUNK_OVERLAP = 50

# Карта моделей: имя → размерность эмбеддинга
EMBEDDING_DIM_MAP = {
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 384,
    "sentence-transformers/bge-base-en-v1.5": 768,
    "sentence-transformers/bge-base-zh-v1.5": 768,
    "intfloat/multilingual-e5-large": 1024,
    "intfloat/multilingual-e5-small": 384,
}

def load_documents(directory: str) -> list[Document]:
    """Загружает .txt и .md файлы из директории"""
    documents = []
    for filepath in Path(directory).rglob("*.txt"):
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        documents.append(Document(
            page_content=text,
            metadata={"source": str(filepath), "title": filepath.stem}
        ))
    for filepath in Path(directory).rglob("*.md"):
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        documents.append(Document(
            page_content=text,
            metadata={"source": str(filepath), "title": filepath.stem}
        ))
    return documents

def split_documents(documents: list[Document], chunk_size: int, chunk_overlap: int) -> list[Document]:
    """Разбивает документы на чанки"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    return splitter.split_documents(documents)

def get_embedding_dim(model_name: str) -> int:
    """Возвращает размерность эмбеддинга для модели"""
    return EMBEDDING_DIM_MAP.get(model_name, 384)  # fallback на 384

def build_index(model_name: str, kb_dir: str, index_path: str, chunk_size: int, chunk_overlap: int):
    # 🔥 Очистка папки перед сборкой
    if Path(index_path).exists():
        shutil.rmtree(index_path)
        print(f"🧹 Удалён старый индекс: {index_path}")
    
    start_time = time.time()
    
    # 1. Загрузка документов
    print("📁 Загрузка документов...")
    docs = load_documents(kb_dir)
    print(f"   Загружено документов: {len(docs)}")
    
    # 2. Разбиение на чанки
    print("✂️ Разбиение на чанки...")
    chunks = split_documents(docs, chunk_size, chunk_overlap)
    print(f"   Создано чанков: {len(chunks)}")
    
    # 3. Инициализация эмбеддингов
    print(f"🔤 Загрузка модели эмбеддингов: {model_name}...")
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    
    # 4. Создание индекса FAISS
    print("🗂️ Создание векторного индекса...")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    # 5. Сохранение индекса
    os.makedirs(index_path, exist_ok=True)
    vectorstore.save_local(index_path)
    print(f"💾 Индекс сохранён в {index_path}")
    
    # 6. Логирование
    elapsed = time.time() - start_time
    stats = {
        "model": model_name,
        "embedding_dim": get_embedding_dim(model_name),
        "total_documents": len(docs),
        "total_chunks": len(chunks),
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "index_path": index_path,
        "build_time_seconds": round(elapsed, 2)
    }
    with open(f"{index_path}/metadata.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Готово за {elapsed:.1f} сек.")
    print(f"📊 Модель: {model_name} | Чанков: {len(chunks)} | Размерность: {stats['embedding_dim']}")
    return vectorstore, stats

def parse_args():
    parser = argparse.ArgumentParser(description="Создание векторного индекса базы знаний")
    parser.add_argument("--model", type=str, 
                        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                        help="Название модели эмбеддингов (Hugging Face)")
    parser.add_argument("--kb-dir", type=str, 
                        default=DEFAULT_KNOWLEDGE_BASE_DIR,
                        help="Путь к папке с документами базы знаний")
    parser.add_argument("--index-path", type=str, 
                        default=DEFAULT_INDEX_OUTPUT_PATH,
                        help="Путь для сохранения индекса")
    parser.add_argument("--chunk-size", type=int, 
                        default=DEFAULT_CHUNK_SIZE,
                        help="Размер чанка в токенах")
    parser.add_argument("--chunk-overlap", type=int, 
                        default=DEFAULT_CHUNK_OVERLAP,
                        help="Перекрытие чанков в токенах")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    build_index(
        model_name=args.model,
        kb_dir=args.kb_dir,
        index_path=args.index_path,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )