import os
import re
import time
import random
import requests
from pathlib import Path
from bs4 import BeautifulSoup

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
    """Очищает HTML от шума"""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "aside", "footer", "header", "table", "form", "img"]):
        tag.decompose()
    content = soup.find("div", class_="mw-content-ltr") or soup.find("div", class_="mw-parser-output")
    if not content:
        return ""
    text = content.get_text(separator="\n")
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r"\[edit\]|\[source\]|\^", "", text)
    text = "\n".join(line.strip() for line in text.split("\n") if line.strip())
    return text

def safe_filename(title: str) -> str:
    return f"{title}.md"

def main():
    out_dir = Path("raw_texts")
    out_dir.mkdir(exist_ok=True)
    
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