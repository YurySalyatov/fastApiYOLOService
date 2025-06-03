let prevFile = null;
let cameraStream = null;
let processingInterval = null;
let isProcessing = false;

function setupEventListeners() {
    document.getElementById('process-btn').addEventListener('click', processFile);
    document.getElementById('confidence').addEventListener('input', updateConfidence);
    document.getElementById('model-select').addEventListener('change', toggleCustomModel);
    document.getElementById('file-input').addEventListener('change', updateFile);
    document.getElementById('start-camera').addEventListener('click', toggleCamera);
    document.getElementById('process-frame').addEventListener('click', processCameraFrame);
    document.getElementById('download-btn').addEventListener('click', downloadFile)
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
        origfile: file,
        name: file.name,
        size: file.size,
        lastModified: file.lastModified,
        inputFiles: e.target.files // Сохраняем весь FileList
    };
    document.getElementById('download-btn').style.display = 'none'
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
        const response = await fetch('/upload/file/', {
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
    const resp = await fetch(`/api/tasks/${taskId}/`)
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
    const downloadBtn = document.getElementById('download-btn');
    if (isVideo) {
        const processingStatus = document.getElementById('processing-status');
        processingStatus.style.display = 'none';

        // Настраиваем кнопку скачивания для видео
        downloadBtn.href = `/processed/${filePath}`;
        downloadBtn.download = `processed_${filePath.replace('processed_', '')}`;
        downloadBtn.textContent = 'Download Video';
        downloadBtn.style.display = 'block';

        // Показываем сообщение о готовности видео
        const processedImg = document.getElementById('processed-img');
        processedImg.style.display = 'block';
        processedImg.src = ''; // Очищаем предыдущее изображение
        processedImg.alt = 'Video processing complete';
        processedImg.style.width = 'auto';
        processedImg.style.height = 'auto';
        processedImg.style.objectFit = 'none';
        processedImg.innerHTML = '<div class="video-ready">Video processing complete!<br>Click "Download Video" to get the result.</div>';

        return
    }

    // console.log(filePath)
    // console.log(filePath)
    const originalImg = document.getElementById('original-img');
    originalImg.style.display = 'block';
    originalImg.src = `/uploads/${filePath.replace('processed_', '')}`;
    // console.log(originalImg.src)

    const processedImg = document.getElementById('processed-img');
    processedImg.style.display = 'block';
    processedImg.src = `/processed/${filePath}`;
    // console.log(processedImg.src)
    downloadBtn.href = `/processed/${filePath}`;
    downloadBtn.download = `processed_${filePath.replace('processed_', '')}`;
    downloadBtn.textContent = 'Download Image';
    downloadBtn.style.display = 'block';
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

let currentClasses = [];

// Загрузка доступных моделей при старте
async function loadAvailableModels() {
    try {
        const response = await fetch('/api/models/');
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
        const response = await fetch(`/api/models/`);
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
    try {
        await loadAvailableModels();
        document.getElementById('model-select').value = '';
    } catch (error) {
        console.error('Initialization error:', error);
        alert('Failed to load models. Please refresh the page.');
    }
});

async function initCamera() {
    try {
        const video = document.getElementById('camera-preview');
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: {ideal: 1280},
                height: {ideal: 720},
                frameRate: {ideal: 30}
            }
        });

        video.srcObject = stream;
        cameraStream = stream;
        document.getElementById('process-frame').disabled = false;
        document.getElementById('start-camera').textContent = 'Disable Camera';
        document.getElementById('camera-preview').style.display = 'block';

        return true;
    } catch (error) {
        console.error('Error accessing camera:', error);
        alert('Cannot access camera: ' + error.message);
        return false;
    }
}

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
        document.getElementById('process-frame').disabled = true;
        document.getElementById('start-camera').textContent = 'Enable Camera';
        document.getElementById('camera-preview').style.display = 'none';
        document.getElementById('processed-frame').style.display = 'none';
    }

    if (processingInterval) {
        clearInterval(processingInterval);
        processingInterval = null;
    }
}

async function toggleCamera() {
    if (cameraStream) {
        stopCamera();
    } else {
        const success = await initCamera();
        if (success) {
            startFrameProcessing();
        }
    }
}

function startFrameProcessing() {
    if (processingInterval) return;

    // Обработка кадра каждые 200мс (5 FPS)
    processingInterval = setInterval(processCameraFrame, 200);
}

async function processCameraFrame() {
    if (!cameraStream) return;

    try {
        const video = document.getElementById('camera-preview');
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        const blob = await new Promise(resolve =>
            canvas.toBlob(resolve, 'image/jpeg', 0.95)
        );

        const formData = new FormData();
        formData.append('frame', blob, 'frame.jpg');
        formData.append('confidence', document.getElementById('confidence').value);
        formData.append('model_name', document.getElementById('model-select').value);

        const colorItems = document.querySelectorAll('.color-item input[type="color"]');
        const colorsRGB = Array.from(colorItems).map(input => hexToRgb(input.value));
        formData.append('colors', JSON.stringify(colorsRGB));

        const response = await fetch('/camera_upload/process_frame/', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        updateCameraResult(result);

    } catch (error) {
        console.error('Frame processing error:', error);
    }
}

function updateCameraResult(result) {
    const processedImg = document.getElementById('processed-frame');

    // Если результат - base64 изображение
    if (result.processed_frame) {
        processedImg.src = `data:image/jpeg;base64,${result.processed_frame}`;
        processedImg.style.display = 'block';
    }
    // Если результат - URL файла
    else if (result.file_path) {
        processedImg.src = `/processed/${result.file_path}`;
        processedImg.style.display = 'block';
    }

    // Обновляем счетчики
    if (result.latency) {
        document.getElementById('latency-counter').textContent = result.latency;
    }
}

function downloadFile() {
    const processedFile = document.getElementById('processed-img')
    // Создаем временную ссылку
    const url = URL.createObjectURL();
    const a = document.createElement('a');

    // Настраиваем ссылку
    a.href = url;
    a.download = processedFile.name; // Имя файла
    a.style.display = 'none';

    // Добавляем в DOM и эмулируем клик
    document.body.appendChild(a);
    a.click();

    // Убираем ссылку и освобождаем память
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 100);
}