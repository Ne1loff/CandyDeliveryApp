# CandyDeliveryApp
## Установка зависимостей
```
pip3 install -r requirements.txt
```
## Запуск 
Параметры подключения к базе данных можно указать в переменной окружения ```DB_URL```, например: ```DB_URL=sqlite:///database/app.db```
```
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```
## Запуск тестов
```
python3 -m pytest
```
## Docs
Документация доступна после запуска сервера по пути ```/docs``` или ```/redoc```