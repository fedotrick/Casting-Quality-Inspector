# 🎨 Style Guide - Руководство по стилю

> **Полное руководство по визуальному стилю системы Casting Quality Inspector**

---

## 📋 Содержание

1. [Цветовая палитра](#цветовая-палитра)
2. [Типографика](#типографика)
3. [Spacing система](#spacing-система)
4. [Кнопки](#кнопки)
5. [Формы](#формы)
6. [Таблицы](#таблицы)
7. [Карточки](#карточки)
8. [Иконки и эмодзи](#иконки-и-эмодзи)
9. [Анимации](#анимации)
10. [Responsive breakpoints](#responsive-breakpoints)

---

## 1. 🎨 Цветовая палитра

### Основные цвета (Primary Colors)

#### Primary Blue
```css
Color: #007bff
RGB: (0, 123, 255)
Hex: #007bff
```
**Использование**: Основные кнопки, заголовки таблиц, акцентные элементы

**Hover состояние**:
```css
Color: #0056b3
RGB: (0, 86, 179)
```

**Примеры**:
- Кнопки `.btn`
- Заголовки таблиц `<th>`
- Фокус на inputs

---

#### Secondary Gray
```css
Color: #6c757d
RGB: (108, 117, 125)
Hex: #6c757d
```
**Использование**: Второстепенные кнопки, неактивные элементы

**Hover состояние**:
```css
Color: #5a6268
RGB: (90, 98, 104)
```

**Примеры**:
- Кнопки "Назад", "Отмена"
- Неактивные состояния

---

### Цвета состояний (State Colors)

#### Success Green
```css
Color: #28a745
RGB: (40, 167, 69)
Hex: #28a745
```
**Использование**: Успешные операции, подтверждения

**Hover**: `#218838`

**Примеры**:
- Flash-сообщения успеха
- Кнопки "Сохранить", "Создать"
- Карточки с позитивной информацией

**Фоновые оттенки**:
```css
Background: #d4edda (light green)
Border: #c3e6cb
Text: #155724 (dark green)
```

---

#### Danger Red
```css
Color: #dc3545
RGB: (220, 53, 69)
Hex: #dc3545
```
**Использование**: Ошибки, удаление, критические действия

**Hover**: `#c82333`

**Примеры**:
- Flash-сообщения ошибок
- Кнопки "Удалить", "Закрыть"
- Предупреждения

**Фоновые оттенки**:
```css
Background: #f8d7da (light red)
Border: #f5c6cb
Text: #721c24 (dark red)
```

---

#### Info Cyan
```css
Color: #17a2b8
RGB: (23, 162, 184)
Hex: #17a2b8
```
**Использование**: Информационные элементы, дополнительные действия

**Hover**: `#138496`

**Примеры**:
- Flash-сообщения информации
- Кнопки "Отчёты", "QR-сканирование"
- Информационные карточки

**Фоновые оттенки**:
```css
Background: #d1ecf1 (light cyan)
Border: #bee5eb
Text: #0c5460 (dark cyan)
```

---

#### Warning Yellow
```css
Color: #ffc107
RGB: (255, 193, 7)
Hex: #ffc107
```
**Использование**: Предупреждения, изменения статуса

**Hover**: `#e0a800`

**Примеры**:
- Flash-сообщения предупреждений
- Кнопки "Деактивировать"
- Предупреждающие карточки

**Фоновые оттенки**:
```css
Background: #fff3cd (light yellow)
Border: #ffeeba
Text: #856404 (dark brown)
```

---

### Нейтральные цвета (Neutral Colors)

#### Text Colors
```css
/* Основной текст */
Primary Text: #333
RGB: (51, 51, 51)

/* Белый текст (на кнопках) */
White Text: #ffffff
RGB: (255, 255, 255)
```

#### Background Colors
```css
/* Основной фон страницы */
Page Background: #f5f5f5
RGB: (245, 245, 245)

/* Фон контейнера */
Container Background: #ffffff (white)

/* Фон секций */
Section Background: #f8f9fa
RGB: (248, 249, 250)

/* Фон информационных карточек */
Shift Info: #e3f2fd (light blue)
Card Info: #d4edda (light green)
Statistics: #fff3cd (light yellow)
```

#### Border Colors
```css
/* Границы inputs, таблиц */
Default Border: #ddd
RGB: (221, 221, 221)

/* Активная граница (focus) */
Active Border: #007bff
```

---

### Градиенты

#### Welcome Screen Gradient
```css
background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
```
**Использование**: Фон главной страницы

#### Start Button Gradient
```css
background: linear-gradient(45deg, #ff6b35, #f7931e);
```
**Использование**: Кнопка "Начать работу" на welcome screen

---

## 2. 📝 Типографика

### Шрифт

**Семейство**:
```css
font-family: 'Arial', sans-serif;
```

**Обоснование**:
- Универсальная читаемость
- Хорошая поддержка кириллицы
- Системный шрифт (быстрая загрузка)

---

### Заголовки

#### H1
```css
h1 {
    font-size: 2em;        /* 32px при base 16px */
    font-weight: bold;
    margin-bottom: 20px;
}
```
**Использование**: Главный заголовок страницы  
**Пример**: `<h1>📋 Создание новой смены</h1>`

#### H2
```css
h2 {
    font-size: 1.5em;      /* 24px */
    font-weight: bold;
    margin-bottom: 15px;
}
```
**Использование**: Заголовки секций  
**Пример**: Не используется в текущей версии

#### H3
```css
h3 {
    font-size: 1.17em;     /* ~19px */
    font-weight: bold;
    margin-bottom: 10px;
}
```
**Использование**: Заголовки подсекций  
**Пример**: `<h3>📊 Статистика смены</h3>`

#### H4
```css
h4 {
    font-size: 1em;        /* 16px */
    font-weight: bold;
    margin-bottom: 8px;
}
```
**Использование**: Заголовки карточек статистики  
**Пример**: `<h4>🏭 Отлито</h4>`

---

### Текст

#### Body Text
```css
body {
    font-size: 16px;
    line-height: 1.5;
    color: #333;
}
```

#### Paragraph
```css
p {
    margin-bottom: 10px;
    line-height: 1.6;
}
```

#### Strong (Bold)
```css
strong {
    font-weight: bold;
}
```
**Использование**: `<p><strong>Дата:</strong> 2024-01-15</p>`

---

### Labels

```css
label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
    font-size: 16px;
}
```

**Для inline labels** (checkboxes):
```css
label[style*="display: inline"] {
    font-weight: normal;
}
```

---

### Размеры шрифта в компонентах

#### Кнопки
```css
.btn {
    font-size: 16px;
}

.start-btn {
    font-size: 1.1em;  /* 17.6px */
}
```

#### Статистика
```css
.stat-card p {
    font-size: 24px;
    font-weight: bold;
}
```

#### Welcome Screen
```css
.title {
    font-size: 2.5em;  /* 40px */
    font-weight: bold;
}

.subtitle {
    font-size: 1.2em;  /* 19.2px */
}
```

---

### Специальные эффекты текста

#### Text Shadow (Welcome Screen)
```css
.title {
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}
```

---

## 3. 📏 Spacing система

### Принцип: Кратность 5px

Все отступы базируются на значениях, кратных 5px:
- 5px, 10px, 15px, 20px, 30px, 40px, 50px

---

### Margins

#### Container
```css
.container {
    margin: 0 auto;      /* Центрирование */
    margin-top: 20px;
    margin-bottom: 20px;
}
```

#### Form Fields
```css
div {  /* Контейнер поля формы */
    margin-bottom: 20px;
}
```

#### Labels
```css
label {
    margin-bottom: 5px;
}
```

#### Buttons
```css
.btn {
    margin: 5px;
}
```

#### Sections
```css
.shift-info, .statistics-section, .search-section {
    margin: 20px 0;
}

.stats-grid {
    margin-top: 15px;
}
```

---

### Paddings

#### Container
```css
.container {
    padding: 30px;
}

/* Mobile */
@media (max-width: 768px) {
    .container {
        padding: 15px;
    }
}
```

#### Flash Messages
```css
.flash-message {
    padding: 15px;
}
```

#### Buttons
```css
.btn {
    padding: 10px 20px;
}

.start-btn {
    padding: 15px 40px;
}
```

#### Info Sections
```css
.shift-info {
    padding: 20px;
}

.card-info {
    padding: 15px;
}

.search-section {
    padding: 20px;
}

.statistics-section {
    padding: 20px;
}
```

#### Tables
```css
th, td {
    padding: 12px;
}
```

#### Stat Cards
```css
.stat-card {
    padding: 15px;
}
```

---

### Gaps

#### Stats Grid
```css
.stats-grid {
    gap: 15px;
}
```

#### Search Section Flexbox
```css
div[style*="display: flex"] {
    gap: 10px;  /* Inline style */
}
```

---

## 4. 🔘 Кнопки

### Base Button

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

**Анатомия**:
- **Padding**: 10px (верх/низ) × 20px (лево/право)
- **Border-radius**: 5px (слегка скругленные углы)
- **Transition**: 0.3s ease (плавная анимация)
- **Hover**: Поднимается на 2px, меняет цвет, добавляется тень

---

### Button Variants

#### Primary (.btn)
- **Color**: #007bff → #0056b3
- **Text**: белый
- **Use**: Основное действие

#### Success (.btn .btn-success)
- **Color**: #28a745 → #218838
- **Text**: белый
- **Use**: Подтверждение, сохранение

#### Danger (.btn .btn-danger)
- **Color**: #dc3545 → #c82333
- **Text**: белый
- **Use**: Удаление, закрытие

#### Secondary (.btn .btn-secondary)
- **Color**: #6c757d → #5a6268
- **Text**: белый
- **Use**: Отмена, возврат

#### Info (.btn .btn-info)
- **Color**: #17a2b8 → #138496
- **Text**: белый
- **Use**: Информация, дополнительные действия

#### Warning (.btn .btn-warning)
- **Color**: #ffc107 → #e0a800
- **Text**: #333 (темный)
- **Use**: Предупреждения, изменения

---

### Special Buttons

#### Start Button (Welcome Screen)
```css
.start-btn {
    background: linear-gradient(45deg, #ff6b35, #f7931e);
    color: white;
    border: none;
    padding: 15px 40px;
    font-size: 1.1em;
    border-radius: 50px;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    transition: all 0.3s ease;
    animation: btnPulse 2s ease-in-out infinite;
}

.start-btn:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.3);
}

@keyframes btnPulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}
```

**Особенности**:
- Градиентный фон
- Скругленные края (50px = pill shape)
- Пульсирующая анимация
- Увеличенный padding

---

### Button States

#### Normal
- Default стили

#### Hover
```css
:hover {
    background: <darker color>;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
```

#### Active
- Не определено (используется браузерный default)

#### Disabled
- Не определено в текущей версии
- **Рекомендация**:
```css
.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
```

---

### Responsive Buttons

**Mobile** (< 768px):
```css
@media (max-width: 768px) {
    .btn {
        display: block;
        width: 100%;
        margin: 10px 0;
    }
}
```

На мобильных устройствах кнопки:
- Занимают 100% ширины
- Расположены вертикально
- Увеличенный margin для touch

---

### Button Usage

```html
<!-- Primary action -->
<button class="btn">🔍 Найти карту</button>

<!-- Success action -->
<button type="submit" class="btn btn-success">✅ Сохранить</button>

<!-- Danger action -->
<button class="btn btn-danger" onclick="deleteController()">Удалить</button>

<!-- Navigation -->
<a href="/reports" class="btn btn-info">📊 Отчеты</a>
<a href="/" class="btn btn-secondary">⬅️ Назад</a>
```

**Примечание**: Используйте `<button>` для действий, `<a class="btn">` для навигации.

---

## 5. 📝 Формы

### Input Fields

#### Base Input Style
```css
input, select, textarea {
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-size: 16px;
}
```

#### Focus State
```css
input:focus, select:focus, textarea:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 5px rgba(0,123,255,0.3);
}
```

**Эффект**: Синяя рамка + свечение при фокусе

---

### Input Types

#### Text Input
```html
<input type="text" id="field" name="field" required style="width: 100%;">
```

**Inline styles**:
- `width: 100%` - на всю ширину контейнера

#### Number Input
```html
<input type="number" id="total_cast" name="total_cast" required min="1" style="width: 100%;">
```

**Attributes**:
- `min` - минимальное значение
- `max` - максимальное значение (если нужно)
- `step` - шаг изменения (default: 1)

#### Date Input
```html
<input type="date" id="date" name="date" required style="width: 100%;">
```

**JavaScript**: Автозаполнение текущей даты

#### Select Dropdown
```html
<select id="shift_number" name="shift_number" required style="width: 100%;">
    <option value="">Выберите смену</option>
    <option value="1">Смена 1 (07:00 - 19:00)</option>
    <option value="2">Смена 2 (19:00 - 07:00)</option>
</select>
```

**Первый option**: Placeholder с пустым value

#### Textarea
```html
<textarea id="notes" name="notes" rows="3" style="width: 100%;"></textarea>
```

**Attributes**:
- `rows` - количество видимых строк

#### Checkbox
```html
<input type="checkbox" id="controller_1" name="controllers" value="Иванов">
<label for="controller_1" style="display: inline; font-weight: normal;">Иванов И.И.</label>
```

**Особенность**: Inline label с нормальным весом шрифта

---

### Form Structure

```html
<form method="POST" action="{{ url_for('...') }}">
    <div style="margin-bottom: 20px;">
        <label for="field_name">Название поля:</label>
        <input type="text" id="field_name" name="field_name" required style="width: 100%;">
    </div>
    
    <button type="submit" class="btn btn-success">✅ Сохранить</button>
    <a href="..." class="btn btn-secondary">❌ Отмена</a>
</form>
```

**Паттерн**:
1. `<div>` контейнер с `margin-bottom: 20px`
2. `<label>` с атрибутом `for`
3. `<input>` с `id`, `name`, inline style
4. Submit button + Cancel link

---

### Validation Styles

**HTML5 validation**:
- `required` - обязательное поле
- `min`, `max` - диапазон чисел
- `pattern` - регулярное выражение
- `maxlength` - максимальная длина

**JavaScript validation**:
- Real-time проверка
- Auto-calculate (например, принято = отлито - дефекты)

**Backend validation**:
- Flash messages для ошибок
- Красные уведомления

---

## 6. 📊 Таблицы

### Base Table Style

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

---

### Table Structure

```html
<table>
    <thead>
        <tr>
            <th>Колонка 1</th>
            <th>Колонка 2</th>
            <th>Действия</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Данные 1</td>
            <td>Данные 2</td>
            <td>
                <button class="btn btn-warning">Действие</button>
            </td>
        </tr>
    </tbody>
</table>
```

---

### Table Features

#### Header (thead)
- **Background**: #007bff (синий)
- **Text**: белый
- **Bold**: да (браузерный default)

#### Rows (tr)
- **Border-bottom**: 1px solid #ddd
- **Hover**: фон меняется на #f5f5f5

#### Cells (td)
- **Padding**: 12px
- **Align**: left
- **Vertical-align**: middle (браузерный default)

---

### Table with Actions

**Последняя колонка** "Действия":
```html
<td>
    <button class="btn btn-warning" onclick="action1()">Изменить</button>
    <button class="btn btn-danger" onclick="action2()">Удалить</button>
</td>
```

**Inline buttons**: Кнопки расположены горизонтально, `margin: 5px` разделяет их.

---

### Empty State

```html
{% if items %}
<table>...</table>
{% else %}
<p>Нет данных</p>
{% endif %}
```

---

## 7. 🗂️ Карточки

### Shift Info Card

```css
.shift-info {
    background: #e3f2fd;  /* Light blue */
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 20px;
}
```

**Цвет**: Голубой (ассоциируется с информацией о смене)

---

### Card Info (Route Card)

```css
.card-info {
    background: #d4edda;  /* Light green */
    padding: 15px;
    border-radius: 5px;
    margin: 10px 0;
}
```

**Цвет**: Зеленый (успешный поиск карты)

---

### Search Section

```css
.search-section {
    background: #f8f9fa;  /* Light gray */
    padding: 20px;
    border-radius: 10px;
    margin: 20px 0;
}
```

**Цвет**: Серый (нейтральная секция)

---

### Statistics Section

```css
.statistics-section {
    background: #fff3cd;  /* Light yellow */
    padding: 20px;
    border-radius: 10px;
    margin: 20px 0;
}
```

**Цвет**: Желтый (привлечение внимания к статистике)

---

### Stat Card

```css
.stat-card {
    background: white;
    padding: 15px;
    border-radius: 8px;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
```

**Особенности**:
- Белый фон (контраст с желтым фоном секции)
- Центрированный текст
- Легкая тень для глубины
- Меньший border-radius (8px vs 10px)

---

### Card Usage

**Информация**:
```html
<div class="shift-info">
    <h3>📋 Информация о смене</h3>
    <p><strong>Дата:</strong> 2024-01-15</p>
</div>
```

**Поиск результат**:
```html
<div class="card-info">
    <h4>✅ Маршрутная карта найдена</h4>
    <p>Детали...</p>
</div>
```

**Секция действий**:
```html
<div class="search-section">
    <h3>🔍 Поиск</h3>
    <input...>
</div>
```

---

## 8. 🎯 Иконки и эмодзи

### Эмодзи как иконки

**Принцип**: Вместо иконочных шрифтов используются эмодзи для простоты и универсальности.

---

### Используемые эмодзи

| Эмодзи | Unicode | Использование |
|--------|---------|---------------|
| 🏭 | U+1F3ED | Логотип, производство |
| 📋 | U+1F4CB | Информация о смене |
| 📝 | U+1F4DD | Ввод данных, записи |
| ✅ | U+2705 | Успех, подтверждение |
| ❌ | U+274C | Отмена, закрытие |
| 🔍 | U+1F50D | Поиск |
| 📱 | U+1F4F1 | QR-сканирование, мобильное |
| 📊 | U+1F4CA | Отчеты, статистика |
| 👥 | U+1F465 | Контролёры, пользователи |
| 🚀 | U+1F680 | Начать работу, запуск |
| 🔚 | U+1F51A | Закрыть смену, конец |
| ➕ | U+2795 | Добавить |
| ➡️ | U+27A1 | Перейти к |
| ⬅️ | U+2B05 | Назад |
| 🔧 | U+1F527 | Дефекты |
| 📈 | U+1F4C8 | Качество, процент |
| ⚠️ | U+26A0 | Предупреждение |

---

### Размещение эмодзи

#### В заголовках
```html
<h1>📋 Создание новой смены</h1>
<h3>📊 Статистика смены</h3>
```

#### В кнопках
```html
<button class="btn">🔍 Найти карту</button>
<a href="/" class="start-btn">🚀 Начать работу</a>
```

#### В тексте
```html
<h4>🏭 Отлито</h4>
<p>✅ Маршрутная карта найдена</p>
```

---

### Преимущества эмодзи

✅ Универсальность (работают везде)  
✅ Не требуют загрузки шрифтов  
✅ Цветные (привлекают внимание)  
✅ Понятны интуитивно  
✅ Поддержка всех ОС

---

## 9. 🎬 Анимации

### Transitions

#### Button Hover
```css
.btn {
    transition: all 0.3s ease;
}

.btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
```

**Эффект**: Кнопка поднимается на 2px с тенью за 0.3 секунды

---

#### Input Focus
```css
input {
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

input:focus {
    border-color: #007bff;
    box-shadow: 0 0 5px rgba(0,123,255,0.3);
}
```

**Эффект**: Плавное появление синей рамки и свечения

---

### Keyframe Animations

#### Logo Float (Welcome Screen)
```css
@keyframes logoFloat {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-20px) rotate(5deg); }
}

.logo {
    animation: logoFloat 3s ease-in-out infinite;
}
```

**Эффект**: Логотип плавает вверх-вниз с небольшим поворотом (3 сек, бесконечно)

---

#### Logo Glow
```css
@keyframes logoGlow {
    0% { box-shadow: 0 0 30px rgba(255,255,255,0.3); }
    100% { box-shadow: 0 0 50px rgba(255,255,255,0.8), 0 0 80px rgba(255,165,0,0.4); }
}

.logo {
    animation: logoGlow 2s ease-in-out infinite alternate;
}
```

**Эффект**: Пульсирующее свечение логотипа (2 сек, туда-обратно)

---

#### Title Slide
```css
@keyframes titleSlide {
    0% { opacity: 0; transform: translateY(50px); }
    100% { opacity: 1; transform: translateY(0); }
}

.title {
    animation: titleSlide 1s ease-out;
}
```

**Эффект**: Заголовок выезжает снизу с fade-in (1 сек, один раз)

---

#### Subtitle Fade
```css
@keyframes subtitleFade {
    0% { opacity: 0; }
    100% { opacity: 0.9; }
}

.subtitle {
    animation: subtitleFade 1.5s ease-out 0.5s both;
}
```

**Эффект**: Подзаголовок появляется с задержкой 0.5 сек (1.5 сек)

---

#### Button Pulse
```css
@keyframes btnPulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

.start-btn {
    animation: btnPulse 2s ease-in-out infinite;
}
```

**Эффект**: Кнопка пульсирует (увеличивается/уменьшается) (2 сек, бесконечно)

---

#### Particles Float
```css
@keyframes float {
    0%, 100% { transform: translateY(0) translateX(0); opacity: 0; }
    10% { opacity: 1; }
    90% { opacity: 1; }
    100% { transform: translateY(-100vh) translateX(50px); opacity: 0; }
}

.particle {
    animation: float 15s infinite ease-in-out;
}
```

**Эффект**: Частицы плавают вверх по экрану (15 сек, бесконечно)

---

### Flash Message Auto-hide

**JavaScript**:
```javascript
setTimeout(function() {
    message.style.opacity = '0';  // Fade out
    setTimeout(function() {
        message.remove();  // Remove from DOM
    }, 500);
}, 5000);  // После 5 секунд
```

**CSS** (для плавности):
```css
.flash-message {
    transition: opacity 0.5s ease;
}
```

---

## 10. 📱 Responsive Breakpoints

### Breakpoint Definition

```css
/* Desktop (default) */
/* Без @media, базовые стили */

/* Mobile */
@media (max-width: 768px) {
    /* Mobile overrides */
}
```

**Единственный breakpoint**: 768px (стандарт для tablet/mobile)

---

### Responsive Overrides

#### Container
```css
/* Desktop */
.container {
    max-width: 800px;
    padding: 30px;
    margin: 20px auto;
}

/* Mobile */
@media (max-width: 768px) {
    .container {
        padding: 15px;
        margin: 10px;
    }
}
```

**Изменения**: Уменьшен padding и margin для маленьких экранов

---

#### Stats Grid
```css
/* Desktop */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
}

/* Mobile */
@media (max-width: 768px) {
    .stats-grid {
        grid-template-columns: 1fr;  /* Одна колонка */
    }
}
```

**Изменения**: Статистика в один столбец на мобильных

---

#### Buttons
```css
/* Desktop */
.btn {
    display: inline-block;
    margin: 5px;
}

/* Mobile */
@media (max-width: 768px) {
    .btn {
        display: block;
        width: 100%;
        margin: 10px 0;
    }
}
```

**Изменения**: Кнопки на всю ширину, вертикальное расположение

---

### Mobile-First Considerations

**Touch targets**:
- Кнопки: минимум 44×44px (текущий padding обеспечивает это)
- Увеличенный margin между элементами

**Text readability**:
- Минимум 16px font-size (без zoom)
- Достаточный line-height (1.5-1.6)

**Form inputs**:
- 100% width на всех экранах
- Large touch targets

---

### Viewport Meta Tag

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

**Параметры**:
- `width=device-width` - ширина = ширине устройства
- `initial-scale=1.0` - без начального zoom

---

## 🎯 Общие принципы стиля

### 1. Consistency (Единообразие)
- Все кнопки используют `.btn` класс
- Единая цветовая палитра
- Одинаковый spacing

### 2. Clarity (Ясность)
- Четкая визуальная иерархия
- Контрастные цвета для важных элементов
- Понятные иконки (эмодзи)

### 3. Simplicity (Простота)
- Минимум декоративных элементов
- Фокус на функциональности
- Чистый, white-space дизайн

### 4. Feedback (Обратная связь)
- Hover эффекты на интерактивных элементах
- Анимации для привлечения внимания
- Цветовое кодирование статусов

### 5. Accessibility (Доступность)
- Хороший контраст текста и фона
- Large touch targets
- Семантический HTML

---

## 📝 Шпаргалка для разработчиков

### Быстрый reference

**Создать кнопку**:
```html
<button class="btn btn-success">✅ Действие</button>
```

**Создать карточку**:
```html
<div class="shift-info">
    <h3>📋 Заголовок</h3>
    <p>Содержимое</p>
</div>
```

**Создать форму**:
```html
<form method="POST">
    <div style="margin-bottom: 20px;">
        <label for="field">Поле:</label>
        <input type="text" id="field" name="field" required style="width: 100%;">
    </div>
    <button type="submit" class="btn btn-success">✅ Сохранить</button>
</form>
```

**Создать таблицу**:
```html
<table>
    <thead><tr><th>Колонка</th></tr></thead>
    <tbody><tr><td>Данные</td></tr></tbody>
</table>
```

---

*Style Guide обновлен: 2024*
