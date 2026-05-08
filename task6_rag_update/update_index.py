import os, json, logging, hashlib, shutil
from datetime import datetime
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

DOCS_DIR = "../rag_project/knowledge_base"
INDEX_PATH = "../rag_project/faiss_index"
META_FILE = "index_metadata.json"
TEMP_LOG = "update_temp.log"  # Временный лог во время работы

def get_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f: h.update(f.read())
    return h.hexdigest()

def setup_temp_logging():
    """Настройка логгера на временный файл"""
    logging.root.handlers = []
    logging.basicConfig(
        filename=TEMP_LOG,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        encoding="utf-8",
        force=True
    )

def finalize_log(files_count, errors_count):
    """Закрыть логгер и переименовать файл с итоговой статистикой"""
    # Закрываем все хендлеры — освобождаем файл на Windows
    for handler in logging.root.handlers[:]:
        handler.close()
        logging.root.removeHandler(handler)
    
    timestamp = datetime.now().strftime("%Y-%m-%d")
    # Формат с пробелами и скобками, как вы просили
    final_name = f"update_{timestamp}_({files_count}-files) ({errors_count}_errors).log"
    
    if os.path.exists(TEMP_LOG):
        try:
            shutil.move(TEMP_LOG, final_name)
        except PermissionError:
            # Если не удалось переименовать — копируем и удаляем исходный
            shutil.copy2(TEMP_LOG, final_name)
            os.remove(TEMP_LOG)
    return final_name

def update_index():
    files_processed = 0
    errors_count = 0
    
    setup_temp_logging()
    logging.info("=== Запуск обновления индекса ===")
    
    try:
        meta = json.load(open(META_FILE, encoding="utf-8")) if os.path.exists(META_FILE) else {}
        new_files = []
        
        for root, _, files in os.walk(DOCS_DIR):
            for f in files:
                if f.endswith((".txt", ".md")):
                    p = os.path.join(root, f)
                    if p not in meta or meta[p] != get_hash(p):
                        new_files.append(p)
                        
        if not new_files:
            logging.info("Изменений не найдено. Завершение.")
            finalize_log(0, 0)
            return
            
        files_processed = len(new_files)
        logging.info(f"Найдено файлов для обработки: {files_processed}")
        
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = []
        for p in new_files:
            try:
                docs = TextLoader(p, encoding="utf-8").load()
                split = splitter.split_documents(docs)
                for c in split: c.metadata["source"] = p
                chunks.extend(split)
            except Exception as e:
                errors_count += 1
                logging.warning(f"Ошибка чтения {p}: {e}")
            
        if not chunks:
            logging.error("Не удалось создать чанки. Завершение.")
            finalize_log(files_processed, errors_count)
            return
            
        emb = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        if os.path.exists(INDEX_PATH):
            store = FAISS.load_local(INDEX_PATH, emb, allow_dangerous_deserialization=True)
            store.add_documents(chunks)
        else:
            store = FAISS.from_documents(chunks, emb)
        store.save_local(INDEX_PATH)
        
        for p in new_files: meta[p] = get_hash(p)
        with open(META_FILE, "w", encoding="utf-8") as f: json.dump(meta, f, ensure_ascii=False)
        
        index_size = store.index.ntotal if hasattr(store.index, "ntotal") else len(store.docstore._dict)
        summary = f"index updated at {datetime.now().strftime('%Y-%m-%d')}, {files_processed} files added, {errors_count} errors."
        logging.info(f"Добавлено чанков: {len(chunks)} | Итоговый размер индекса: {index_size}")
        logging.info(summary)
        logging.info("=== Обновление завершено успешно ===")
        
    except Exception as e:
        errors_count += 1
        logging.error(f"Ошибка при обновлении: {e}")
    
    finally:
        # Всегда финализируем лог, даже при ошибке
        final_file = finalize_log(files_processed, errors_count)
        print(f"Лог сохранён: {final_file}")

if __name__ == "__main__":
    update_index()