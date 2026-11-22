# BACKEND — Телефонный справочник

Учебное Full Stack веб-приложение для хранения личных контактов. Пользователь регистрируется, входит в систему, создаёт группы, добавляет контакты и управляет ими. Контакты разных пользователей изолированы.

## Архитектура

- **Presentation:** HTML, Bootstrap, JavaScript (`fetch`). Интерфейс разрабатывается отдельно и подключается к API.
- **Business Logic / Core:** Flask, Blueprint, JWT, обработка запросов.
- **Supporting:** FastAPI, JSON-сервис хеширования и аналитики.
- **Data Access / Storage:** `db.py`, обычные SQL-запросы через `psycopg`, PostgreSQL. ORM не используется.

Схема БД: `users` → `groups`, `users` → `contacts`, `groups` → `contacts`. Три таблицы связаны внешними ключами. Повторяющиеся сведения вынесены в отдельные таблицы; структура соответствует третьей нормальной форме.

## Запуск Backend совместно с Database Engineering

Backend и PostgreSQL теперь **разделены по рабочим веткам**. В этом дереве находятся Flask, FastAPI, API-маршруты, бизнес-логика, SQL-запросы доступа к данным (`db.py`) и тесты. Создание таблиц, настройка ролей, репликация и индексы находятся **только** в [ветке Database Engineer](https://github.com/ivansemkov15-ui/project-web/tree/feature/danil/postgresql). SQL-запросы `db.py` — часть взаимодействия Backend с базой, поэтому они остаются здесь.

**Первый запуск через Docker на одном компьютере:**

1. Скачайте обе ветки в **разные соседние каталоги**: `backend/` (ветка `feature/ivan/backend`) и `database/` (ветка `feature/danil/postgresql`).
2. В каталоге `database` скопируйте `.env.example` в `.env`, задайте отдельные случайные `DB_PASSWORD`, `APP_DB_PASSWORD`, `REPLICATION_PASSWORD`. В каталоге `backend` тоже создайте `.env`: тот же **`APP_DB_PASSWORD`**, что и в БД, плюс собственный случайный `JWT_SECRET` (минимум 32 байта). Для генерации паролей используйте `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Не публикуйте `.env`.
3. В каталоге `database` выполните `docker compose up -d db`. Этот Compose создаёт сеть `phonebook-shared` и запускает PostgreSQL. При новом пустом томе создаются три таблицы, ограниченные роли, индексы.
4. Затем в каталоге `backend` выполните `docker compose up --build -d core supporting`. Backend присоединяется к готовой сети `phonebook-shared` и использует PostgreSQL по адресу `db:5432`.
5. Откройте `http://localhost:5000/health`, `http://localhost:8001/docs` и `http://localhost:5000/api/about`.
6. Для проверки реплики в каталоге `database` выполните `docker compose --profile replication up -d db-replica`, затем `docker compose exec db-replica psql -U phonebook -d phonebook -c "SELECT pg_is_in_recovery();"` (ожидается `t`).

Остановка: сначала `docker compose down` в `backend`, затем `docker compose down` в `database`. **Не выполнять `docker compose down -v`** с рабочими данными: эта команда удаляет том БД.

Если уже существует старая база, созданная прежним объединённым Compose, данные остаются в её старом томе: новый отдельный Compose использует **другое имя проекта и другой том**. Не удаляйте старый том. Для переноса понадобится резервная копия и восстановление — это отдельная миграция, а не автоматический перенос.

### Локальный запуск Python

Установите зависимости: `python -m pip install -r requirements.txt`. Запустите БД через Compose из ветки Database Engineer. Для локального Flask установите переменные окружения `JWT_SECRET` и `DATABASE_URL` (адрес `127.0.0.1:5432` и пароль `APP_DB_PASSWORD`), затем запустите `python app.py`. В соседнем терминале: `uvicorn supporting_api:app --host 127.0.0.1 --port 8001`. Локальные Python-процессы не нужно запускать одновременно с контейнерами Backend на тех же портах.

## API для Frontend

Все запросы, кроме регистрации, входа, `/api/about`, `/api/hash/{value}` и `/health`, требуют заголовок:

`Authorization: Bearer <access_token>`

`POST /api/auth/refresh` требует **refresh_token** в этом же заголовке. Новый `access_token` можно использовать для последующих запросов.

| Метод | Адрес | Назначение |
|---|---|---|
| POST | `/api/auth/register` | Регистрация `{ "user_name": "student", "password": "password123" }` |
| POST | `/api/auth/login` | Вход, выдача `access_token` и `refresh_token` |
| POST | `/api/auth/refresh` | Получить новый `access_token` |
| GET | `/api/users/me` | Текущий пользователь |
| GET | `/<username>` | Информация о владельце токена, только для самого пользователя |
| GET | `/api/groups` | Список групп |
| POST | `/api/groups` | Создать группу `{ "name": "Семья" }` |
| DELETE | `/api/groups/<id>` | Удалить группу |
| GET | `/api/contacts` | Контакты с поиском, сортировкой и пагинацией |
| POST | `/api/contacts` | Создать `{ "name": "Анна", "phone": "+79990000000", "group_id": null }` |
| GET | `/api/contacts/<id>` | Получить контакт |
| PUT/PATCH | `/api/contacts/<id>` | Изменить поля контакта |
| DELETE | `/api/contacts/<id>` | Удалить контакт |
| GET | `/api/stats` | Количество контактов по группам для Chart.js |
| GET | `/api/analytics` | Статистика через FastAPI с резервным ответом |
| GET | `/api/hash/<value>` | SHA-256 строки, JSON `request` и `result` |
| GET | `/api/about` | Описание из `about.json` |
| GET | `/dashboard` | HTML-страница статистики, когда Frontend добавит `static/dashboard.html` |
| GET | `/about` | HTML-страница описания при наличии `static/about.html`, иначе JSON |
| GET | `/health` | Проверка Flask |

Для `GET /api/contacts` поддерживаются параметры:

- `search` — поиск по имени и телефону;
- `group_id` — фильтр по группе;
- `sort_by` — `name`, `phone` или `created_at`;
- `order` — `asc` или `desc`;
- `page` — номер страницы, начиная с 1;
- `per_page` — количество записей, от 1 до 100.

Пример: `/api/contacts?search=Анна&sort_by=name&order=asc&page=1&per_page=10`.

Ответ содержит `items`, `total`, `page`, `per_page`, `pages`. Ошибки возвращаются в JSON-поле `error`. Удаление возвращает HTTP 204.

## Интеграция Frontend

Напарник добавляет `static/index.html`, `static/dashboard.html`, `static/profile.html` и JavaScript-файлы. Flask автоматически отдаёт `index.html` по `/` и `dashboard.html` по `/dashboard`, когда файлы появятся. Пока этих файлов нет, эти маршруты возвращают информационный JSON — это **не готовый Frontend**.

Для страницы профиля используйте `GET /api/users/me` либо `GET /<username>` с access-токеном. Кнопка обновления токена должна вызывать `POST /api/auth/refresh` с refresh-токеном и сохранять новый access-токен. Данные для диаграмм находятся в `GET /api/stats`; диаграммы реализуются на Frontend через Chart.js.

## Тесты и Git

`python -m pytest -q` — проверка маршрутов Flask, обработки ошибок с подменой функций БД и маршрутов FastAPI. Отдельная GitHub Actions-проверка должна скачивать базовую ветку Данила и запускать сервисы обоих участников. Эти тесты **не заменяют** интеграционную проверку с настоящим PostgreSQL и Docker.

Рабочие ветки: `main`, `develop`, `feature/<username>/<task-name>`, `release/v1.0`. Коммиты оформляются на английском, одно логическое изменение — один коммит.

## Безопасность и ограничения

Пароли хранятся как хеши Werkzeug. SQL-запросы параметризованы, а поля сортировки выбираются из фиксированного списка. Каждый контакт привязан к пользователю, и API проверяет владельца записи. Секреты из `.env` нельзя добавлять в Git. В `.env.example` JWT_SECRET намеренно оставлен пустым. Для JWT нужен отдельный случайный ключ длиной не менее 32 байт.

Это учебный проект. Перед публичным развёртыванием понадобятся HTTPS, защита от перебора паролей, более строгая конфигурация CORS и проверка всех контейнеров. 
