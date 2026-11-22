# project-web — Телефонный справочник

Учебное Full Stack веб-приложение для хранения личных контактов. Пользователь регистрируется, входит в систему, создаёт группы, добавляет контакты и управляет ими. Контакты разных пользователей изолированы.

> **Статус репозитория:** здесь ведётся командная разработка. Сейчас ветка `main` содержит обзор и документацию; исходники приложения находятся в рабочих ветках ниже. **Полностью объединённая версия для сдачи пока не подготовлена.**

## Участники и рабочие ветки

| Роль | Ветка | Что содержит |
|---|---|---|
| Backend Engineer | [`feature/ivan/backend`](../../tree/feature/ivan/backend) | Flask API, FastAPI, Docker, тесты, SQL-интеграция |
| Frontend Engineer | [`feature/darkandcryssis-eng/frontend`](../../tree/feature/darkandcryssis-eng/frontend) | HTML, CSS, JavaScript, страницы приложения |
| Database Engineer | [`feature/database-engineering`](../../tree/feature/database-engineering) | Копия Backend как рабочая основа, SQL-схема, настройка PostgreSQL и репликации; [список задач](../../blob/feature/database-engineering/db/README.md) |

**Важно:** разработка роли Database Engineer только выделена в отдельную ветку, её задачи ещё не завершены. Ветка Backend не изменена при создании Database Engineering. Для полноценной сдачи требуется объединение и проверка всех частей проекта.

## Архитектура

- **Presentation:** HTML, Bootstrap, JavaScript (`fetch`). Интерфейс разрабатывается отдельно и подключается к API.
- **Business Logic / Core:** Flask, Blueprint, JWT, обработка запросов.
- **Supporting:** FastAPI, JSON-сервис хеширования и аналитики.
- **Data Access / Storage:** `db.py`, обычные SQL-запросы через `psycopg`, PostgreSQL. ORM не используется.

Схема БД: `users` → `groups`, `users` → `contacts`, `groups` → `contacts`. Три таблицы связаны внешними ключами. Повторяющиеся сведения вынесены в отдельные таблицы; структура соответствует третьей нормальной форме.

## Быстрый запуск через Docker Compose

> **Предупреждение для проверяющего.** Эти инструкции относятся к исходникам в рабочих ветках, а не к текущей `main`. На GitHub пока выявлен блокер чистого развёртывания: `core` требует `APP_DB_PASSWORD` и роль `phonebook_app`, но в `.env.example` нет этой переменной, а в `init.sql` роль ещё не создаётся. Локальная БД разработчика уже была настроена вручную. Задача исправления закреплена за Database Engineer; до её выполнения запуск проекта на новой машине не гарантирован.


Нужен Docker Desktop. В корне проекта:

1. После исправления инициализации роли приложения: скопировать `.env.example` в `.env` и задать обязательные переменные, включая `APP_DB_PASSWORD`. Сгенерировать секрет командой `python -c "import secrets; print(secrets.token_urlsafe(48))"` и записать результат в `JWT_SECRET` в файле `.env`. Не добавлять `.env` в Git. Для локальной демонстрации остальные значения можно оставить.
2. Выполнить `docker compose up --build -d`.
3. Открыть `http://localhost:5000/health` — основной Flask-сервис.
4. Открыть `http://localhost:8001/docs` — автоматическая документация FastAPI.
5. Открыть `http://localhost:5000/api/about` — описание проекта.

Остановка: `docker compose down`. Команда `docker compose down -v` **удаляет данные БД**, её не следует использовать для обычной остановки.

Скрипт `init.sql` выполняется PostgreSQL **только при первом создании пустого тома**. После изменения структуры таблиц необходимо использовать миграцию либо пересоздать тестовую БД с осознанием потери данных.

## Запуск Backend через PyCharm (Python 3.13)

1. Открыть папку проекта в PyCharm.
2. В терминале проекта выполнить `python -m pip install -r requirements.txt`.
3. Запустить PostgreSQL: `docker compose up -d db`.
4. В одном терминале выполнить `uvicorn supporting_api:app --host 127.0.0.1 --port 8001`.
5. В другом терминале выполнить `python app.py`.
6. Проверить `http://127.0.0.1:5000/health`.

При локальном запуске `db.py` использует адрес `postgresql://phonebook:phonebook@localhost:5432/phonebook`, если `DATABASE_URL` не задан. Если изменён `DB_PASSWORD`, необходимо также задать `DATABASE_URL` в конфигурации запуска PyCharm. `JWT_SECRET` тоже можно задать в переменных окружения. JWT_SECRET обязателен: при запуске из PyCharm его нужно задать в переменных окружения (например, в PowerShell: `$env:JWT_SECRET = (python -c "import secrets; print(secrets.token_urlsafe(48))")`). Без него выдача и проверка JWT-токенов не работают.

**Важно:** если запущены контейнеры `core` и `supporting`, локальные команды `python app.py` и `uvicorn ...` займут те же порты. Для работы через PyCharm сначала остановите контейнеры приложения: `docker compose stop core supporting`.

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

## Реплика PostgreSQL (дополнительное требование из видео)

Основная база запускается сервисом `db`. Дополнительная read-only реплика запускается командой:

`docker compose --profile replication up --build -d`

При первом старте реплика выполняет `pg_basebackup` с основной базы и запускается в режиме standby. Проверить режим можно командой:

`docker compose exec db-replica psql -U phonebook -d phonebook -c "SELECT pg_is_in_recovery();"`

Ожидается `t`. Реплика не используется для записи контактов. Конфигурацию репликации необходимо дополнительно проверить на машине с Docker; здесь она подготовлена, но не прошла контейнерное тестирование.

## Тесты и Git

`python -m pytest -q` — проверка маршрутов Flask с подменой функций БД и маршрутов FastAPI. Эти тесты **не заменяют** интеграционную проверку с настоящим PostgreSQL и Docker.

Используемые ветки: `main`, `develop`, `feature/ivan/backend`, `feature/darkandcryssis-eng/frontend`, `feature/database-engineering`. Для общей версии потребуется интеграция в `main`. Коммиты оформляются на английском, одно логическое изменение — один коммит.

## Безопасность и ограничения

Пароли хранятся как хеши Werkzeug. SQL-запросы параметризованы, а поля сортировки выбираются из фиксированного списка. Каждый контакт привязан к пользователю, и API проверяет владельца записи. Секреты из `.env` нельзя добавлять в Git. В `.env.example` JWT_SECRET намеренно оставлен пустым. Для JWT нужен отдельный случайный ключ длиной не менее 32 байт.

Это учебный проект. Перед публичным развёртыванием понадобятся HTTPS, защита от перебора паролей, более строгая конфигурация CORS и проверка всех контейнеров. 
