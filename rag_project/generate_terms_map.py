import json
import random
import string
from pathlib import Path

# 🎲 Генератор «инопланетных» названий
def generate_name(prefix="", suffix="", length=8):
    vowels = "aeiou"
    consonants = "bcdfghjklmnpqrstvwxz"
    name = prefix
    for i in range(length - len(prefix) - len(suffix)):
        pool = vowels if i % 2 else consonants
        name += random.choice(pool)
    name += suffix
    return name.capitalize()

def generate_pair(original: str) -> str:
    """Создаёт замену, сохраняя структуру (одно/два слова)"""
    parts = original.split()
    if len(parts) == 1:
        return generate_name(length=random.randint(6, 10))
    else:
        return f"{generate_name(length=5)} {generate_name(length=6)}"

def create_terms_map(candidates_file="candidates.json", 
                     manual_additions: dict = None,
                     output="terms_map.json"):
    # Загружаем найденные кандидаты
    candidates = {}
    if Path(candidates_file).exists():
        candidates = json.loads(Path(candidates_file).read_text(encoding="utf-8"))
    
    # Добавляем ручные термины (обязательные)
    if manual_additions:
        candidates.update(manual_additions)
    
    # Генерируем маппинг
    terms_map = {term: generate_pair(term) for term in candidates}
    
    # Фиксируем ключевые замены для консистентности
    core_replacements = {
        "Darth Vader": "Xarn Velgor",
        "Luke Skywalker": "Kaelen Voss", 
        "Death Star": "Void Core",
        "The Force": "Synth Flux",
        "Jedi": "Order of Lumin",
        "Sith": "Covenant of Ash",
        "Lightsaber": "Phase Blade",
        "Millennium Falcon": "Skylark Runner",
        "Tatooine": "Aridion",
        "Coruscant": "Zenith Prime",
        "Star Destroyer": "Nexus Cruiser",
        "X-wing": "Viper Wing",
        "TIE Fighter": "Shadow Dart",
        "Rebel Alliance": "Free Systems Coalition",
        "Galactic Empire": "Central Hegemony",
        "Clone Wars": "Synth Uprising",
        "Battle of Yavin": "Siege of Aridion",
        "Force sensitive": "Flux-attuned",
        "Dark side": "Void Aspect",
        "Light side": "Lumin Aspect",
    }
    terms_map.update(core_replacements)
    
    Path(output).write_text(json.dumps(terms_map, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Создан {output} с {len(terms_map)} заменами")
    return terms_map

if __name__ == "__main__":
    # Обязательные термины (если candidates.json ещё нет)
    manual = {
        "Darth Vader", "Luke Skywalker", "Princess Leia", "Han Solo", "Chewbacca",
        "Obi-Wan Kenobi", "Yoda", "Emperor Palpatine", "Kylo Ren", "Rey Skywalker",
        "Death Star", "Millennium Falcon", "X-wing", "TIE Fighter", "Lightsaber",
        "The Force", "Jedi", "Sith", "Tatooine", "Coruscant", "Endor", "Hoth",
        "Galactic Empire", "Rebel Alliance", "Clone Wars", "Battle of Yavin",
        "Star Destroyer", "AT-AT", "Blaster", "Mandalorian", "Ahsoka Tano",
        "Boba Fett", "Darth Maul", "Naboo", "Kashyyyk", "Mustafar", "Jakku",
        "Ahch-To", "Exegol", "First Order", "Resistance", "Jedi Order",
        "Force sensitive", "Dark side of the Force", "Light side of the Force",
    }
    manual_dict = {t: None for t in manual}  # значения перегенерируются
    create_terms_map(manual_additions=manual_dict)