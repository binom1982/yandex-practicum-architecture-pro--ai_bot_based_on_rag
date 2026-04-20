# Задание 4. Реализация RAG-бота с техниками промптинга

## Запуск бота в режиме REPL

```bash
python rag_bot.py
```

## Примеры диалогов

### Успешные

**Запрос: Кто такой Xarn Velgor?**
Ответ: Шаг 1: Вопрос: Кто такой Xarn Velgor?
Шаг 2: Ищу в контексте «Xarn Velgor».
Шаг 3: Нахожу упоминание о Xarn Velgor в документе «Great_Jedi_Purge.md» и «Jedi_Order.md».
Шаг 4: В документе «Great_Jedi_Purge.md» упоминается, что Xarn Velgor был его бывшим учеником, который betrayed и murdered его отца, а также helped Haduhi hunt down and destroy Lasad Tiheza.
Шаг 5: В документе «Jedi_Order.md» упоминается, что Xarn Velgor был бывшим учеником Nukeq Qazoki и betrayed Order of Lumin.
Шаг 6: Следовательно, Xarn Velgor — это персона, которая betrayal Order of Lumin.



**Запрос: Что такое Synth Flux?**
Ответ: Я не знаю.

**Запрос: Где находится Zenith Prime?**

Ответ: 1. Ищу в контексте «Zenith Prime».
2. Нахожу упоминание «Zenith Prime» в различных документах.
3. Ответ: Zenith Prime — планета, расположенная в центре галактики, столица Qodol Coqena и центр политического управления.

Какой корабль называется Skylark Runner?**

**Что такое ** **Phase Blade** **?**

### «Я не знаю»

Как зовут создателя Synth Flux?

Сколько стоит билет на Skylark Runner?

Кто победил в битве при Aridion?
