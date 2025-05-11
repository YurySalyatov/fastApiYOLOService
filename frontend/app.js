document.addEventListener('DOMContentLoaded', () => {
    initColorPicker();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('process-btn').addEventListener('click', processFile);
    document.getElementById('confidence').addEventListener('input', updateConfidence);
    document.getElementById('model-select').addEventListener('change', toggleCustomModel);
}

async function processFile() {
    const formData = new FormData();
    const fileInput = document.getElementById('file-input');
    const modelType = document.getElementById('model-select').value;

    // Добавить файлы для кастомной модели
    if (modelType === 'custom') {
        formData.append('custom_weights', document.getElementById('weights-file').files[0]);
        formData.append('custom_config', document.getElementById('config-file').files[0]);
    }
    if (fileInput.files[0]) {
        formData.append('file', fileInput.files[0]);
    }

    formData.append('confidence', document.getElementById('confidence').value);
    formData.append('model_name', document.getElementById('model-select').value);

    try {
        const response = await fetch('http://localhost:8000/upload/', {
            method: 'POST',
            body: formData
        });

        const {task_id} = await response.json();
        monitorTask(task_id);
    } catch (error) {
        console.error('Error:', error);
    }
}

function monitorTask(taskId) {
    const processingStatus = document.getElementById('processing-status');
    const originalImg = document.getElementById('original-img');

    fetch(`http://localhost:8000/tasks/${taskId}`)
        .then(response => response.json())
        .then(({status, result}) => {
            if (status === 'SUCCESS') {
                processingStatus.style.display = 'none';
                showResult(result);
            } else if (status === 'FAILURE') {
                processingStatus.textContent = 'Error!';
            } else {
                processingStatus.style.display = 'block';
                originalImg.style.display = 'block';
                setTimeout(() => monitorTask(taskId), 2000);
            }
        });
}

function showResult(filePath) {
    const isVideo = filePath.endsWith('.mp4');
    if (isVideo) return; // Видео временно не обрабатываем

    // Показываем оригинал
    const originalImg = document.getElementById('original-img');
    originalImg.style.display = 'block';
    originalImg.src = `http://localhost:8000/${filePath.replace('processed_', '')}`;

    // Показываем кнопки
    document.querySelector('.navigation-buttons').style.display = 'flex';

    // Обработанное изображение
    const processedImg = document.getElementById('processed-img');
    processedImg.style.display = 'block';
    processedImg.src = `http://localhost:8000/${filePath}`;

    // Обработчики кнопок
    document.getElementById('prev-btn').addEventListener('click', () => {
        processedImg.style.display = 'none';
        originalImg.style.display = 'block';
        document.getElementById('prev-btn').disabled = true;
        document.getElementById('next-btn').disabled = false;
    });

    document.getElementById('next-btn').addEventListener('click', () => {
        processedImg.style.display = 'block';
        originalImg.style.display = 'none';
        document.getElementById('prev-btn').disabled = false;
        document.getElementById('next-btn').disabled = true;
    });
}

function initColorPicker(classes = []) {
    const container = document.getElementById('color-grid');
    container.innerHTML = '';

    classes.forEach((className, index) => {
        const color = DEFAULT_COLORS[index % DEFAULT_COLORS.length];
        const wrapper = document.createElement('div');
        wrapper.className = 'color-item';
        wrapper.innerHTML = `
            <label>${className}</label>
            <input type="color" value="${color}">
        `;
        container.appendChild(wrapper);
    });
}

// Обновить функцию toggleCustomModel
function toggleCustomModel() {
    const modelSelect = document.getElementById('model-select');
    const customFields = document.getElementById('custom-model-fields');

    if (modelSelect.value === 'custom') {
        customFields.style.display = 'block';
        document.querySelector('.color-picker').style.display = 'block';
        currentClasses = [];
        updateColorPicker([]);
    } else {
        customFields.style.display = 'none';
        loadModelClasses(modelSelect.value);
    }
}

function updateConfidence(e) {
    document.getElementById('confidence-value').textContent = e.target.value;
}

document.getElementById('file-input').addEventListener('change', function (e) {
    const file = e.target.files[0];
    const originalImg = document.getElementById('original-img');
    const url = URL.createObjectURL(file);

    originalImg.style.display = 'block';
    originalImg.src = url;
});

let currentClasses = [];

// Загрузка доступных моделей при старте
function loadAvailableModels() {
    try {
        const response = fetch('/api/models');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const models = response.json();

        const modelSelect = document.getElementById('model-select');
        modelSelect.innerHTML = ''; // Полная очистка списка

        // Добавляем дефолтную опцию
        const defaultOption = new Option('Select a model...', '');
        defaultOption.disabled = true;
        defaultOption.selected = true;
        modelSelect.add(defaultOption);

        // Добавляем кастомную опцию
        modelSelect.add(new Option('Custom Model', 'custom'));

        // Добавляем существующие модели
        models.forEach(model => {
            const option = new Option(
                `${model.name} (${model.classes.length} classes)`,
                model.name
            );
            modelSelect.add(option);
        });

        return models; // Возвращаем результат для возможного использования
    } catch (error) {
        console.error('Error loading models:', error);
        throw error; // Пробрасываем ошибку дальше
    }
}

// Парсинг YAML конфига
async function parseYamlConfig(event) {
    const file = event.target.files[0];
    if (!file) return;

    try {
        const yamlText = await file.text();
        const config = jsyaml.load(yamlText);
        currentClasses = config.names || [];
        updateColorPicker(currentClasses); // Используем цвета по умолчанию
    } catch (error) {
        alert('Error parsing YAML file: ' + error.message);
        event.target.value = '';
    }
}

function updateColorPicker(classes, colors = {}) {
    const colorGrid = document.getElementById('color-grid');
    colorGrid.innerHTML = '';

    classes.forEach((className, index) => {
        const defaultColor = DEFAULT_COLORS[index % DEFAULT_COLORS.length];
        const color = colors[className] || defaultColor;

        const div = document.createElement('div');
        div.className = 'color-item';
        div.innerHTML = `
            <label>${className}</label>
            <input type="color" value="${color}">
        `;
        colorGrid.appendChild(div);
    });
}

async function loadModelClasses(modelName) {
    try {
        const response = await fetch(`/api/models`);
        const models = await response.json();
        const model = models.find(m => m.name === modelName);

        if (model) {
            currentClasses = model.classes;
            const colors = model.colors || {};
            updateColorPicker(model.classes, colors);
        }
    } catch (error) {
        console.error('Error loading model classes:', error);
    }
}

window.addEventListener('DOMContentLoaded', async () => {
    try {
        loadAvailableModels();
        initColorPicker();
        document.getElementById('model-select').value = '';
    } catch (error) {
        console.error('Initialization error:', error);
        alert('Failed to load models. Please refresh the page.');
    }
});