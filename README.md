# Сайт Опрессуем.ru

Боевой адрес: https://www.opressuem.ru (Yandex Object Storage, бакет `www.opressuem.ru`).
Копия на GitHub Pages: https://lifeexplorer230.github.io/teploseti-sait/ — canonical указывает на боевой домен.
Макет в Claude Design: https://claude.ai/artifact/3cXdQR1m2e3P9TQnBb3QG5

## Статьи

1. Создать файл `stati/_src/<адрес-латиницей>.md`. Имя файла станет адресом: `/stati/<адрес>/`.
2. Вверху — шапка:

   ```
   ---
   title: Заголовок для поиска, до ~65 знаков
   description: Описание для выдачи, до ~160 знаков
   date: 2026-10-15
   h1: Заголовок на странице (если не задан — берётся title)
   lead: Вводный абзац под заголовком
   draft: true      # пока черновик — страница не собирается
   ---
   ```

3. Дальше обычный markdown: `## Подзаголовок`, списки, таблицы, `> врезка`.
4. Собрать: `python3 tools/stati.py` — создаёт страницы, список статей, sitemap.xml, robots.txt.
5. Опубликовать: `git push` (GitHub Pages) и `python3 tools/deploy.py` (боевой хостинг).

Темы, запросы и частотность — в плане статей: `~/core/scratch/sait-teploseti/seo/PLAN-STATEI.md`.

## Индексация

Сейчас сайт закрыт от поисковиков (`"index": false` в `tools/site.json`). Открыть — поставить
`true`, пересобрать и залить: мета robots сменится на всех страницах, включая главную.
Открывать после замены выдуманных кейсов на реальные.

Телефон и часы работы для статей — тоже в `tools/site.json` (на главной — вручную в `index.html`).
