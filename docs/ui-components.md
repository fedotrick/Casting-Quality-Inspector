# 📐 UI Компоненты - Документация

> **Полное описание всех переиспользуемых компонентов интерфейса**

---

## 📋 Содержание

1. [Формы](#формы)
2. [Кнопки](#кнопки)
3. [Таблицы](#таблицы)
4. [Карточки информации](#карточки-информации)
5. [Flash-сообщения](#flash-сообщения)
6. [QR-сканер](#qr-сканер)
7. [Навигация](#навигация)
8. [Статистика](#статистика)

---

## 1. 📝 Формы

### 1.1 Text Input

**Назначение**: Ввод текстовых данных

**HTML структура**:
```html
<div style="margin-bottom: 20px;">
    <label for="field_name">Название поля:</label>
    <input type="text" id="field_name" name="field_name" required style="width: 100%;">
</div>
```

**CSS классы**:
- Используется inline стиль `width: 100%`
- Базовые стили из `style.css`: `input { padding: 10px; border: 1px solid #ddd; ... }`

**Состояния**:
- **Normal**: серая рамка (#ddd)
- **Focus**: синяя рамка (#007bff) с тенью
- **Error**: отображается через flash-сообщение

**Пример использования**:
```html
<!-- Ввод номера маршрутной карты -->
<input type="text" id="cardNumber" placeholder="000295" maxlength="6" style="flex: 1;">
```

---

### 1.2 Number Input

**Назначение**: Ввод числовых значений (количество деталей, дефектов)

**HTML структура**:
```html
<div style="margin-bottom: 20px;">
    <label for="total_cast">Всего отлито:</label>
    <input type="number" id="total_cast" name="total_cast" required min="1" style="width: 100%;">
</div>
```

**Особенности**:
- Атрибут `min` для валидации минимального значения
- Атрибут `required` для обязательных полей
- Автоматический расчет в форме ввода контроля

**JavaScript интерактивность**:
```javascript
// Auto-calculate accepted based on defects
totalCastInput.addEventListener('input', calculateAccepted);
```

---

### 1.3 Date Input

**Назначение**: Выбор даты смены

**HTML структура**:
```html
<input type="date" id="date" name="date" required style="width: 100%;">
```

**JavaScript автозаполнение**:
```javascript
// Set today's date by default
const dateInput = document.getElementById('date');
const today = new Date().toISOString().split('T')[0];
dateInput.value = today;
```

**Особенности**:
- Автоматически устанавливается текущая дата
- Валидация на backend (не в будущем)

---

### 1.4 Select Dropdown

**Назначение**: Выбор из предопределенных вариантов

**HTML структура**:
```html
<select id="shift_number" name="shift_number" required style="width: 100%;">
    <option value="">Выберите смену</option>
    <option value="1">Смена 1 (07:00 - 19:00)</option>
    <option value="2">Смена 2 (19:00 - 07:00)</option>
</select>
```

**JavaScript автовыбор**:
```javascript
// Auto-select shift based on current time
const currentHour = new Date().getHours();
if (currentHour >= 7 && currentHour < 19) {
    shiftSelect.value = '1';
} else {
    shiftSelect.value = '2';
}
```

**Использование**:
- Выбор смены (1 или 2)
- Выбор контролёра из списка
- Категории дефектов

---

### 1.5 Checkbox

**Назначение**: Множественный выбор (контролёры)

**HTML структура**:
```html
<div style="margin: 5px 0;">
    <input type="checkbox" id="controller_{{ controller.id }}" name="controllers" value="{{ controller.имя }}">
    <label for="controller_{{ controller.id }}" style="display: inline; font-weight: normal;">
        {{ controller.имя }}
    </label>
</div>
```

**Особенности**:
- Inline label (не блочный)
- Используется для выбора контролёров при создании смены
- Валидация: хотя бы один должен быть выбран

---

### 1.6 Textarea

**Назначение**: Многострочный текст (заметки)

**HTML структура**:
```html
<div style="margin-bottom: 20px;">
    <label for="notes">Заметки (необязательно):</label>
    <textarea id="notes" name="notes" rows="3" style="width: 100%;"></textarea>
</div>
```

**Особенности**:
- Необязательное поле
- 3 строки высоты по умолчанию

---

### 1.7 Submit Button

**HTML структура**:
```html
<button type="submit" class="btn btn-success">✅ Создать смену</button>
```

**Варианты**:
- `btn btn-success` - зеленая (создать, сохранить)
- `btn` - синяя (основное действие)
- `btn btn-danger` - красная (удалить, закрыть)
- `btn btn-secondary` - серая (отмена, назад)

---

## 2. 🎯 Кнопки

### 2.1 Primary Button

**CSS класс**: `.btn`

**Стили**:
```css
.btn {
    padding: 10px 20px;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    margin: 5px;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    transition: all 0.3s ease;
}

.btn:hover {
    background: #0056b3;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
```

**Использование**:
```html
<button class="btn">🔍 Найти карту</button>
<a href="/reports" class="btn">📊 Отчеты</a>
```

**Анимация**:
- Hover: поднимается на 2px, меняет цвет, добавляется тень
- Transition: 0.3s ease для плавности

---

### 2.2 Button Variants

#### Success Button
```html
<button class="btn btn-success">✅ Сохранить</button>
```
- Цвет: #28a745 (зеленый)
- Hover: #218838
- Использование: подтверждающие действия

#### Danger Button
```html
<button class="btn btn-danger">🔚 Закрыть смену</button>
```
- Цвет: #dc3545 (красный)
- Hover: #c82333
- Использование: удаление, закрытие

#### Secondary Button
```html
<a href="/" class="btn btn-secondary">⬅️ Назад</a>
```
- Цвет: #6c757d (серый)
- Hover: #5a6268
- Использование: отмена, возврат

#### Info Button
```html
<button class="btn btn-info">📱 Сканировать QR</button>
```
- Цвет: #17a2b8 (голубой)
- Hover: #138496
- Использование: дополнительные действия

#### Warning Button
```html
<button class="btn btn-warning">Деактивировать</button>
```
- Цвет: #ffc107 (желтый)
- Hover: #e0a800
- Использование: предупреждающие действия

---

### 2.3 Responsive Buttons

**Mobile view** (< 768px):
```css
@media (max-width: 768px) {
    .btn {
        display: block;
        width: 100%;
        margin: 10px 0;
    }
}
```

На мобильных устройствах кнопки растягиваются на всю ширину.

---

## 3. 📊 Таблицы

### 3.1 Data Table

**Назначение**: Отображение списков данных (смены, контролёры)

**HTML структура**:
```html
<table>
    <thead>
        <tr>
            <th>Дата</th>
            <th>Смена</th>
            <th>Контролеры</th>
            <th>Время</th>
            <th>Статус</th>
        </tr>
    </thead>
    <tbody>
        {% for shift in shifts %}
        <tr>
            <td>{{ shift.date }}</td>
            <td>{{ shift.shift_number }}</td>
            <td>{{ shift.controllers|join(', ') }}</td>
            <td>{{ shift.start_time }} - {{ shift.end_time or 'активна' }}</td>
            <td>{{ shift.status }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

**CSS стили**:
```css
table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
}

th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

th {
    background-color: #007bff;
    color: white;
}

tr:hover {
    background-color: #f5f5f5;
}
```

**Особенности**:
- Синяя шапка таблицы
- Hover эффект на строках
- Разделители между строками

---

### 3.2 Table with Actions

**Пример**: Управление контролёрами

```html
<table>
    <thead>
        <tr>
            <th>Имя</th>
            <th>Статус</th>
            <th>Действия</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Иванов И.И.</td>
            <td>Активен</td>
            <td>
                <button class="btn btn-warning" onclick="toggleController(1)">
                    Деактивировать
                </button>
                <button class="btn btn-danger" onclick="deleteController(1)">
                    Удалить
                </button>
            </td>
        </tr>
    </tbody>
</table>
```

**JavaScript обработчики**:
```javascript
async function toggleController(id) {
    const response = await fetch('/api/toggle-controller', {
        method: 'POST',
        body: formData
    });
    // ...
}
```

---

## 4. 🗂️ Карточки информации

### 4.1 Shift Info Card

**Назначение**: Отображение информации о текущей смене

**HTML структура**:
```html
<div class="shift-info">
    <h3>📋 Информация о смене</h3>
    <p><strong>Дата:</strong> {{ shift.date }}</p>
    <p><strong>Смена:</strong> {{ shift.shift_number }}</p>
    <p><strong>Контролеры:</strong> {{ shift.controllers|join(', ') }}</p>
</div>
```

**CSS стили**:
```css
.shift-info {
    background: #e3f2fd;  /* Светло-синий */
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 20px;
}
```

---

### 4.2 Card Info (Route Card)

**Назначение**: Информация о маршрутной карте

**HTML структура**:
```html
<div class="card-info">
    <h4>✅ Маршрутная карта найдена</h4>
    <p><strong>Номер:</strong> 000295</p>
    <p><strong>Учетный номер:</strong> 12345</p>
    <p><strong>Наименование отливки:</strong> Деталь А</p>
    <button class="btn" onclick="proceedToInput('000295')">
        ➡️ Перейти к вводу контроля
    </button>
</div>
```

**CSS стили**:
```css
.card-info {
    background: #d4edda;  /* Светло-зеленый */
    padding: 15px;
    border-radius: 5px;
    margin: 10px 0;
}
```

---

### 4.3 Search Section

**Назначение**: Секция поиска маршрутных карт

**HTML структура**:
```html
<div class="search-section">
    <h3>🔍 Поиск маршрутной карты</h3>
    <div style="display: flex; gap: 10px;">
        <input type="text" id="cardNumber" placeholder="000295" maxlength="6" style="flex: 1;">
        <button class="btn" onclick="searchCard()">🔍 Найти карту</button>
        <button class="btn btn-info" onclick="startQRScan()">📱 Сканировать QR</button>
    </div>
    <div id="qrReader" style="display: none;"></div>
    <div id="cardResult"></div>
</div>
```

**CSS стили**:
```css
.search-section {
    background: #f8f9fa;  /* Светло-серый */
    padding: 20px;
    border-radius: 10px;
    margin: 20px 0;
}
```

---

## 5. 💬 Flash-сообщения

### 5.1 Структура

**Назначение**: Уведомления пользователя о результатах действий

**HTML структура** (в base.html):
```html
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
```

---

### 5.2 Типы сообщений

#### Success
```css
.flash-success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}
```
**Использование**: Успешное выполнение действия
```python
flash('Смена успешно создана!', 'success')
```

#### Error
```css
.flash-error {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}
```
**Использование**: Ошибки
```python
flash('Ошибка при создании смены', 'error')
```

#### Info
```css
.flash-info {
    background-color: #d1ecf1;
    color: #0c5460;
    border: 1px solid #bee5eb;
}
```
**Использование**: Информационные сообщения
```python
flash('Нет активной смены', 'info')
```

#### Warning
```css
.flash-warning {
    background-color: #fff3cd;
    color: #856404;
    border: 1px solid #ffeeba;
}
```
**Использование**: Предупреждения
```python
flash('Маршрутная карта уже обработана', 'warning')
```

---

### 5.3 Auto-hide функция

**JavaScript** (в main.js):
```javascript
// Flash message auto-hide
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 500);
        }, 5000);  // Скрывается через 5 секунд
    });
});
```

**Особенности**:
- Автоматически скрывается через 5 секунд
- Плавное исчезновение (opacity transition)
- Полное удаление из DOM через 500ms после начала fade

---

## 6. 📱 QR-сканер

### 6.1 Компонент

**Назначение**: Сканирование QR-кодов маршрутных карт через камеру браузера

**Библиотека**: html5-qrcode
```html
<script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
```

---

### 6.2 HTML структура

```html
<button class="btn btn-info" onclick="startQRScan()">📱 Сканировать QR</button>
<div id="qrReader" style="display: none; margin: 10px 0;"></div>
```

---

### 6.3 JavaScript реализация

**Запуск сканера**:
```javascript
function startQRScan() {
    const qrReaderDiv = document.getElementById('qrReader');
    
    if (html5QrcodeScanner) {
        // Toggle - если уже запущен, остановить
        html5QrcodeScanner.clear();
        html5QrcodeScanner = null;
        qrReaderDiv.style.display = 'none';
        return;
    }
    
    // Показать контейнер
    qrReaderDiv.style.display = 'block';
    qrReaderDiv.innerHTML = '<div id="qr-reader" style="width: 100%;"></div>';
    
    // Инициализировать сканер
    html5QrcodeScanner = new Html5Qrcode("qr-reader");
    
    const config = {
        fps: 10,
        qrbox: { width: 250, height: 250 }
    };
    
    html5QrcodeScanner.start(
        { facingMode: "environment" },  // Задняя камера
        config,
        (decodedText, decodedResult) => {
            // Успешное сканирование
            document.getElementById('cardNumber').value = decodedText;
            stopQRScan();
            searchCard();  // Автоматический поиск
        },
        (errorMessage) => {
            // Ошибка сканирования (игнорируется)
        }
    ).catch(err => {
        alert('Не удалось запустить камеру. Проверьте разрешения.');
        qrReaderDiv.style.display = 'none';
    });
}
```

**Остановка сканера**:
```javascript
function stopQRScan() {
    if (html5QrcodeScanner) {
        html5QrcodeScanner.stop().then(() => {
            html5QrcodeScanner.clear();
            html5QrcodeScanner = null;
            document.getElementById('qrReader').style.display = 'none';
        });
    }
}
```

---

### 6.4 UX флоу

1. Пользователь нажимает "Сканировать QR"
2. Браузер запрашивает разрешение на камеру
3. Появляется видео с наложением рамки сканирования
4. При обнаружении QR-кода:
   - Код автоматически вставляется в поле ввода
   - Сканер закрывается
   - Выполняется автоматический поиск карты
5. Результат отображается в `cardResult` div

---

## 7. 🧭 Навигация

### 7.1 Навигационные кнопки

**Кнопка "Назад"**:
```html
<a href="{{ url_for('ui.work_menu') }}" class="btn btn-secondary">⬅️ Назад</a>
```

**Кнопка "Отмена"**:
```html
<a href="{{ url_for('ui.index') }}" class="btn btn-secondary">❌ Отмена</a>
```

---

### 7.2 Главные переходы

**Welcome → Create Shift**:
```html
<a href="/create-shift" class="start-btn">🚀 Начать работу</a>
```

**Work Menu навигация**:
```html
<a href="/reports" class="btn btn-info">📊 Отчеты</a>
<a href="/manage-controllers" class="btn btn-secondary">👥 Контролеры</a>
```

---

### 7.3 Специальная кнопка Start

**CSS** (welcome.html):
```css
.start-btn {
    background: linear-gradient(45deg, #ff6b35, #f7931e);
    color: white;
    padding: 15px 40px;
    font-size: 1.1em;
    border-radius: 50px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    animation: btnPulse 2s ease-in-out infinite;
}

@keyframes btnPulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}
```

**Особенности**:
- Градиентный фон
- Пульсирующая анимация
- Увеличенный размер
- Привлекает внимание на главной странице

---

## 8. 📊 Статистика

### 8.1 Statistics Section

**HTML структура**:
```html
<div class="statistics-section">
    <h3>📊 Статистика смены</h3>
    <div class="stats-grid">
        <div class="stat-card">
            <h4>📝 Записей</h4>
            <p style="font-size: 24px; font-weight: bold; color: #007bff;">15</p>
        </div>
        <div class="stat-card">
            <h4>🏭 Отлито</h4>
            <p style="font-size: 24px; font-weight: bold; color: #28a745;">450</p>
        </div>
        <div class="stat-card">
            <h4>✅ Принято</h4>
            <p style="font-size: 24px; font-weight: bold; color: #17a2b8;">420</p>
        </div>
        <div class="stat-card">
            <h4>📈 Качество</h4>
            <p style="font-size: 24px; font-weight: bold; color: #ffc107;">93.3%</p>
        </div>
    </div>
</div>
```

---

### 8.2 CSS Grid Layout

```css
.statistics-section {
    background: #fff3cd;  /* Светло-желтый */
    padding: 20px;
    border-radius: 10px;
    margin: 20px 0;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-top: 15px;
}

.stat-card {
    background: white;
    padding: 15px;
    border-radius: 8px;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
```

**Особенности**:
- Адаптивная сетка (auto-fit)
- Минимальная ширина карточки: 200px
- Центрированный текст
- Цветовое кодирование цифр

---

### 8.3 Real-time обновление

**JavaScript** (work_menu.html):
```javascript
// Auto-update statistics every 30 seconds
async function updateStatistics() {
    try {
        const response = await fetch('/api/shifts/current');
        const data = await response.json();
        if (data.success && data.shift.statistics) {
            const stats = data.shift.statistics;
            const statCards = document.querySelectorAll('.stat-card p');
            statCards[0].textContent = stats.total_records || 0;
            statCards[1].textContent = stats.total_cast || 0;
            statCards[2].textContent = stats.total_accepted || 0;
            statCards[3].textContent = (stats.avg_quality || 0) + '%';
        }
    } catch (error) {
        console.log('Ошибка обновления статистики:', error);
    }
}

setInterval(updateStatistics, 30000);  // Каждые 30 секунд
```

---

## 🎨 Общие принципы использования

### 1. Consistency (Единообразие)
- Используйте существующие CSS классы
- Следуйте паттерну HTML структур
- Сохраняйте spacing (margin-bottom: 20px для форм)

### 2. Accessibility
- Всегда используйте `<label for="...">` с inputs
- Добавляйте `required` для обязательных полей
- Используйте семантические HTML теги

### 3. Responsive
- Используйте `width: 100%` для form inputs
- Проверяйте работу на мобильных (< 768px)
- Тестируйте с разными размерами экрана

### 4. JavaScript
- Используйте `async/await` для API запросов
- Обрабатывайте ошибки через `try/catch`
- Добавляйте `alert()` для критических ошибок

### 5. Эмодзи иконки
- Используются для визуального улучшения UX
- Не обязательны, но рекомендуются
- Примеры: 📋 📝 ✅ ❌ 🔍 📊 👥 🚀

---

*Документация компонентов обновлена: 2024*
