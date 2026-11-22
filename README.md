# Database Engineering — телефонный справочник

Рабочая ветка третьего участника: **`feature/danil/postgresql`**. Роль — **Database Engineer / DBA**.

Это **отдельная часть проекта**, а не копия Backend: здесь только PostgreSQL, проектирование данных, SQL, индексы, роли и потоковая репликация. Flask, FastAPI, JWT и HTTP-обработчики находятся у [Backend-разработчика](https://github.com/ivansemkov15-ui/project-web/tree/feature/ivan/backend).

## Структура

| Файл | Назначение |
|---|---|
| `init.sql` | Нормализованная схема `users`, `groups`, `contacts`, индексы, связи |
| `db/schema.dbml` | ER-модель для dbdiagram.io (детали внешних ключей см. в SQL) |
| `db/setup-app-role.sh` | Роль приложения `phonebook_app` и минимальные права |
| `db/setup-replication.sh` | Роль `replicator` для PostgreSQL |
| `db/start-replica.sh` | Запуск резервной standby-БД с `pg_basebackup` |
| `docker-compose.yml` | Главная БД и реплика без Flask/FastAPI |
| `.env.example` | Шаблон обязательных настроек БД |

## Нормализация и целостность

Три связанные сущности: `users`, `groups`, `contacts`. Пароли хранятся как хеши, не как исходные строки. Таблицы рассчитаны на третью нормальную форму. `groups.user_id` и `contacts.user_id` ссылаются на владельца в `users`; составной внешний ключ `contacts(user_id, group_id)` не позволяет назначить контакту чужую группу. Удаление группы сбрасывает только `contacts.group_id` в `NULL`, контакт сохраняется. Уникальные ограничения и индексы перечислены в `init.sql`.

Схему и SQL-запросы согласовывать с Backend-разработчиком; интерфейс Flask не менять в этой ветке.

## Запуск

1. Скопировать `.env.example` в `.env`.
2. Задать три разные случайные строки `DB_PASSWORD`, `APP_DB_PASSWORD`, `REPLICATION_PASSWORD`; например, генерировать каждую отдельным запуском `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
3. Выполнить `docker compose up -d db`. Создаётся именованная сеть `phonebook-shared` для подключения Backend. PostgreSQL слушает локальный порт `5432`.
4. Проверить права: `docker compose exec db psql -U phonebook -d phonebook -c "SELECT rolname, rolsuper FROM pg_roles WHERE rolname = 'phonebook_app';"`; для `phonebook_app` должно быть `f`.
5. Запуск реплики: `docker compose --profile replication up -d db-replica`. Проверка: `docker compose exec db-replica psql -U phonebook -d phonebook -c "SELECT pg_is_in_recovery();"`; ожидается `t`.

При первом создании пустого тома PostgreSQL выполняет SQL и оба установочных скрипта автоматически. На существующей базе установочные скрипты нужно применять отдельно; они **не** пересоздадут старые таблицы. `docker compose down -v` удаляет данные — не выполнять на рабочей базе.

## Подключение Backend

В соседнем каталоге клонировать `feature/ivan/backend`. В его `.env` задать такой же `APP_DB_PASSWORD`, как здесь, и отдельный `JWT_SECRET`, затем `docker compose up -d --build core supporting`. Backend подключается к БД по имени `db` через общую сеть.

## Проверка перед сдачей

Добавленная конфигурация требует проверки на чистой системе и подтверждения успешных тестов. Наличие кода не является доказательством, что PostgreSQL standby уже работает в контейнерах. `main` и `develop` предназначены соответственно для описания и интеграции общего проекта.
