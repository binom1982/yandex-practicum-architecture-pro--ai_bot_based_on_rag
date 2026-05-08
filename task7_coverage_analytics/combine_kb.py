# combine_kb.py
from pathlib import Path

DEFAULT_KNOWLEDGE_BASE_DIR = "../rag_project/knowledge_base"
OUTPUT_FILE = "combined_knowledge_base.md"

def combine_kb_files(input_dir: str, output_file: str = OUTPUT_FILE) -> None:
    dir_path = Path(input_dir)
    if not dir_path.exists():
        raise FileNotFoundError(f"❌ Папка не найдена: {input_dir}")

    md_files = sorted(dir_path.glob("*.md"))
    if not md_files:
        print("⚠️ Файлы .md не найдены.")
        return

    with open(output_file, "w", encoding="utf-8") as out:
        for f in md_files:
            out.write(f"[{f.name}]\n")
            try:
                out.write(f"{f.read_text(encoding='utf-8').strip()}\n\n")
            except Exception as e:
                out.write(f"⚠️ Ошибка чтения {f.name}: {e}\n\n")

    print(f"✅ Склеено {len(md_files)} файлов → {output_file}")

if __name__ == "__main__":
    combine_kb_files(DEFAULT_KNOWLEDGE_BASE_DIR)