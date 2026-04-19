import os
import json
import re
from pathlib import Path
import shutil

def load_mapping(path="terms_map.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def clean_html(raw_text: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', raw_text)
    text = re.sub(r'&\w+;', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def replace_terms(text: str, mapping: dict) -> str:
    # Сортировка по длине исключает частичные замены (например, "Jedi" раньше "Jedi Master")
    for term in sorted(mapping.keys(), key=len, reverse=True):
        text = text.replace(term, mapping[term])
    return text

def main():
    mapping = load_mapping()
    input_dir = Path("raw_texts")
    output_dir = Path("knowledge_base")
    # 🔥 Очистка папки при каждом запуске
    if output_dir.exists():
        shutil.rmtree(output_dir)  # Удаляем папку полностью
    output_dir.mkdir(parents=True, exist_ok=True)  # Создаём заново

    if not input_dir.exists():
        print("❌ Папка raw_texts не найдена. Положите туда скачанные документы.")
        return

    processed = 0
    for file in input_dir.iterdir():
        if file.suffix.lower() in (".html", ".htm", ".txt", ".md"):
            raw = file.read_text(encoding="utf-8")
            clean = clean_html(raw) if file.suffix.lower() in (".html", ".htm") else raw
            final_text = replace_terms(clean, mapping)
            
            out_path = output_dir / f"{file.stem}.md"
            out_path.write_text(final_text, encoding="utf-8")
            processed += 1

    print(f"✅ Готово: {processed} файлов сохранены в {output_dir}")

if __name__ == "__main__":
    main()