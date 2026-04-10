# BETON_CALCULATION

Структура проекта:

- `app/handlers` - обработчики команд и пользовательских действий.
- `app/states` - состояния диалогов.
- `app/keyboards` - reply и inline клавиатуры.
- `app/services` - инфраструктурные сервисы.
- `app/domain` - доменные сущности и будущая логика расчета.
- `app/utils` - вспомогательные функции.
- `prices` - Excel-файлы с прайсами.

Запуск:

1. Установить зависимости: `pip install -r requirements.txt`
2. Заполнить `.env`
3. Запустить бота: `python main.py`
