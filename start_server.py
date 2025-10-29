#!/usr/bin/env python3
"""
Скрипт для запуска сервера системы контроля качества
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """Проверяет наличие необходимых зависимостей"""
    try:
        import flask
        import flask_cors
        print("✅ Flask установлен")
        return True
    except ImportError:
        print("❌ Flask не установлен")
        print("Установите зависимости: pip install flask flask-cors")
        return False

def start_server():
    """Запускает сервер"""
    if not check_dependencies():
        return
    
    print("🚀 Запуск сервера системы контроля качества...")
    print("📍 URL: http://localhost:5005")
    print("🛑 Для остановки нажмите Ctrl+C")
    
    # Открываем браузер через 2 секунды
    def open_browser():
        time.sleep(2)
        webbrowser.open("http://localhost:5005")
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Запускаем сервер
    try:
        # Импортируем и запускаем приложение из main
        import sys
        import os
        # Добавляем директорию проекта в путь Python
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from main import app
        app.run(host='127.0.0.1', port=5005, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Убедитесь, что все зависимости установлены корректно.")
        input("Нажмите любую клавишу для продолжения...")

if __name__ == "__main__":
    start_server()