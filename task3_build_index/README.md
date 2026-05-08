# Задание 3. Создание векторного индекса базы знаний

## 1. Выбор модели эмбеддингов

**Модель:** `paraphrase-multilingual-MiniLM-L12-v2` (Sentence-Transformers)

| **Параметр**        | **Значение**                                                                                                                                                                                  |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Репозиторий            | [Hugging Face](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)                                                                                                             |
| Размер эмбеддинга | 384 измерения                                                                                                                                                                                      |
| Тип                            | Локальная, открытая                                                                                                                                                                        |
| Преимущества          | Быстрая, лёгкая, хорошее качество для коротких текстов, мультиязычность (не нужно приводить все к одному языку) |

## Создание векторного индекса базы знаний

```bash
python build_index.py
```

## Пример запроса к индексу

```bash
python test_query.py
```

**Пример ответа**

```1c
🔍 Запрос: Что питает технологию HyperRelay?

[1] Источник: ..\rag_project\knowledge_base\First_Order.md
    Текст: static hyperspace field generator
, which enveloped arrays of databanks and computers in a localized hyperspace field that accelerated their calculation speeds to unimaginable rates.
Additionally, the...

[2] Источник: ..\rag_project\knowledge_base\First_Order.md
    Текст: Puzol Badotu also developed the hyperspace tracker which was a type of
active tracker
with the ability to detect starships traveling through hyperspace developed by Kinoq Guwufo scientists. Xidemagly ...

[3] Источник: ..\rag_project\knowledge_base\The_Force.md
    Текст: or several more
to be taken elsewhere in the name of balance. As such, the Mimeqexudi believed the Remadize needed to be "freed" from use and that Remadize users were abusing it.
Wowagu the Remadize i...
```

## Итоговое описание

| **Параметр**                     | **Значение**                                                                          |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Модель эмбеддингов            | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`                                     |
| База знаний                          | `../rag_project/knowledge_base`(43 документа, вымышленная вселенная) |
| Количество чанков              | 10 381                                                                                              |
| Размерность эмбеддинга    | 384                                                                                                 |
| Размер чанка / перекрытие | 500 / 50 токенов                                                                             |
| Векторная БД                        | FAISS (CPU)                                                                                         |
| Время генерации                  | 506.5 сек (~8.4 мин)                                                                          |
| Путь к индексу                     | `faiss_index/`                                                                                    |
