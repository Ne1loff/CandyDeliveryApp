# CandyDeliveryApp
## Установка зависимостей
```
pip install -r requirements.txt
```
## Запуск 
Параметры подключения к базе данных можно указать в переменной окружения ```DB_URL```, например: ```DB_URL=sqlite:///database/app.db```
```
uvicorn app.main:app
```
## Запуск тестов
```
pytest
```