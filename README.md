# OCR CCCD API

API nhận dạng và trích xuất thông tin từ hình ảnh Căn cước công dân Việt Nam.

## Tính năng

- Nhận dạng văn bản từ hình ảnh CCCD
- Trích xuất thông tin: số CCCD, họ tên, ngày sinh, giới tính, quốc tịch, quê quán, nơi thường trú, ngày cấp, nơi cấp
- Giao diện web thân thiện với người dùng
- Hỗ trợ kéo thả file
- Hiển thị kết quả trực quan

## Cài đặt

1. Clone repository:
```bash
git clone <repository-url>
cd ocr_api_cccd
```

2. Tạo môi trường ảo và cài đặt dependencies:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
.\venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

3. Chạy ứng dụng:
```bash
uvicorn main:app --reload
```

4. Truy cập http://localhost:8000 để sử dụng giao diện web

## API Endpoints

- `GET /`: Giao diện web
- `POST /api/ocr_cccd/`: API trích xuất thông tin từ hình ảnh CCCD

## Công nghệ sử dụng

- FastAPI
- EasyOCR
- HTML/CSS/JavaScript
- Jinja2 Templates

## Cấu trúc dự án

```
ocr_api_cccd/
├── app/
│   ├── api/
│   │   └── routes.py
│   │   
│   │   └── services/
│   │       └── ocr_service.py
│   ├── models/
│   │   └── response.py
│   ├── static/
│   │   ├── style.css
│   │   ├── script.js
│   │   └── upload-icon.png
│   ├── templates/
│   │   └── index.html
│   ├── main.py
│   ├── requirements.txt
│   └── README.md
```

## Đóng góp

Mọi đóng góp đều được hoan nghênh! Vui lòng tạo issue hoặc pull request để đóng góp.

## Giấy phép

MIT License