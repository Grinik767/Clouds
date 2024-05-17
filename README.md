# Clouds

## Описание

Небольшая консольная утилита для работы с облачными хранилищами. Поддерживаются Яндекс.Диск и Dropbox

## Подготовка

1. Установить все библиотеки из requirements.txt
2. Получить данные для входа:
    1. Яндекс:
        1. Перейти по
           ссылке https://oauth.yandex.ru/authorize?response_type=token&client_id=773e0d9487fa477e88060e1178f31bc1
        2. Войти в свой аккаунт
        3. Сохранить полученный токен
    2. Dropbox
        1. Получить токен согласно Dropbox API (раздел авторизация)
        2. Сохранить полученный токен
3. Создать файл ".env.prod" и добавить две переменные "AUTH_TOKEN_YANDEX" и "AUTH_TOKEN_DROPBOX" соответствующие токены.
   Файл должен лежать в директории скрипта.

## Запуск

Запуск необходимо произвести из командной строки (файл для запуска "main.py"). Пример запуска:
```python main.py info --cloud yandex``` (команда получает информацию об Яндекс.Диске пользователя)

## Доступные команды

Посмотреть все доступные команды можно прописав: ```python main.py --help```.
Также для каждой команды существует свой --help. Пример ```python main.py info --help```

## Особенности использования

1. Пути для скачивания/загрузки файлов должны содержать название файла. Пример: ```/content/file.docx```
2. У Dropbox нет возможности посмотреть корневую папку (а у Яндекса есть, путь: ```/```)
3. Лимиты на выгрузку на один файл:
    1. Яндекс: до 1 ГБ
    2. Dropbox: до 150 МБ