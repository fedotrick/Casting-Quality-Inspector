# 🏗️ Структура интерфейса - Interface Structure

> **Архитектура и организация UI системы контроля качества**

---

## 📋 Содержание

1. [Общая архитектура](#общая-архитектура)
2. [Layout структура](#layout-структура)
3. [Типы страниц](#типы-страниц)
4. [Технический стек](#технический-стек)
5. [Особенности реализации](#особенности-реализации)
6. [Структура файлов](#структура-файлов)

---

## 1. 🎯 Общая архитектура

### Архитектурная модель

```
┌─────────────────────────────────────────────────┐
│                  Browser (Client)               │
│  ┌───────────────────────────────────────────┐  │
│  │         HTML Templates (Jinja2)           │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │        Static Assets                │  │  │
│  │  │  - CSS (style.css)                  │  │  │
│  │  │  - JavaScript (main.js)             │  │  │
│  │  │  - External libs (html5-qrcode)     │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────┘
                 │ HTTP Requests (GET/POST)
                 │
┌────────────────▼────────────────────────────────┐
│            Flask Application Server             │
│  ┌───────────────────────────────────────────┐  │
│  │           Blueprints                      │  │
│  │  ┌─────────────┐    ┌─────────────┐      │  │
│  │  │  UI Routes  │    │ API Routes  │      │  │
│  │  │  (HTML)     │    │  (JSON)     │      │  │
│  │  └─────────────┘    └─────────────┘      │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │           Services Layer                  │  │
│  │  - shift_service                          │  │
│  │  - database_service                       │  │
│  │  - control_service                        │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │         Repository Layer                  │  │
│  │  - ShiftRepository                        │  │
│  │  - ControllerRepository                   │  │
│  │  - DefectRepository                       │  │
│  └───────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────┘
                 │ SQL Queries
                 │
┌────────────────▼────────────────────────────────┐
│              SQLite Database                    │
│  - quality_control.db                           │
│  - Cyrillic table/column names                  │
│                                                  │
│  External DB Integration:                       │
│  - database.external_db_integration             │
│  - Foundry DB (Литейка)                         │
└─────────────────────────────────────────────────┘
```

---

### Принципы архитектуры

1. **MVC Pattern** (Model-View-Controller)
   - **Model**: Repository + Database layer
   - **View**: Jinja2 Templates
   - **Controller**: Flask Blueprints (UI + API)

2. **Separation of Concerns**
   - UI logic отделена от бизнес-логики
   - API endpoints для AJAX запросов
   - Service layer для бизнес-операций

3. **Single Page Flow**
   - Каждая страница = отдельный шаблон
   - Наследование от базового layout
   - Минимальная JavaScript-интерактивность

4. **Session-based State**
   - Хранение ID активной смены в session
   - Filesystem session storage
   - Автоматическая очистка при закрытии

---

## 2. 📐 Layout структура

### Base Template (`base.html`)

**Структура**:
```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Система контроля качества{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- Flash Messages Section -->
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            <div class="flash-messages">
                {% for category, message in messages %}
                    <div class="flash-message flash-{{ category }}">
                        {{ message }}
                    </div>
                {% endfor %}
            </div>
        {% endif %}
    {% endwith %}
    
    <!-- Main Content Container -->
    <div class="container">
        {% block content %}{% endblock %}
    </div>
    
    <!-- Common JavaScript -->
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

---

### Layout компоненты

#### 1. Flash Messages
- **Расположение**: Вверху страницы, над контейнером
- **Типы**: success, error, info, warning
- **Поведение**: Auto-hide через 5 секунд
- **Стили**: Центрированные, max-width 800px

#### 2. Container
- **Класс**: `.container`
- **Max-width**: 800px
- **Центрирование**: `margin: 0 auto`
- **Padding**: 30px
- **Фон**: белый
- **Border-radius**: 10px
- **Тени**: нет (чистый дизайн)

#### 3. Content Blocks
Каждая страница определяет:
```jinja2
{% extends "base.html" %}

{% block title %}Название страницы{% endblock %}

{% block extra_css %}
<!-- Специфичные стили для страницы -->
{% endblock %}

{% block content %}
<!-- Основной контент -->
{% endblock %}

{% block extra_js %}
<!-- Специфичные скрипты для страницы -->
{% endblock %}
```

---

### Responsive Layout

**Breakpoints**:
```css
/* Desktop (default) */
.container {
    max-width: 800px;
    padding: 30px;
}

/* Mobile (< 768px) */
@media (max-width: 768px) {
    .container {
        padding: 15px;
        margin: 10px;
    }
    
    .btn {
        display: block;
        width: 100%;
        margin: 10px 0;
    }
    
    .stats-grid {
        grid-template-columns: 1fr;  /* Одна колонка */
    }
}
```

**Adaptive элементы**:
- ✅ Кнопки: full-width на мобильных
- ✅ Таблицы: горизонтальная прокрутка
- ✅ Формы: 100% ширина полей
- ✅ Grid: автоматическая адаптация колонок

---

## 3. 📄 Типы страниц

### 3.1 Landing Page (Welcome Screen)

**URL**: `/`  
**Template**: `welcome.html`  
**Тип**: Специальная страница с анимацией

**Особенности**:
- Полноэкранный дизайн (`height: 100vh`)
- Градиентный фон
- Анимации (логотип, текст, фон)
- Единственная кнопка действия

**Layout override**:
```css
body {
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    overflow: hidden;
}

.container {
    background: transparent;  /* Отключение белого фона */
}
```

**Компоненты**:
- Animated logo (🏭)
- Title с slide-in анимацией
- Subtitle с fade-in
- CTA button с pulse анимацией
- Animated particles background

---

### 3.2 Form Pages (Формы создания/редактирования)

**Примеры**:
- `/create-shift` - Создание смены
- `/input-control` - Ввод контроля качества

**Структура**:
```html
<h1>📋 Заголовок страницы</h1>

<form method="POST" action="{{ url_for('...') }}">
    <!-- Поля формы -->
    <div style="margin-bottom: 20px;">
        <label for="field">Название:</label>
        <input type="text" id="field" name="field" required>
    </div>
    
    <!-- Кнопки -->
    <button type="submit" class="btn btn-success">✅ Сохранить</button>
    <a href="..." class="btn btn-secondary">❌ Отмена</a>
</form>
```

**Характеристики**:
- Label над каждым полем
- Inline стили для spacing
- Required атрибуты для обязательных полей
- Submit кнопка + Cancel ссылка
- Валидация на backend с flash-сообщениями

---

### 3.3 Dashboard Page (Рабочее меню)

**URL**: `/work-menu`  
**Template**: `work_menu.html`  
**Тип**: Dashboard с статистикой и действиями

**Секции**:

1. **Shift Info** (голубая карточка)
   ```html
   <div class="shift-info">
       <h3>📋 Информация о смене</h3>
       <p>Дата, смена, контролёры</p>
   </div>
   ```

2. **Statistics Section** (желтая карточка с grid)
   ```html
   <div class="statistics-section">
       <h3>📊 Статистика смены</h3>
       <div class="stats-grid">
           <div class="stat-card">...</div>
           <div class="stat-card">...</div>
           <div class="stat-card">...</div>
           <div class="stat-card">...</div>
       </div>
   </div>
   ```

3. **Search Section** (серая карточка с формой)
   ```html
   <div class="search-section">
       <h3>🔍 Поиск маршрутной карты</h3>
       <input + buttons>
       <div id="qrReader"></div>
       <div id="cardResult"></div>
   </div>
   ```

4. **Action Buttons**
   ```html
   <a href="/reports" class="btn btn-info">📊 Отчеты</a>
   <a href="/manage-controllers" class="btn btn-secondary">👥 Контролёры</a>
   <button onclick="closeShift()" class="btn btn-danger">🔚 Закрыть смену</button>
   ```

**JavaScript функции**:
- `searchCard()` - Поиск маршрутной карты
- `startQRScan()` / `stopQRScan()` - QR-сканирование
- `updateStatistics()` - Auto-refresh каждые 30 сек
- `closeShift()` - Закрытие смены

---

### 3.4 List/Table Pages (Списки данных)

**Примеры**:
- `/reports` - Список смен
- `/manage-controllers` - Список контролёров

**Структура**:
```html
<h1>📊 Заголовок</h1>

<a href="..." class="btn btn-secondary">⬅️ Назад</a>

<!-- Опционально: Форма добавления -->

<h3>Список элементов</h3>
{% if items %}
<table>
    <thead>
        <tr>
            <th>Колонка 1</th>
            <th>Колонка 2</th>
            <th>Действия</th>
        </tr>
    </thead>
    <tbody>
        {% for item in items %}
        <tr>
            <td>{{ item.field1 }}</td>
            <td>{{ item.field2 }}</td>
            <td>
                <button class="btn btn-warning">Действие</button>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% else %}
<p>Нет данных</p>
{% endif %}
```

**Empty State**:
- Если нет данных → `<p>Нет элементов</p>`
- Может включать ссылку на создание первого элемента

---

### 3.5 CRUD Pages (Create, Read, Update, Delete)

**Пример**: `/manage-controllers`

**Секции**:

1. **Create Section** (серая карточка сверху)
   ```html
   <div style="background: #f8f9fa; padding: 20px;">
       <h3>Добавить контролера</h3>
       <form onsubmit="addController(event)">
           <input + button>
       </form>
   </div>
   ```

2. **List Section** (таблица)
   - Отображение всех элементов
   - Колонка "Действия" с кнопками

3. **JavaScript CRUD operations**
   ```javascript
   async function addController(event) { ... }
   async function toggleController(id) { ... }
   async function deleteController(id) { ... }
   ```

**Паттерн AJAX**:
1. Сбор данных формы
2. FormData или JSON
3. Fetch API request
4. Обработка ответа
5. `location.reload()` для обновления

---

## 4. 🛠️ Технический стек

### Backend

#### Flask Framework
```python
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
```

**Используемые модули**:
- `render_template` - рендеринг Jinja2 шаблонов
- `request` - получение данных форм/JSON
- `jsonify` - создание JSON ответов
- `redirect` / `url_for` - навигация
- `flash` - уведомления
- `session` - хранение состояния

#### Blueprints

**UI Blueprint** (`app/blueprints/ui.py`):
```python
ui_bp = Blueprint('ui', __name__)

@ui_bp.route('/')
def index():
    return render_template('welcome.html')

@ui_bp.route('/create-shift', methods=['GET', 'POST'])
def create_shift_route():
    # ...
```

**API Blueprint** (`app/blueprints/api.py`):
```python
api_bp = Blueprint('api', __name__)

@api_bp.route('/search-card/<card_number>')
def search_card(card_number):
    return jsonify({'success': True, 'card': data})

@api_bp.route('/close-shift', methods=['POST'])
def api_close_shift():
    return jsonify({'success': True})
```

**Регистрация**:
```python
app.register_blueprint(ui_bp, url_prefix='/')
app.register_blueprint(api_bp, url_prefix='/api')
```

---

### Frontend

#### HTML5
- Семантические теги
- Form validation (required, min, max, pattern)
- Date/number inputs
- Accessibility attributes

#### CSS3
**Файл**: `app/static/css/style.css` (259 строк)

**Основные секции**:
1. Base styles (body, container)
2. Flash messages
3. Buttons (все варианты)
4. Forms
5. Info sections (cards)
6. Statistics
7. Tables
8. Welcome screen
9. Responsive (@media)

**CSS Features**:
- Flexbox для layout
- CSS Grid для статистики
- Transitions для анимаций
- @keyframes для сложных анимаций
- @media queries для responsive

#### JavaScript (Vanilla)

**Файл**: `app/static/js/main.js` (46 строк)

**Функции**:
- `closeShift()` - закрытие смены
- `proceedToInput()` - переход к вводу
- Flash message auto-hide (DOMContentLoaded)

**Встроенный JS** (в шаблонах):
- `searchCard()` - work_menu.html
- `startQRScan()` / `stopQRScan()` - work_menu.html
- `updateStatistics()` - work_menu.html
- `addController()` - manage_controllers.html
- `toggleController()` - manage_controllers.html
- `deleteController()` - manage_controllers.html
- `calculateAccepted()` - input_control.html
- Date/shift auto-fill - create_shift.html

**Паттерны**:
```javascript
// Async/await для API запросов
async function someAction() {
    try {
        const response = await fetch('/api/endpoint', {...});
        const data = await response.json();
        if (data.success) {
            // Success handling
        } else {
            // Error handling
        }
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialization code
});

// Element manipulation
element.addEventListener('input', handleInput);
```

---

### External Libraries

#### html5-qrcode
**CDN**: `https://unpkg.com/html5-qrcode`

**Использование**:
```javascript
const html5QrcodeScanner = new Html5Qrcode("qr-reader");

html5QrcodeScanner.start(
    { facingMode: "environment" },
    { fps: 10, qrbox: { width: 250, height: 250 } },
    onScanSuccess,
    onScanFailure
);
```

**Интеграция**: Только на странице `/work-menu`

---

## 5. 🔧 Особенности реализации

### 5.1 Session Management

**Flask Session**:
```python
# При создании смены
session['current_shift_id'] = shift_id

# При проверке активной смены
shift_id = session.get('current_shift_id')

# При закрытии смены
session.pop('current_shift_id', None)
```

**Session Config**:
```python
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
```

**Lifetime**: До закрытия браузера или закрытия смены

---

### 5.2 Flash Messages

**Backend**:
```python
from flask import flash

# Категории
flash('Успешное действие', 'success')
flash('Ошибка операции', 'error')
flash('Информация', 'info')
flash('Предупреждение', 'warning')
```

**Frontend rendering** (base.html):
```jinja2
{% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
        {% for category, message in messages %}
            <div class="flash-message flash-{{ category }}">
                {{ message }}
            </div>
        {% endfor %}
    {% endif %}
{% endwith %}
```

**Auto-hide** (main.js):
```javascript
setTimeout(() => { message.style.opacity = '0'; }, 5000);
```

---

### 5.3 AJAX Requests

**Паттерн**:
```javascript
// POST with FormData
const formData = new FormData();
formData.append('key', value);

const response = await fetch('/api/endpoint', {
    method: 'POST',
    body: formData
});

// POST with JSON
const response = await fetch('/api/endpoint', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ key: value })
});

// GET
const response = await fetch(`/api/endpoint/${param}`);
```

**Response handling**:
```javascript
const data = await response.json();

if (data.success) {
    alert('Успех');
    location.reload();  // или redirect
} else {
    alert('Ошибка: ' + data.error);
}
```

---

### 5.4 Form Validation

**Frontend (HTML5)**:
```html
<input type="text" required>
<input type="number" min="1" max="100">
<input type="text" pattern="^\d{6}$">
```

**Backend (Python)**:
```python
errors = []

if not field:
    errors.append('Поле обязательно')

if errors:
    for error in errors:
        flash(error, 'error')
    return redirect(...)
```

**JavaScript (Real-time)**:
```javascript
input.addEventListener('input', validateField);
```

---

### 5.5 Cyrillic Support

**Database**:
- Таблицы: `Смены`, `Контролёры`, `Записи_контроля`
- Колонки: `имя`, `дата`, `статус`, `активен`
- Encoding: UTF-8

**Python**:
```python
# Все строки - Unicode
имя = "Иванов И.И."
дата = "2024-01-15"
```

**HTML**:
```html
<meta charset="UTF-8">
<html lang="ru">
```

**JavaScript**:
- Все строки поддерживают кириллицу
- Alert messages на русском

---

### 5.6 Error Handling

**Три уровня**:

1. **Frontend validation**:
   - HTML5 required/pattern
   - JavaScript проверки
   - Alert для критических ошибок

2. **Backend validation**:
   - Валидация бизнес-правил
   - Flash messages для ошибок
   - Логирование

3. **Exception handling**:
   ```python
   try:
       operation()
   except Exception as e:
       logger.error(f"Error: {e}")
       flash(f'Ошибка: {str(e)}', 'error')
       return redirect(...)
   ```

---

## 6. 📁 Структура файлов

### Директории

```
app/
├── blueprints/
│   ├── __init__.py
│   ├── ui.py              # UI routes (HTML pages)
│   └── api.py             # API routes (JSON endpoints)
│
├── templates/
│   ├── base.html          # Base layout
│   ├── welcome.html       # Landing page
│   ├── create_shift.html  # Shift creation form
│   ├── work_menu.html     # Dashboard
│   ├── input_control.html # Quality control form
│   ├── manage_controllers.html  # Controllers CRUD
│   └── reports.html       # Reports list
│
├── static/
│   ├── css/
│   │   └── style.css      # All styles
│   └── js/
│       └── main.js        # Common JS functions
│
├── services/
│   ├── shift_service.py
│   ├── database_service.py
│   └── control_service.py
│
├── repositories/
│   ├── shift_repository.py
│   ├── controller_repository.py
│   └── defect_repository.py
│
├── helpers/
│   ├── error_handlers.py
│   ├── validators.py
│   └── logging_config.py
│
└── database.py            # Database connection
```

---

### Mapping: URL → Template → Services

| URL | Template | Blueprint | Services | Description |
|-----|----------|-----------|----------|-------------|
| `/` | `welcome.html` | `ui.index` | `shift_service.get_current_shift` | Главная страница |
| `/create-shift` | `create_shift.html` | `ui.create_shift_route` | `shift_service.create_shift`, `database_service.get_all_controllers` | Создание смены |
| `/work-menu` | `work_menu.html` | `ui.work_menu` | `shift_service.get_current_shift`, `shift_service.get_shift_statistics` | Рабочее меню |
| `/input-control` | `input_control.html` | `ui.input_control` | `database_service.search_route_card_in_foundry`, `database_service.get_all_defect_types` | Ввод контроля |
| `/save-control` | - (redirect) | `ui.save_control` | `control_service.save_control_record` | Сохранение контроля |
| `/manage-controllers` | `manage_controllers.html` | `ui.manage_controllers` | `database_service.get_all_controllers` | Управление контролёрами |
| `/reports` | `reports.html` | `ui.reports` | `shift_service.get_all_shifts` | Отчёты |
| `/api/search-card/<id>` | JSON | `api.search_card` | `database_service.search_route_card_in_foundry` | Поиск карты |
| `/api/close-shift` | JSON | `api.api_close_shift` | `shift_service.close_shift` | Закрытие смены |
| `/api/add-controller` | JSON | `api.add_controller` | `database_service.add_controller` | Добавить контролёра |
| `/api/toggle-controller` | JSON | `api.toggle_controller` | `database_service.toggle_controller` | Активация/деактивация |
| `/api/delete-controller` | JSON | `api.delete_controller` | `database_service.delete_controller` | Удалить контролёра |
| `/api/shifts/current` | JSON | `api.get_current_shift_api` | `shift_service.get_current_shift`, `shift_service.get_shift_statistics` | Текущая смена + статистика |

---

## 🎯 Архитектурные принципы

### 1. Separation of Concerns
- **Templates**: Только отображение
- **Blueprints**: Обработка HTTP запросов
- **Services**: Бизнес-логика
- **Repositories**: Доступ к данным

### 2. DRY (Don't Repeat Yourself)
- Базовый шаблон для всех страниц
- Общие CSS классы
- Переиспользуемые JS функции
- Service layer для дублирующейся логики

### 3. Convention over Configuration
- Стандартная структура Flask
- Blueprints для модульности
- Static/templates в стандартных местах

### 4. Progressive Enhancement
- Базовая функциональность без JS
- AJAX для улучшенного UX
- Fallback для старых браузеров

### 5. Mobile-First Responsive
- Base styles для desktop
- @media queries для адаптации
- Touch-friendly элементы

---

*Структура интерфейса обновлена: 2024*
