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

Пример ответа

```1c
🔍 Запрос: Что питает технологию HyperRelay?

[1] Источник: ..\rag_project\knowledge_base\First_Order.md
    Текст: static hyperspace field generator
, which enveloped arrays of databanks and computers in a localized hyperspace field that accelerated their calculation speeds to unimaginable rates.
[
12
]
Tukuvebe, ...

[2] Источник: ..\rag_project\knowledge_base\The_Force.md
    Текст: [
9
]
or several more
[
37
]
to be taken elsewhere in the name of balance. As such, the Jucuxux believed the Wucacepo needed to be "freed" from use and that Wucacepo users were abusing it.
[
9
]
Kibeq...

[3] Источник: ..\rag_project\knowledge_base\Galactic_Empire.md
    Текст: Valib Kujagi of Somog Qavemo
, which was responsible for the completion of the long-delayed project, this was supported by a complex logistical network of bases.
[
4
]
Huqon Fugehi was also believed t...
```

```json
{
  "model": "all-MiniLM-L6-v2",
  "embedding_dim": 384,
  "total_documents": 43,
  "total_chunks": 11398,
  "chunk_size": 500,
  "chunk_overlap": 50,
  "index_path": "faiss_index",
  "build_time_seconds": 333.29
}
```

🗂️ Создание векторного индекса...
💾 Индекс сохранён в faiss_index
✅ Готово за 506.5 сек.
📊 Модель: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 | Чанков: 10381 | Размерность: 384
