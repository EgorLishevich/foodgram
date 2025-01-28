# Foodgram
«Фудграм» — сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов.

---
## Backend stack:
- Python
	- Django rest-framework
	- django-filter
	- psycopg2-binary
	- reportlab
	- pytest
	- PyYAML
	- gunicorn
	- python-dotenv
- DB
	- PostgreSQL
	- SQLite
- Docker
- nginx


---
## CD/CI для развертывания

### Команды локального развертывания с Докером 
##### Клонирование репозитория.
`git clone https://github.com/EgorLishevich/foodgram.git`
##### Создание .env файла
`SECRET_KEY=django-key...`\
`DEBUG=False`\
`ALLOWED_HOSTS=<ваш хост>,127.0.0.1,localhost`\
`POSTGRES_USER=<имя пользователя>`\
`POSTGRES_PASSWORD=<пароль>`\
`POSTGRES_DB=<имя базы данных>`\
`DB_HOST=<хост>`\
`DB_PORT=<порт>`
##### Подъем контейнераов в Докере.
`sudo docker compose -f docker-compose.production.yml pull`\
`sudo docker compose -f docker-compose.production.yml down`
##### Подготовка базы:
Миграции:
`sudo docker compose -f docker-compose.production.yml exec backend python manage.py makemigrations`\
`sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate`\
Создание супер-пользователя:
`sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser`
##### Сборка статики.
`sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput`
##### Запуск сервера.

`sudo docker compose -f docker-compose.production.yml up -d`