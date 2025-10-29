#!/usr/bin/env python3
"""
Скрипт для завершения всех предыдущих версий проекта
"""
import os
import sys
import signal
import subprocess
from pathlib import Path

def cleanup_old_processes():
    """Завершает все предыдущие версии проекта"""
    print("Завершение всех предыдущих версий проекта...")
    
    # Завершаем все процессы python, связанные с проектом
    try:
        # На Windows используем taskkill
        if os.name == 'nt':
            result = subprocess.run(['tasklist'], capture_output=True, text=True)
            if result.returncode == 0:
                processes = result.stdout
                # Ищем все процессы python, которые могут быть частью проекта
                for line in processes.split('\n'):
                    if 'python.exe' in line.lower() and ('main.py' in line or 'casting' in line.lower() or 'quality' in line.lower()):
                        pid = line.split()[1]  # PID находится во втором столбце
                        print(f"Завершение процесса python.exe с PID {pid}")
                        subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                        
        # Проверяем, есть ли запущенный сервер Flask
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 5005))
        if result == 0:
            print("Обнаружен запущенный сервер Flask на порту 5005")
            # На Windows завершаем процесс, использующий порт
            subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if ':5005' in line and 'LISTENING' in line:
                    pid = line.split()[-1]
                    print(f"Завершение процесса на порту 5005 (PID: {pid})")
                    subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
        sock.close()
        
        print("Завершение всех процессов завершено.")
        
    except Exception as e:
        print(f"Ошибка при завершении процессов: {e}")
    
if __name__ == "__main__":
    cleanup_old_processes()