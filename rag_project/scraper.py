import os
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from pathlib import Path

TARGET_URLS = [
    # 🔹 Персонажи
    "https://starwars.fandom.com/wiki/Darth_Vader",
    "https://starwars.fandom.com/wiki/Luke_Skywalker",
    "https://starwars.fandom.com/wiki/Princess_Leia",
    "https://starwars.fandom.com/wiki/Han_Solo",
    "https://starwars.fandom.com/wiki/Chewbacca",
    "https://starwars.fandom.com/wiki/Obi-Wan_Kenobi",
    "https://starwars.fandom.com/wiki/Yoda",
    "https://starwars.fandom.com/wiki/Emperor_Palpatine",
    "https://starwars.fandom.com/wiki/Kylo_Ren",
    "https://starwars.fandom.com/wiki/Rey_Skywalker",
    "https://starwars.fandom.com/wiki/Finn",
    "https://starwars.fandom.com/wiki/Poe_Dameron",
    "https://starwars.fandom.com/wiki/Ahsoka_Tano",
    "https://starwars.fandom.com/wiki/Boba_Fett",
    "https://starwars.fandom.com/wiki/Darth_Maul",
    
    # 🪐 Планеты и локации
    "https://starwars.fandom.com/wiki/Tatooine",
    "https://starwars.fandom.com/wiki/Coruscant",
    "https://starwars.fandom.com/wiki/Endor",
    "https://starwars.fandom.com/wiki/Hoth",
    "https://starwars.fandom.com/wiki/Naboo",
    "https://starwars.fandom.com/wiki/Kashyyyk",
    "https://starwars.fandom.com/wiki/Mustafar",
    "https://starwars.fandom.com/wiki/Jakku",
    "https://starwars.fandom.com/wiki/Ahch-To",
    "https://starwars.fandom.com/wiki/Exegol",
    
    # 🚀 Техника и оружие
    "https://starwars.fandom.com/wiki/Millennium_Falcon",
    "https://starwars.fandom.com/wiki/X-wing_starfighter",
    "https://starwars.fandom.com/wiki/TIE_Fighter",
    "https://starwars.fandom.com/wiki/AT-AT",
    "https://starwars.fandom.com/wiki/Lightsaber",
    "https://starwars.fandom.com/wiki/Death_Star",
    "https://starwars.fandom.com/wiki/Star_Destroyer",
    "https://starwars.fandom.com/wiki/Blaster",
    
    # 🏛️ Организации
    "https://starwars.fandom.com/wiki/Galactic_Empire",
    "https://starwars.fandom.com/wiki/Rebel_Alliance",
    "https://starwars.fandom.com/wiki/First_Order",
    "https://starwars.fandom.com/wiki/Resistance",
    "https://starwars.fandom.com/wiki/Jedi_Order",
    "https://starwars.fandom.com/wiki/Sith",
    "https://starwars.fandom.com/wiki/Mandalorian",
    
    # ⚔️ События и концепты
    "https://starwars.fandom.com/wiki/Battle_of_Yavin",
    "https://starwars.fandom.com/wiki/Clone_Wars",
    "https://starwars.fandom.com/wiki/Great_Jedi_Purge",
    "https://starwars.fandom.com/wiki/The_Force",
    "https://starwars.fandom.com/wiki/Force_sensitive",
    "https://starwars.fandom.com/wiki/Dark_side_of_the_Force",
    "https://starwars.fandom.com/wiki/Light_side_of_the_Force",
    "https://starwars.fandom.com/wiki/Jedi_Training",
    "https://starwars.fandom.com/wiki/Sith_Lightsaber",
]

# 🎭 Реалистичные заголовки браузера
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}

def clean_wiki_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Удаляем шум
    for tag in soup(["script", "style", "nav", "aside", "footer", "header", "table", "form"]):
        tag.decompose()
    # Контент в .mw-content-ltr или .mw-parser-output
    content = soup.find("div", class_="mw-content-ltr") or soup.find("div", class_="mw-parser-output") or soup.find("body")
    if not content:
        return ""
    text = content.get_text(separator="\n")
    # Чистка
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r"\[edit\]|\[source\]", "", text)
    text = "\n".join(line.strip() for line in text.split("\n") if line.strip())
    return text

def safe_filename(url: str) -> str:
    title = url.rstrip("/").split("/")[-1].split("?")[0]
    title = re.sub(r"[^\w\-_ ]", "", title).replace(" ", "_")
    return f"{title}.md"

def main():
    out_dir = Path("raw_texts")
    out_dir.mkdir(exist_ok=True)
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    print(f"🌐 Запуск парсера. Страниц: {len(TARGET_URLS)}")
    for i, url in enumerate(TARGET_URLS, 1):
        print(f"[{i}/{len(TARGET_URLS)}] {url}")
        try:
            # Рандомная задержка для обхода защиты
            time.sleep(random.uniform(2, 4))
            resp = session.get(url, timeout=15)
            if resp.status_code == 403:
                print("⚠️ 403 Forbidden — пробуем ещё раз через 5 сек...")
                time.sleep(5)
                resp = session.get(url, timeout=15)
            resp.raise_for_status()
            
            clean_text = clean_wiki_html(resp.text)
            if len(clean_text) < 200:
                print("⚠️ Мало контента, пропускаем")
                continue
                
            fname = safe_filename(url)
            (out_dir / fname).write_text(clean_text, encoding="utf-8")
            print(f"✅ {fname} ({len(clean_text)} симв.)")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка сети: {e}")
        except Exception as e:
            print(f"❌ Ошибка: {type(e).__name__}: {e}")
            
    print(f"\n📦 Готово. Проверьте папку {out_dir}")

if __name__ == "__main__":
    main()