# Парсер документов PEP

Парсер собирает данные о документах PEP (Python Enhancement Proposal)
и документации Python с сайтов [peps.python.org](https://peps.python.org/)
и [docs.python.org](https://docs.python.org/3/).

## Возможности

- Режим `pep` — обходит все документы PEP, считает количество PEP
  в каждом статусе, сравнивает статус в общем списке с фактическим
  на странице документа, логирует несовпадения и сохраняет итог
  в CSV-файл.
- Режим `whats-new` — собирает ссылки, заголовки и авторов из раздела
  «What's New in Python».
- Режим `latest-versions` — получает актуальные версии Python
  и их статусы (stable, pre-release, EOL и др.).
- Режим `download` — скачивает ZIP-архив с документацией Python
  в директорию `src/downloads/`.
- Вывод результатов в консоль, в виде форматированной таблицы
  или в CSV-файл (флаг `-o`).
- Кэширование HTTP-запросов через `requests-cache` (флаг `-c` для сброса).

## Технологии

- Python 3, BeautifulSoup4, lxml
- requests-cache (кэширование), tqdm (прогресс-бар)
- PrettyTable (табличный вывод)
- pytest, flake8

## Структура проекта

```
bs4_parser_pep/
├── src/
│   ├── __init__.py
│   ├── configs.py       # аргументы CLI и настройка логирования
│   ├── constants.py     # URL-адреса, пути, словарь статусов PEP
│   ├── exceptions.py    # исключение ParserFindTagException
│   ├── main.py          # парсеры и точка входа
│   ├── outputs.py       # вывод в консоль, таблицу и CSV
│   └── utils.py         # HTTP-запросы и поиск тегов
├── tests/               # тесты проекта
├── .flake8
├── pytest.ini
└── requirements.txt
```

## Установка и запуск

Клонировать репозиторий и перейти в него:

```bash
git clone https://github.com/0legRogovenko/bs4_parser_pep.git
cd bs4_parser_pep
```

Создать и активировать виртуальное окружение:

```bash
python3 -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate       # Windows
```

Установить зависимости:

```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

Запустить парсер (из корневой директории проекта):

```bash
PYTHONPATH=src python src/main.py {whats-new,latest-versions,download,pep}
```

Доступные флаги:

| Флаг | Описание |
|---|---|
| `-c`, `--clear-cache` | Очистить кэш перед запуском |
| `-o pretty` | Вывести результат в виде таблицы |
| `-o file` | Сохранить результат в CSV-файл (`src/results/`) |

Примеры:

```bash
# Парсинг PEP с сохранением результата в CSV
PYTHONPATH=src python src/main.py pep -o file

# Список новых статей с очисткой кэша
PYTHONPATH=src python src/main.py whats-new -c

# Актуальные версии Python в табличном виде
PYTHONPATH=src python src/main.py latest-versions -o pretty
```

## Тестирование

```bash
pytest
flake8 src/
```

## Автор

Олег Роговенко — [GitHub](https://github.com/0legRogovenko)
