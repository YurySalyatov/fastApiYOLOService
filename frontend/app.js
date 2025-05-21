let prevFile = null

function setupEventListeners() {
    document.getElementById('process-btn').addEventListener('click', processFile);
    document.getElementById('confidence').addEventListener('input', updateConfidence);
    document.getElementById('model-select').addEventListener('change', toggleCustomModel);
    document.getElementById('file-input').addEventListener('change', updateFile);
}

function updateFile(e) {
    const file = e.target.files[0];
    if (!file) {
        return
    }

    const originalImg = document.getElementById('original-img');
    const processedImg = document.getElementById('processed-img');
    const processingStatus = document.getElementById('processing-status');

    const isSameFile = prevFile &&
        file.name === prevFile.name &&
        file.size === prevFile.size &&
        file.lastModified === prevFile.lastModified;

    if (isSameFile) {
        return;
    }

    URL.revokeObjectURL(originalImg.src);
    processedImg.style.display = 'none';
    processedImg.src = '';
    processingStatus.style.display = 'none';
    document.getElementById('preset-files').value = '';

    const url = URL.createObjectURL(file);
    originalImg.style.display = 'block';
    originalImg.src = url;

    prevFile = {
        name: file.name,
        size: file.size,
        lastModified: file.lastModified,
        inputFiles: e.target.files // Сохраняем весь FileList
    };
}


async function processFile() {
    const formData = new FormData();
    const fileInput = document.getElementById('file-input');
    const modelType = document.getElementById('model-select').value;
    const processedImg = document.getElementById('processed-img');
    processedImg.src = ''
    // Добавить файлы для кастомной модели
    if (modelType === 'custom') {
        formData.append('custom_weights', document.getElementById('weights-file').files[0]);
    }
    if (fileInput.files[0]) {
        const file = fileInput.files[0]
        formData.append('file', file);
        console.log(file)
    }
    const conf = document.getElementById('confidence').value
    formData.append('confidence', conf);
    console.log(conf)
    const model_name = document.getElementById('model-select').value
    formData.append('model_name', model_name);
    console.log(model_name)
    const colorItems = document.querySelectorAll('.color-item input[type="color"]');
    const colorsRGB = Array.from(colorItems).map(input => hexToRgb(input.value));
    console.log(colorsRGB)
    formData.append("colors", JSON.stringify(colorsRGB))
    try {
        const response = await fetch('/upload/', {
            method: 'POST',
            body: formData
        });

        const {task_id} = await response.json();
        monitorTask(task_id);
    } catch (error) {
        console.error('Error:', error);
    }
}

async function monitorTask(taskId) {
    const processingStatus = document.getElementById('processing-status');
    const originalImg = document.getElementById('original-img');
    console.log(`monitoring ${taskId}`)
    const resp = await fetch(`/api/tasks/${taskId}`)
    const resp_json = await resp.json()
    const status = resp_json.status
    if (status === 'SUCCESS') {
        processingStatus.style.display = 'none';
        showResult(resp_json.result);
    } else if (status === 'FAILURE') {
        processingStatus.textContent = 'Error!';
    } else {
        processingStatus.style.display = 'block';
        originalImg.style.display = 'block';
        setTimeout(() => monitorTask(taskId), 2000);
    }
}

function showResult(filePath) {
    const isVideo = filePath.endsWith('.mp4');
    if (isVideo) return;

    console.log(filePath)
    console.log(filePath)
    const originalImg = document.getElementById('original-img');
    originalImg.style.display = 'block';
    originalImg.src = `/uploads/${filePath.replace('processed_', '')}`;
    console.log(originalImg.src)

    const processedImg = document.getElementById('processed-img');
    processedImg.style.display = 'block';
    processedImg.src = `/processed/${filePath}`;
    console.log(processedImg.src)
}

// function initColorPicker(classes = []) {
//     const dropdownHeader = document.querySelector('.dropdown-header');
//     const container = document.getElementById('color-list');
//
//     container.innerHTML = '';
//
//     classes.forEach((className, index) => {
//         const color = DEFAULT_COLORS[index % DEFAULT_COLORS.length];
//         const wrapper = document.createElement('div');
//         wrapper.className = 'color-item';
//         wrapper.innerHTML = `
//             <label>${className}</label>
//             <input type="color" value="${color}">
//         `;
//         container.appendChild(wrapper);
//     });
// }

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

let currentClasses = [];

// Загрузка доступных моделей при старте
async function loadAvailableModels() {
    try {
        const response = await fetch('/api/models');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const models = await response.json();

        const modelSelect = document.getElementById('model-select');
        modelSelect.innerHTML = ''; // Полная очистка списка

        // Добавляем кастомную опцию
        modelSelect.add(new Option('Custom Model', 'custom'));

        // Добавляем существующие модели
        models.forEach(model => {
            const classCount = Object.keys(model.classes).length;
            const option = new Option(
                `${model.name} (${classCount} classes)`,
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

function rgbToHex(rgbArray) {
    return '#' + rgbArray.map(x => {
        const val = Math.max(0, Math.min(255, x));
        return val.toString(16).padStart(2, '0');
    }).join('');
}

function hexToRgb(hex) {
    hex = hex.replace(/^#/, '');

    let r = parseInt(hex.substring(0, 2), 16);
    let g = parseInt(hex.substring(2, 4), 16);
    let b = parseInt(hex.substring(4, 6), 16);

    return [r, g, b];
}

function updateColorPicker(classes, colors) {
    const dropdownHeader = document.querySelector('.dropdown-toggle');
    const colorList = document.getElementById('color-list');

    // Очищаем предыдущие элементы
    colorList.innerHTML = '';

    // Создаем элементы списка
    for (let i = 0; i < colors.length; i++) {
        const color = colors[i];
        const className = classes[i];

        const itemDiv = document.createElement('div');
        itemDiv.className = 'color-item';
        itemDiv.innerHTML = `
            <input type="color" value="${rgbToHex(color)}">
            <span>${className}</span>
        `;
        colorList.appendChild(itemDiv);
    }

    // Добавляем обработчики событий
    dropdownHeader.addEventListener('click', () => {
        colorList.classList.toggle('show');
    });

    // Закрываем список при клике вне области
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.color-dropdown')) {
            colorList.classList.remove('show');
        }
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
    setupEventListeners();
    // initColorPicker();
    try {
        await loadAvailableModels();
        document.getElementById('model-select').value = '';
    } catch (error) {
        console.error('Initialization error:', error);
        alert('Failed to load models. Please refresh the page.');
    }
});