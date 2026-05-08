import os
import re
import time
import random
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from html import unescape  # Для декодирования &nbsp; &amp; и т.д.
import shutil

# 🔧 СПИСОК СТРАНИЦ (49 URL)
TARGET_PAGES = [
    "Darth_Vader", "Luke_Skywalker", "Princess_Leia", "Han_Solo", "Chewbacca",
    "Obi-Wan_Kenobi", "Yoda", "Emperor_Palpatine", "Kylo_Ren", "Rey_Skywalker",
    "Finn", "Poe_Dameron", "Ahsoka_Tano", "Boba_Fett", "Darth_Maul",
    "Tatooine", "Coruscant", "Endor", "Hoth", "Naboo",
    "Kashyyyk", "Mustafar", "Jakku", "Ahch-To", "Exegol",
    "Millennium_Falcon", "X-wing_starfighter", "TIE_Fighter", "AT-AT", "Lightsaber",
    "Death_Star", "Star_Destroyer", "Blaster", "Galactic_Empire", "Rebel_Alliance",
    "First_Order", "Resistance", "Jedi_Order", "Sith", "Mandalorian",
    "Battle_of_Yavin", "Clone_Wars", "Great_Jedi_Purge", "The_Force", "Force_sensitive",
    "Dark_side_of_the_Force", "Light_side_of_the_Force", "Jedi_Training", "Sith_Lightsaber",
]

API_URL = "https://starwars.fandom.com/api.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

def fetch_page_content(title: str) -> str:
    """Получает HTML-контент страницы через MediaWiki API"""
    params = {
        "action": "parse",
        "page": title,
        "format": "json",
        "prop": "text",
        "disablelimitreport": True,
    }
    resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        return None
    return data["parse"]["text"]["*"]

def clean_html(html: str) -> str:
    """Полная очистка HTML от шума"""
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Удаляем служебные теги
    for tag in soup(["script", "style", "nav", "aside", "footer", "header", "table", "form", "img", "iframe", "noscript"]):
        tag.decompose()
    
    # 2. Находим основной контент
    content = soup.find("div", class_="mw-content-ltr") or soup.find("div", class_="mw-parser-output")
    if not content:
        return ""
    
    # 3. Извлекаем текст
    text = content.get_text(separator="\n")
    
    # 4. Декодируем HTML-сущности (&nbsp; &amp; &lt; и т.д.)
    text = unescape(text)
    
    # 5. Удаляем вики-разметку и служебные элементы
    # 🔧 ИСПРАВЛЕНИЕ: \[\s*\d+\s*\] ловит сноски даже с переносами внутри [ 12 ] или [\n12\n]
    text = re.sub(r"\[edit\]|\[source\]|\^|\[\s*\d+\s*\]", "", text)
    text = re.sub(r"\{\{.*?\}\}", "", text, flags=re.DOTALL)     # шаблоны {{...}}
    text = re.sub(r"\[\[.*?\|?(.*?)\]\]", r"\1", text)           # вики-ссылки [[Text|Label]] → Label
    text = re.sub(r"__NOTOC__|__NOEDITSECTION__", "", text)      # магические слова MediaWiki
    
    # 6. Удаляем языковые переключатели (строки с 3+ языковыми кодами)
    lang_pattern = r'^(.*?(français|English|한국어|日本語|українська|polski|português|Türkçe|ქართული|עברית|suomi|norsk|magyar|italiano|Deutsch|Español|русский|中文).*?){3,}.*$'
    text = re.sub(lang_pattern, "", text, flags=re.M | re.I)
    
    # 7. Убираем лишние переносы и пробелы
    text = re.sub(r"\n\s*\n", "\n\n", text)           # множественные переносы → один пустой абзац
    text = re.sub(r"[ \t]+", " ", text)               # множественные пробелы → один
    text = "\n".join(line.strip() for line in text.split("\n") if line.strip())  # trim + удаление пустых
    
    # 8. Обрезаем слишком длинные строки (опционально, защита от «простыней»)
    lines = []
    for line in text.split("\n"):
        if len(line) > 500:
            parts = re.split(r'(?<=[.!?])\s+', line)
            lines.extend(parts)
        else:
            lines.append(line)
    text = "\n".join(lines)
    
    return text.strip()

def safe_filename(title: str) -> str:
    return f"{title}.md"

def main():
    out_dir = Path("raw_texts")
    # 🔥 Очистка папки при каждом запуске
    if out_dir.exists():
        shutil.rmtree(out_dir)  # Удаляем папку полностью
    out_dir.mkdir(parents=True, exist_ok=True)  # Создаём заново
    
    print(f"🌐 Запуск парсера (API). Страниц: {len(TARGET_PAGES)}")
    session = requests.Session()
    session.headers.update(HEADERS)
    
    for i, title in enumerate(TARGET_PAGES, 1):
        print(f"[{i}/{len(TARGET_PAGES)}] {title}")
        try:
            time.sleep(random.uniform(1.5, 3))  # Вежливая задержка
            html = fetch_page_content(title)
            if not html:
                print(f"⚠️ Нет контента, пропускаем")
                continue
            clean_text = clean_html(html)
            if len(clean_text) < 200:
                print(f"⚠️ Мало текста, пропускаем")
                continue
            fname = safe_filename(title)
            (out_dir / fname).write_text(clean_text, encoding="utf-8")
            print(f"✅ {fname} ({len(clean_text)} симв.)")
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка сети: {e}")
        except Exception as e:
            print(f"❌ Ошибка: {type(e).__name__}: {e}")
            
    print(f"\n📦 Готово. Проверьте папку {out_dir}")

if __name__ == "__main__":
    main()