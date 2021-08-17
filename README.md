# Учебный проект Yatube, итоговый

Yatube это социальная сеть для публикации постов, комментирования их, подписок на интересующих
людей и группы. Сделан с учебной целью для практики написания сервиса на фреймворке Django.
В финальной версии добавлены возможность загружать картинки с помощью Pillow и sorl-thumbnail,
модель подписок и комментирования и кеширование главной страницы.
Используются версия Python 3.7 и фреймворки Django 2.2.

## Как запустить проект:

Создать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
source venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python manage.py migrate
```

Запустить проект:

```
python manage.py runserver
```
