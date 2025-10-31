# 📸 UI Screenshots

Эта папка предназначена для хранения скриншотов всех ключевых страниц системы.

## Структура папок

```
ui-screenshots/
├── home/              # Главная страница (welcome screen)
├── shifts/            # Создание и управление сменами
├── controllers/       # Управление контролёрами
├── quality-control/   # Ввод данных контроля качества
├── reports/           # Отчёты и статистика
└── qr-scan/          # QR-сканирование
```

## Как добавить скриншоты

### 1. Запустить приложение

```bash
python main.py
```

### 2. Открыть браузер

Перейти на http://localhost:5000

### 3. Сделать скриншоты

Для каждой страницы создать скриншоты следующих состояний:

#### Welcome Screen (`home/`)
- `welcome-default.png` - начальный экран с анимацией
- `welcome-mobile.png` - мобильная версия

#### Create Shift (`shifts/`)
- `create-shift-empty.png` - пустая форма
- `create-shift-filled.png` - заполненная форма
- `create-shift-error.png` - форма с ошибками валидации
- `create-shift-mobile.png` - мобильная версия

#### Work Menu (`shifts/`)
- `work-menu-default.png` - рабочее меню с активной сменой
- `work-menu-with-stats.png` - с заполненной статистикой
- `work-menu-search.png` - поиск маршрутной карты
- `work-menu-qr-active.png` - активный QR-сканер
- `work-menu-mobile.png` - мобильная версия

#### Input Control (`quality-control/`)
- `input-control-empty.png` - пустая форма
- `input-control-filled.png` - заполненная форма
- `input-control-with-defects.png` - с выбранными дефектами
- `input-control-mobile.png` - мобильная версия

#### Manage Controllers (`controllers/`)
- `manage-controllers-list.png` - список контролёров
- `manage-controllers-empty.png` - нет контролёров
- `manage-controllers-mobile.png` - мобильная версия

#### Reports (`reports/`)
- `reports-list.png` - список смен
- `reports-empty.png` - нет данных
- `reports-mobile.png` - мобильная версия

#### QR Scanning (`qr-scan/`)
- `qr-scan-camera-active.png` - активная камера
- `qr-scan-success.png` - успешное сканирование
- `qr-scan-mobile.png` - мобильная версия (основной use case)

### 4. Формат скриншотов

- **Формат**: PNG
- **Качество**: Высокое (без сжатия)
- **Размер**: Full screen (не обрезать браузер)
- **Разрешение Desktop**: 1920x1080 или 1440x900
- **Разрешение Mobile**: 375x667 (iPhone SE) или 414x896 (iPhone X)

### 5. Инструменты для создания скриншотов

#### Chrome DevTools
1. F12 → Toggle device toolbar (Ctrl+Shift+M)
2. Выбрать устройство (Responsive, iPhone, iPad)
3. Ctrl+Shift+P → "Capture screenshot"

#### Firefox Developer Tools
1. F12 → Responsive Design Mode (Ctrl+Shift+M)
2. Screenshot icon в toolbar

#### Расширения браузера
- **Awesome Screenshot** - для полных страниц
- **Full Page Screen Capture** - скриншоты с прокруткой
- **Nimbus Screenshot** - с аннотациями

### 6. Naming Convention

Формат: `<page>-<state>-<device>.png`

Примеры:
- `welcome-default.png`
- `create-shift-filled-mobile.png`
- `work-menu-with-stats.png`
- `input-control-error.png`

## Дополнительные типы скриншотов

### Flash Messages
- `flash-success.png` - зеленое уведомление
- `flash-error.png` - красное уведомление
- `flash-warning.png` - желтое уведомление
- `flash-info.png` - голубое уведомление

### Interactive States
- `button-hover.png` - кнопка при наведении
- `input-focus.png` - поле ввода в фокусе
- `table-hover.png` - таблица с hover на строке

### Loading States
- `loading-search.png` - индикация поиска
- `loading-save.png` - сохранение данных

## Альтернатива: Автоматические скриншоты

Если нужно автоматизировать создание скриншотов, можно использовать:

### Playwright

```python
# screenshot.py
from playwright.sync_api import sync_playwright

def take_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Welcome screen
        page.goto('http://localhost:5000/')
        page.screenshot(path='docs/ui-screenshots/home/welcome-default.png')
        
        # Mobile version
        page.set_viewport_size({'width': 375, 'height': 667})
        page.screenshot(path='docs/ui-screenshots/home/welcome-mobile.png')
        
        # ... остальные страницы
        
        browser.close()

if __name__ == '__main__':
    take_screenshots()
```

Установка:
```bash
pip install playwright
playwright install chromium
```

### Selenium

```python
from selenium import webdriver

driver = webdriver.Chrome()
driver.get('http://localhost:5000/')
driver.save_screenshot('docs/ui-screenshots/home/welcome-default.png')
driver.quit()
```

## Текущее состояние

⚠️ **Скриншоты еще не созданы**

Эта документация предоставляет полные инструкции для создания визуальной документации.
Для создания скриншотов необходимо запустить приложение и использовать один из описанных методов.

---

*Инструкция обновлена: 2024*
