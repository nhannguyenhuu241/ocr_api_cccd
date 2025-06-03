document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const previewContainer = document.getElementById('preview-container');
    const previewImage = document.getElementById('preview-image');
    const removeButton = document.getElementById('remove-button');
    const loadingSpinner = document.getElementById('loading-spinner');
    const resultContainer = document.getElementById('result-container');

    // Xử lý kéo thả
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) {
            handleFile(file);
        }
    });

    // Xử lý click vào drop zone
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    // Xử lý chọn file
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFile(file);
        }
    });

    // Xử lý file
    function handleFile(file) {
        if (!file.type.startsWith('image/')) {
            alert('Vui lòng chọn file hình ảnh');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            previewContainer.style.display = 'block';
            uploadImage(file);
        };
        reader.readAsDataURL(file);
    }

    // Xử lý xóa ảnh
    removeButton.addEventListener('click', () => {
        previewImage.src = '';
        previewContainer.style.display = 'none';
        resultContainer.style.display = 'none';
        fileInput.value = '';
    });

    // Upload ảnh lên server
    async function uploadImage(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            showLoading();
            const response = await fetch('/api/ocr_cccd/', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Lỗi khi xử lý ảnh');
            }

            const data = await response.json();
            displayResults(data.extracted_data);
        } catch (error) {
            console.error('Error:', error);
            alert('Có lỗi xảy ra khi xử lý ảnh');
        } finally {
            hideLoading();
        }
    }

    // Hiển thị kết quả
    function displayResults(data) {
        const resultContainer = document.getElementById('result-container');
        const resultGrid = document.getElementById('result-grid');

        // Xóa kết quả cũ
        resultGrid.innerHTML = '';

        // Thêm kết quả mới
        for (const [key, value] of Object.entries(data)) {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';
            
            const label = document.createElement('div');
            label.className = 'result-label';
            label.textContent = formatLabel(key);
            
            const content = document.createElement('div');
            content.className = 'result-content';
            content.textContent = value;

            resultItem.appendChild(label);
            resultItem.appendChild(content);
            resultGrid.appendChild(resultItem);
        }

        resultContainer.style.display = 'block';
    }

    // Format label
    function formatLabel(key) {
        const labels = {
            'id_number': 'Số CCCD',
            'full_name': 'Họ và tên',
            'date_of_birth': 'Ngày sinh',
            'gender': 'Giới tính',
            'nationality': 'Quốc tịch',
            'place_of_origin': 'Quê quán',
            'permanent_address': 'Nơi thường trú',
            'date_of_issue': 'Ngày cấp',
            'place_of_issue': 'Nơi cấp'
        };
        return labels[key] || key;
    }

    // Hiển thị loading
    function showLoading() {
        loadingSpinner.style.display = 'flex';
    }

    // Ẩn loading
    function hideLoading() {
        loadingSpinner.style.display = 'none';
    }
}); 