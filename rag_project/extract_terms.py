import re
import json
from pathlib import Path
from collections import Counter

def extract_candidates(folder="raw_texts", min_freq=2):
    """Находит часто встречающиеся capitalized-слова (потенциальные термины)"""
    words = Counter()
    pattern = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b')  # Darth Vader, Death Star
    
    for file in Path(folder).glob("*.md"):
        text = file.read_text(encoding="utf-8")
        # Исключаем обычные слова в начале предложений
        sentences = re.split(r'[.!?]\s+', text)
        for sent in sentences:
            found = pattern.findall(sent)
            # Убираем слова в начале предложения (ложные срабатывания)
            if found and sent.strip().startswith(found[0]):
                found = found[1:]
            words.update(found)
    
    # Фильтруем: только встречающиеся ≥ min_freq раз и не словарные слова
    common_en = {"The", "A", "An", "In", "On", "At", "To", "For", "Of", "And", "But", "With"}
    candidates = {w: c for w, c in words.items() if c >= min_freq and w not in common_en and len(w) > 3}
    return dict(sorted(candidates.items(), key=lambda x: -x[1]))

if __name__ == "__main__":
    candidates = extract_candidates()
    print(f"🔍 Найдено {len(candidates)} кандидатов:")
    for term, freq in list(candidates.items())[:30]:
        print(f"  {term}: {freq}")
    
    # Сохраняем для ручной проверки
    Path("candidates.json").write_text(json.dumps(candidates, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n✅ Сохранено в candidates.json")