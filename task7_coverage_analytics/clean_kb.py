# clean_kb.py
import shutil
from pathlib import Path

KB_DIR = Path("../rag_project/knowledge_base")
BACKUP_DIR = Path("../rag_project/deleted_entities")
ENTITIES = {"Talak Quzebe", "Zinomoleha", "Kigedobok"}

def clean_knowledge_base():
    BACKUP_DIR.mkdir(exist_ok=True)
    moved = 0
    
    for file_path in KB_DIR.glob("*"):
        if not file_path.is_file():
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if any(entity in content for entity in ENTITIES):
                shutil.move(file_path, BACKUP_DIR / file_path.name)
                moved += 1
                print(f"✅ Перемещён: {file_path.name}")
        except Exception as e:
            print(f"⚠️ Ошибка чтения {file_path.name}: {e}")
            
    print(f"📦 Готово. Резервных копий создано: {moved}")

if __name__ == "__main__":
    clean_knowledge_base()