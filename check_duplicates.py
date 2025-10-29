#!/usr/bin/env python3
"""
Скрипт для проверки наличия дубликатов в таблице типов дефектов
"""

import sqlite3
from collections import defaultdict

# Путь к базе данных
DATABASE_PATH = 'data/quality_control.db'

def check_duplicates():
    """Проверяет наличие дубликатов в таблице типов дефектов"""
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Получаем все типы дефектов
        cursor.execute('''
            SELECT td.id, td.название, cd.название as категория
            FROM типы_дефектов td
            JOIN категории_дефектов cd ON td.категория_id = cd.id
            ORDER BY cd.название, td.название
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        # Группируем по названию и категории
        defects_by_name_category = defaultdict(list)
        for row in rows:
            defect_id, defect_name, category = row
            key = (defect_name, category)
            defects_by_name_category[key].append(defect_id)
        
        # Находим дубликаты
        duplicates = {k: v for k, v in defects_by_name_category.items() if len(v) > 1}
        
        print(f"Всего типов дефектов: {len(rows)}")
        print(f"Уникальных названий: {len(defects_by_name_category)}")
        print(f"Дублирующихся названий: {len(duplicates)}")
        
        if duplicates:
            print("\nНайдены дубликаты:")
            for (name, category), ids in duplicates.items():
                print(f"  {category}: '{name}' - {len(ids)} записей (ID: {ids})")
        else:
            print("\nДубликаты не найдены.")
            
        return len(duplicates) > 0
        
    except Exception as e:
        print(f"Ошибка при проверке дубликатов: {e}")
        return False

if __name__ == '__main__':
    has_duplicates = check_duplicates()
    if has_duplicates:
        print("\n⚠️  В базе данных остались дубликаты.")
    else:
        print("\n✅ Дубликаты в базе данных отсутствуют.")