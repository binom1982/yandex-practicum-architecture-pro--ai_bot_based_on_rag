# Задание 2. Подготовка базы знаний

## Парсинг сайта

```bash
pip install -r requirements.txt
python scraper_media_wiki.py          # 1. Скачивает и чистит 30+ страниц в raw_texts/
```

## Созданние базы знаний

```bash
# 1. Извлечь кандидаты из скачанных файлов
python extract_terms.py

# 2. Сгенерировать terms_map.json (с ручными дополнениями)
python generate_terms_map.py

# 3. Применить замены к базе знаний
python prepare_kb.py
```

## Словарь замен (terms_map.json)

### Выбранная вселенная

**Star Wars** (источник: [starwars.fandom.com](https://starwars.fandom.com/))

### Принцип замены

Все ключевые термины заменены на вымышленные аналоги с сохранением:

- **Семантики**: «Сила» → «Синт-Флюкс» (энергетическая сущность)
- **Структуры**: «Дарт Вейдер» → «Зарн Велгор» (Имя + Фамилия)
- **Контекста**: «Звезда Смерти» → «Ядро Пустоты» (орбитальное оружие)

### Категории замен

| Категория     | Примеры замен                             |
| ---------------------- | ----------------------------------------------------- |
| Персонажи     | Luke Skywalker → Kaelen Voss, Yoda → Zynar          |
| Планеты         | Tatooine → Aridion, Coruscant → Zenith Prime        |
| Технологии   | Lightsaber → Phase Blade, X-wing → Viper Wing       |
| Организации | Jedi Order → Order of Lumin, Sith → Covenant of Ash |
| Концепты       | The Force → Synth Flux, Dark Side → Void Aspect     |

### Метод генерации

- Короткие имена: случайная комбинация согласных/гласных (`Zynar`, `Kaelen`)
- Составные названия: генерация по частям (`Void` + `Core`)
- Ключевые термины зафиксированы вручную для консистентности
