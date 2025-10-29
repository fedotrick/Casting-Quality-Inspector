import sqlite3

def analyze_database():
    print('Подключаюсь к базе данных...')
    conn = sqlite3.connect('data/quality_control.db')
    cursor = conn.cursor()
    
    # Получаем список таблиц
    print('Получаю список таблиц...')
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table";')
    tables = cursor.fetchall()
    print(f'Найдено {len(tables)} таблиц:')
    
    for table in tables:
        table_name = table[0]
        print(f'\n--- Таблица: {table_name} ---')
        
        # Получаем структуру таблицы
        cursor.execute(f'PRAGMA table_info({table_name})')
        columns = cursor.fetchall()
        print('Столбцы:')
        for col in columns:
            cid, name, type_, notnull, default_value, pk = col
            print(f'  {name} ({type_}) - NOT NULL: {bool(notnull)}, PRIMARY KEY: {bool(pk)}')
        
        # Получаем количество записей
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
            count = cursor.fetchone()[0]
            print(f'Количество записей: {count}')
        except Exception as e:
            print(f'Не удалось получить количество записей: {str(e)}')
    
    # Проверим также внешние ключи
    print('\n=== Внешние ключи ===')
    for table in tables:
        table_name = table[0]
        cursor.execute(f'PRAGMA foreign_key_list({table_name})')
        foreign_keys = cursor.fetchall()
        if foreign_keys:
            print(f'Внешние ключи для {table_name}:')
            for fk in foreign_keys:
                print(f'  {fk[3]} -> {fk[2]}.{fk[4]}')
    
    conn.close()
    print('\nАнализ завершен.')

if __name__ == "__main__":
    analyze_database()