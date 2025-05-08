// static/js/whiteboard.js
let canvas, ctx;
let isDrawing = false;
let currentTool = 'pointer';
let currentColor = '#000000';
let currentWidth = 3;
let currentElements = [];
let undoStack = [];
let redoStack = [];
let selectedElement = null;
let startX, startY;
let lastX, lastY;

// 初始化白板
function initWhiteboard(config) {
    canvas = document.getElementById('whiteboard-canvas');
    ctx = canvas.getContext('2d');
    
    // 設置基本配置
    const boardId = config.boardId;
    const canEdit = config.canEdit;
    const elementsUrl = config.elementsUrl;
    const csrfToken = config.csrfToken;
    
    // 如果有初始元素，載入它們
    if (config.initialElements && config.initialElements.length > 0) {
        currentElements = config.initialElements;
        redrawCanvas();
    } else {
        // 否則從服務器獲取元素
        fetchElements();
    }
    
    // 如果用戶可以編輯，添加事件監聽器
    if (canEdit) {
        setupEventListeners();
    }
    
    // 設置工具欄按鈕
    setupToolbarButtons();
    
    // 定期保存畫布內容（每10秒）
    setInterval(() => {
        if (canEdit && currentElements.length > 0) {
            // 可以添加自動保存邏輯
        }
    }, 10000);
    
    // 函數：從服務器獲取元素
    function fetchElements() {
        fetch(elementsUrl)
            .then(response => response.json())
            .then(data => {
                if (data.elements) {
                    currentElements = data.elements;
                    redrawCanvas();
                    updateElementCount();
                }
            })
            .catch(error => console.error('Error fetching elements:', error));
    }
    
    // 函數：設置事件監聽器
    function setupEventListeners() {
        canvas.addEventListener('mousedown', handleMouseDown);
        canvas.addEventListener('mousemove', handleMouseMove);
        canvas.addEventListener('mouseup', handleMouseUp);
        canvas.addEventListener('mouseout', handleMouseUp);
        
        // 觸控支持
        canvas.addEventListener('touchstart', handleTouchStart);
        canvas.addEventListener('touchmove', handleTouchMove);
        canvas.addEventListener('touchend', handleTouchEnd);
    }
    
    // 函數：設置工具欄按鈕
    function setupToolbarButtons() {
        // 工具選擇按鈕
        document.getElementById('tool-pointer').addEventListener('click', () => selectTool('pointer'));
        document.getElementById('tool-pen').addEventListener('click', () => selectTool('pen'));
        document.getElementById('tool-text').addEventListener('click', () => selectTool('text'));
        document.getElementById('tool-shape').addEventListener('click', () => selectTool('shape'));
        document.getElementById('tool-image').addEventListener('click', () => selectTool('image'));
        
        // 顏色選擇器
        document.getElementById('color-select').addEventListener('change', (e) => {
            currentColor = e.target.value;
        });
        
        // 寬度選擇器
        document.getElementById('width-select').addEventListener('change', (e) => {
            currentWidth = parseInt(e.target.value);
        });
        
        // 復原/重做按鈕
        document.getElementById('btn-undo').addEventListener('click', undo);
        document.getElementById('btn-redo').addEventListener('click', redo);
        
        // 清除白板按鈕
        document.getElementById('btn-clear').addEventListener('click', clearBoard);
        
        // 導出按鈕
        document.getElementById('btn-export').addEventListener('click', showExportModal);
        
        // 錄製按鈕
        document.getElementById('btn-record').addEventListener('click', toggleRecording);
        
        // 導出模態框保存按鈕
        document.getElementById('saveExport').addEventListener('click', saveExport);
    }
    
    // 函數：選擇工具
    function selectTool(tool) {
        currentTool = tool;
        
        // 更新 UI
        document.querySelectorAll('.btn-outline-primary').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(`tool-${tool}`).classList.add('active');
        
        // 根據選擇的工具更改光標
        switch(tool) {
            case 'pointer':
                canvas.style.cursor = 'default';
                break;
            case 'pen':
                canvas.style.cursor = 'crosshair';
                break;
            case 'text':
                canvas.style.cursor = 'text';
                break;
            case 'shape':
                canvas.style.cursor = 'crosshair';
                break;
            case 'image':
                canvas.style.cursor = 'cell';
                break;
        }
    }
    
    // 函數：重繪畫布
    function redrawCanvas() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        currentElements.forEach(element => {
            drawElement(element);
        });
        
        // 更新復原/重做按鈕狀態
        document.getElementById('btn-undo').disabled = undoStack.length === 0;
        document.getElementById('btn-redo').disabled = redoStack.length === 0;
    }
    
    // 函數：繪製元素
    function drawElement(element) {
        const data = element.data;
        
        switch(element.element_type) {
            case 'stroke':
                drawStroke(data);
                break;
            case 'text':
                drawText(data);
                break;
            case 'shape':
                drawShape(data);
                break;
            case 'image':
                drawImage(data);
                break;
        }
    }
    
    // 函數：繪製筆畫
    function drawStroke(data) {
        ctx.beginPath();
        ctx.moveTo(data.points[0].x, data.points[0].y);
        
        for (let i = 1; i < data.points.length; i++) {
            ctx.lineTo(data.points[i].x, data.points[i].y);
        }
        
        ctx.strokeStyle = data.color;
        ctx.lineWidth = data.width;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.stroke();
    }
    
    // 函數：繪製文字
    function drawText(data) {
        ctx.font = `${data.fontSize}px Arial`;
        ctx.fillStyle = data.color;
        ctx.fillText(data.text, data.x, data.y);
    }
    
    // 函數：繪製圖形
    function drawShape(data) {
        ctx.beginPath();
        
        switch(data.shapeType) {
            case 'rectangle':
                ctx.rect(data.x, data.y, data.width, data.height);
                break;
            case 'circle':
                ctx.arc(data.x + data.radius, data.y + data.radius, data.radius, 0, Math.PI * 2);
                break;
            case 'line':
                ctx.moveTo(data.x1, data.y1);
                ctx.lineTo(data.x2, data.y2);
                break;
        }
        
        if (data.fill) {
            ctx.fillStyle = data.color;
            ctx.fill();
        }
        
        ctx.strokeStyle = data.color;
        ctx.lineWidth = data.width;
        ctx.stroke();
    }
    
    // 函數：繪製圖片
    function drawImage(data) {
        const img = new Image();
        img.onload = () => {
            ctx.drawImage(img, data.x, data.y, data.width, data.height);
        };
        img.src = data.src;
    }
    
    // 函數：處理滑鼠按下
    function handleMouseDown(e) {
        isDrawing = true;
        const rect = canvas.getBoundingClientRect();
        startX = e.clientX - rect.left;
        startY = e.clientY - rect.top;
        lastX = startX;
        lastY = startY;
        
        if (currentTool === 'pen') {
            // 添加新元素
            const newElement = {
                id: Date.now(),
                element_type: 'stroke',
                data: {
                    points: [{ x: startX, y: startY }],
                    color: currentColor,
                    width: currentWidth
                }
            };
            
            currentElements.push(newElement);
            redoStack = []; // 清空重做堆疊
        } else if (currentTool === 'text') {
            const text = prompt('請輸入文字:');
            if (text) {
                const newElement = {
                    id: Date.now(),
                    element_type: 'text',
                    data: {
                        text: text,
                        x: startX,
                        y: startY,
                        color: currentColor,
                        fontSize: currentWidth * 5
                    }
                };
                
                undoStack.push([...currentElements]);
                currentElements.push(newElement);
                redrawCanvas();
                updateElementCount();
                saveElementToServer(newElement, 'add');
            }
        } else if (currentTool === 'shape') {
            // 開始繪製形狀
            const shapeType = prompt('請選擇形狀類型 (rectangle, circle, line):');
            if (['rectangle', 'circle', 'line'].includes(shapeType)) {
                selectedElement = {
                    id: Date.now(),
                    element_type: 'shape',
                    data: {
                        shapeType: shapeType,
                        x: startX,
                        y: startY,
                        width: 0,
                        height: 0,
                        x1: startX,
                        y1: startY,
                        x2: startX,
                        y2: startY,
                        radius: 0,
                        color: currentColor,
                        width: currentWidth,
                        fill: false
                    }
                };
            }
        } else if (currentTool === 'image') {
            const imageUrl = prompt('請輸入圖片URL:');
            if (imageUrl) {
                const newElement = {
                    id: Date.now(),
                    element_type: 'image',
                    data: {
                        src: imageUrl,
                        x: startX,
                        y: startY,
                        width: 200,
                        height: 150
                    }
                };
                
                undoStack.push([...currentElements]);
                currentElements.push(newElement);
                redrawCanvas();
                updateElementCount();
                saveElementToServer(newElement, 'add');
            }
        }
    }
    
    // 函數：處理滑鼠移動
    function handleMouseMove(e) {
        if (!isDrawing) return;
        
        const rect = canvas.getBoundingClientRect();
        const currentX = e.clientX - rect.left;
        const currentY = e.clientY - rect.top;
        
        if (currentTool === 'pen') {
            const currentStroke = currentElements[currentElements.length - 1];
            currentStroke.data.points.push({ x: currentX, y: currentY });
            
            // 只繪製新增的線段部分
            ctx.beginPath();
            ctx.moveTo(lastX, lastY);
            ctx.lineTo(currentX, currentY);
            ctx.strokeStyle = currentColor;
            ctx.lineWidth = currentWidth;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            ctx.stroke();
            
            lastX = currentX;
            lastY = currentY;
        } else if (currentTool === 'shape' && selectedElement) {
            // 更新形狀尺寸
            if (selectedElement.data.shapeType === 'rectangle' || selectedElement.data.shapeType === 'circle') {
                selectedElement.data.width = currentX - startX;
                selectedElement.data.height = currentY - startY;
                selectedElement.data.radius = Math.min(Math.abs(selectedElement.data.width), Math.abs(selectedElement.data.height)) / 2;
            } else if (selectedElement.data.shapeType === 'line') {
                selectedElement.data.x2 = currentX;
                selectedElement.data.y2 = currentY;
            }
            
            // 重繪畫布以顯示更新的形狀
            redrawCanvas();
            drawElement(selectedElement);
        }
    }
    
    // 函數：處理滑鼠釋放
    function handleMouseUp(e) {
        if (!isDrawing) return;
        isDrawing = false;
        
        if (currentTool === 'pen') {
            const newElement = currentElements[currentElements.length - 1];
            undoStack.push(currentElements.slice(0, -1));
            saveElementToServer(newElement, 'add');
            updateElementCount();
        } else if (currentTool === 'shape' && selectedElement) {
            undoStack.push([...currentElements]);
            currentElements.push(selectedElement);
            saveElementToServer(selectedElement, 'add');
            selectedElement = null;
            redrawCanvas();
            updateElementCount();
        }
    }
    
    // 函數：處理觸控開始
    function handleTouchStart(e) {
        e.preventDefault();
        if (e.touches.length === 1) {
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousedown', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            handleMouseDown(mouseEvent);
        }
    }
    
    // 函數：處理觸控移動
    function handleTouchMove(e) {
        e.preventDefault();
        if (e.touches.length === 1) {
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousemove', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            handleMouseMove(mouseEvent);
        }
    }
    
    // 函數：處理觸控結束
    function handleTouchEnd(e) {
        e.preventDefault();
        const mouseEvent = new MouseEvent('mouseup', {});
        handleMouseUp(mouseEvent);
    }
    
    // 函數：復原
    function undo() {
        if (undoStack.length > 0) {
            redoStack.push([...currentElements]);
            currentElements = undoStack.pop();
            redrawCanvas();
            updateElementCount();
        }
    }
    
    // 函數：重做
    function redo() {
        if (redoStack.length > 0) {
            undoStack.push([...currentElements]);
            currentElements = redoStack.pop();
            redrawCanvas();
            updateElementCount();
        }
    }
    
    // 函數：清除白板
    function clearBoard() {
        if (confirm('確定要清除整個白板嗎？此操作不可復原。')) {
            undoStack.push([...currentElements]);
            currentElements = [];
            redrawCanvas();
            updateElementCount();
            
            // 通知服務器清除白板
            fetch(elementsUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    action: 'clear'
                })
            })
            .catch(error => console.error('Error clearing board:', error));
        }
    }
    
    // 函數：顯示導出模態框
    function showExportModal() {
        // 將白板轉換為圖像
        const dataURL = canvas.toDataURL('image/png');
        
        // 創建臨時圖像並進行OCR（這裡只是模擬，實際中可能需要使用OCR服務）
        const tempImage = new Image();
        tempImage.src = dataURL;
        tempImage.onload = () => {
            // 模擬OCR結果
            document.getElementById('recognized_text').value = '白板內容辨識結果會顯示在這裡...';
            
            // 顯示模態框
            const exportModal = new bootstrap.Modal(document.getElementById('exportModal'));
            exportModal.show();
        };
    }
    
    // 函數：保存導出
    function saveExport() {
        const recognizedText = document.getElementById('recognized_text').value;
        
        // 提交表單
        document.getElementById('exportForm').submit();
    }
    
    // 函數：切換錄製
    let isRecording = false;
    let mediaRecorder = null;
    let recordedChunks = [];
    
    function toggleRecording() {
        if (!isRecording) {
            // 開始錄製
            startRecording();
        } else {
            // 停止錄製
            stopRecording();
        }
    }
    
    // 函數：開始錄製
    function startRecording() {
        recordedChunks = [];
        
        // 使用 MediaRecorder API 錄製畫布
        const stream = canvas.captureStream(30); // 30 FPS
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm' });
        
        mediaRecorder.ondataavailable = function(e) {
            if (e.data.size > 0) {
                recordedChunks.push(e.data);
            }
        };
        
        mediaRecorder.onstop = function() {
            const blob = new Blob(recordedChunks, { type: 'video/webm' });
            const formData = new FormData();
            formData.append('file', blob, 'recording.webm');
            
            // 發送錄製文件到服務器
            fetch(`/boards/${boardId}/record/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('錄製已保存！');
                }
            })
            .catch(error => console.error('Error saving recording:', error));
        };
        
        mediaRecorder.start();
        isRecording = true;
        
        // 更新按鈕狀態
        const recordButton = document.getElementById('btn-record');
        recordButton.classList.remove('btn-danger');
        recordButton.classList.add('btn-warning');
        recordButton.innerHTML = '<i class="fas fa-stop me-1"></i>停止錄製';
    }
    
    // 函數：停止錄製
    function stopRecording() {
        if (mediaRecorder && isRecording) {
            mediaRecorder.stop();
            isRecording = false;
            
            // 更新按鈕狀態
            const recordButton = document.getElementById('btn-record');
            recordButton.classList.remove('btn-warning');
            recordButton.classList.add('btn-danger');
            recordButton.innerHTML = '<i class="fas fa-video me-1"></i>錄製';
        }
    }
    
    // 函數：更新元素計數
    function updateElementCount() {
        const elementCountElement = document.getElementById('element-count');
        if (elementCountElement) {
            elementCountElement.textContent = currentElements.length;
        }
    }
    
    // 函數：保存元素到服務器
    function saveElementToServer(element, action) {
        fetch(elementsUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                action: action,
                element_type: element.element_type,
                element_id: element.id,
                data: element.data
            })
        })
        .catch(error => console.error('Error saving element:', error));
    }
}