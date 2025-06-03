# OCR CCCD API

API trích xuất thông tin từ ảnh Căn cước công dân Việt Nam sử dụng EasyOCR và LLaMA.

## Tính năng

- Trích xuất thông tin từ ảnh CCCD
- Hỗ trợ OCR tiếng Việt
- Xử lý và làm sạch dữ liệu
- API RESTful với FastAPI
- Giao diện web thân thiện

## Cài đặt

1. Clone repository:
```bash
git clone https://github.com/yourusername/ocr_api_cccd.git
cd ocr_api_cccd
```

2. Tạo môi trường ảo Python:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
.\venv\Scripts\activate  # Windows
```

3. Cài đặt các thư viện cần thiết:

```bash
# Cài đặt các thư viện cơ bản
pip install fastapi==0.115.12
pip install uvicorn==0.34.3
pip install python-multipart==0.0.20
pip install Pillow==11.2.1
pip install jinja2==3.1.3

# Cài đặt OpenCV và các thư viện xử lý ảnh
pip install opencv-python==4.9.0.80
pip install numpy==1.26.4

# Cài đặt EasyOCR
pip install easyocr==1.7.2

# Cài đặt PyTorch (tùy chọn, nếu muốn sử dụng GPU)
pip install torch==2.7.0

# Cài đặt LLaMA
pip install llama-cpp-python[server]==0.3.9
```

4. Tải model LLaMA:
```bash
# Tạo thư mục models
mkdir -p models

# Tải model LLaMA (chọn một trong các phiên bản)
curl -L -o models/Vintern-1B-v3_5-f16_q4_k.gguf https://huggingface.co/TheBloke/Vintern-1B-v3.5-GGUF/resolve/main/vintern-1b-v3_5.Q4_K_M.gguf
```

## Chạy ứng dụng

1. Khởi động server:
```bash
uvicorn main:app --reload
```

2. Truy cập API:
- API endpoint: http://localhost:8000/api/ocr_cccd/
- Giao diện web: http://localhost:8000

## API Endpoints

### POST /api/ocr_cccd/
Trích xuất thông tin từ ảnh CCCD

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: file (ảnh CCCD)

**Response:**
```json
{
    "status": "success",
    "extracted_data": {
        "id_number": "001234567890",
        "full_name": "NGUYỄN VĂN A",
        "date_of_birth": "01/01/1990",
        "gender": "Nam",
        "nationality": "Việt Nam",
        "place_of_origin": "Hà Nội",
        "permanent_address": "123 Đường ABC, Quận XYZ, TP. Hà Nội",
        "date_of_issue": "01/01/2020",
        "place_of_issue": "Công an TP. Hà Nội"
    }
}
```

## Đóng góp

Mọi đóng góp đều được hoan nghênh! Vui lòng tạo issue hoặc pull request.

## Giấy phép

MIT License