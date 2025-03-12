
---

# **Foodgram — Продуктовый помощник** 

**Foodgram** — это современное веб-приложение для любителей кулинарии. Здесь вы можете:
- Публиковать свои рецепты.
- Добавлять понравившиеся рецепты в избранное.
- Формировать список покупок для выбранных рецептов.
- Подписываться на любимых авторов и следить за их новыми рецептами.
- Доступ к [сайту](https://foodgrammm.serveblog.net/recipes) 


---

## **Как запустить проект** 

### **1. Клонируйте репозиторий**
```bash
git clone https://github.com/EgorLishevich/foodgram.git
cd foodgram/infra
```

### **2. Создайте файл `.env`**

### **3. Запустите Docker**
Соберите и запустите контейнеры:
```bash
docker-compose up -d --build
```

### **4. Выполните миграции**
Примените миграции для настройки базы данных:
```bash
docker-compose exec backend python manage.py migrate
```

### **5. Заполните базу ингредиентами**
Загрузите предустановленные данные об ингредиентах и тегах:
```bash
docker-compose exec backend python manage.py load_ingredients
docker-compose exec backend python manage.py load_tags
```

### **6. Создайте суперпользователя**
Создайте учетную запись администратора:
```bash
docker-compose exec backend python manage.py createsuperuser
```

---

## **Доступ к приложению** 

После выполнения всех шагов приложение будет доступно по следующим адресам:

- **Веб-интерфейс:** [http://localhost/](http://localhost/)
- **API (Swagger):** [http://localhost/api/docs/](http://localhost/api/docs/)
- **Админ-панель:** [http://localhost/admin/](http://localhost/admin/)

---

## **Технологии** 

### **Backend**
- **Python 3**
- **Django**
- **Django REST Framework**
- **PostgreSQL**

### **Frontend**
- **React**

### **Инфраструктура**
- **Docker**
- **Gunicorn**
- **Nginx**

---

## **Авторы** 

- [Егор Лишевич](https://github.com/EgorLishevich)

---

## **Благодарности** 

Спасибо за использование **Foodgram**! Если у вас есть вопросы или предложения, пожалуйста, создайте issue в репозитории.

---

### **Приятного использования!**

---