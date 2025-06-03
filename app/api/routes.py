from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.services.ocr_service import OCRService
from app.models.response import OCRResponse
from llama_cpp import Llama
import logging
import io
import cv2
import numpy as np
from PIL import Image
import json
import re
import torch
import easyocr

router = APIRouter()
ocr_service = OCRService()

# Khởi tạo EasyOCR với cấu hình cơ bản
reader = easyocr.Reader(
    ['vi'],
    gpu=torch.cuda.is_available(),
    download_enabled=True,
    model_storage_directory='./models',
    user_network_directory='./models',
    recog_network='latin_g2',
    detector=True,
    recognizer=True,
    verbose=False
)

# Khởi tạo LLaMA model
model_path = "./models/Vintern-1B-v3_5-f16_q4_k.gguf"
try:
    llm = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_gpu_layers=-1 if torch.cuda.is_available() else 0,
        verbose=False
    )
    print(f"Loaded LLaMA model from {model_path} successfully.")
except Exception as e:
    print(f"Error loading LLaMA model: {e}")
    llm = None

def is_cccd_image(image):
    """
    Kiểm tra xem ảnh có phải là CCCD hay không dựa trên các đặc điểm:
    1. Tỷ lệ khung hình (aspect ratio)
    2. Các từ khóa đặc trưng
    3. Số CCCD
    """
    try:
        # Chuyển đổi ảnh sang grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 1. Kiểm tra tỷ lệ khung hình
        height, width = image.shape[:2]
        aspect_ratio = width / height
        if not (1.4 <= aspect_ratio <= 1.7):  # Tỷ lệ chuẩn của CCCD
            return False, "Tỷ lệ khung hình không phù hợp với CCCD"

        # 3. Kiểm tra các từ khóa đặc trưng
        results = reader.readtext(image)
        text = " ".join([r[1] for r in results])
        text = text.lower()
        
        required_keywords = ["căn cước", "công dân", "họ và tên", "ngày sinh", "giới tính"]
        found_keywords = sum(1 for keyword in required_keywords if keyword in text)
        
        if found_keywords < 3:  # Cần ít nhất 3 từ khóa
            return False, "Không tìm thấy đủ từ khóa đặc trưng của CCCD"

        # 4. Kiểm tra số CCCD
        if not re.search(r'\b\d{12}\b', text):
            return False, "Không tìm thấy số CCCD hợp lệ"

        return True, "Đây là ảnh CCCD hợp lệ"

    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra CCCD: {str(e)}")
        return False, f"Lỗi khi kiểm tra CCCD: {str(e)}"

@router.get("/")
async def read_root():
    return {"message": "API for CCCD OCR processing"}

@router.post("/ocr_cccd/")
async def ocr_cccd(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

    try:
        contents = await file.read()
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
        img_np = np.array(pil_image)
        img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        # Kiểm tra xem có phải là CCCD không
        is_valid, message = is_cccd_image(img_cv)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)

        # Xử lý ảnh với EasyOCR
        results = reader.readtext(img_cv)
        raw_ocr_text = ""
        for (bbox, text, prob) in results:
            if prob > 0.3:  # Chỉ lấy text có độ tin cậy > 30%
                raw_ocr_text += text + "\n"

        if not raw_ocr_text.strip():
            raise HTTPException(status_code=404, detail="No text detected by OCR.")

        print(f"Raw OCR Text:\n{raw_ocr_text}")

        # Trích xuất thông tin bằng regex
        def extract_regex(text, pattern):
            match = re.search(pattern, text, re.IGNORECASE)
            return match.group(0) if match else ""

        def extract_field(text, keywords, pattern):
            for keyword in keywords:
                # Tìm dòng chứa keyword
                lines = text.split('\n')
                for line in lines:
                    if keyword.lower() in line.lower():
                        # Tìm giá trị sau keyword
                        match = re.search(rf'{keyword}\s*[:|]\s*({pattern})', line, re.IGNORECASE | re.DOTALL)
                        if match:
                            return match.group(1).strip()
                        # Nếu không tìm thấy giá trị sau keyword, tìm ở dòng tiếp theo
                        idx = lines.index(line)
                        if idx + 1 < len(lines):
                            next_line = lines[idx + 1]
                            match = re.search(rf'({pattern})', next_line, re.IGNORECASE | re.DOTALL)
                            if match:
                                return match.group(1).strip()
            return ""

        # Cải thiện pattern cho từng trường
        parsed_data = {
            "id_number": extract_regex(raw_ocr_text, r'\b\d{12}\b'),
            "full_name": extract_field(raw_ocr_text, ["Họ và tên", "Họ tên", "Full name"], r'[A-ZĐ][A-ZĐa-zđéèêìíòóôùúý]+(?:\s+[A-ZĐ][A-ZĐa-zđéèêìíòóôùúý]+)*'),
            "date_of_birth": extract_field(raw_ocr_text, ["Ngày sinh"], r'\d{2}/\d{2}/\d{4}'),
            "gender": extract_field(raw_ocr_text, ["Giới tính"], r'Nam|Nữ|Khác'),
            "nationality": extract_field(raw_ocr_text, ["Quốc tịch"], r'[A-ZĐ][a-zđéèêìíòóôùúý]+'),
            "place_of_origin": extract_field(raw_ocr_text, ["Quê quán"], r'.*?(?=\n|$)'),
            "permanent_address": extract_field(raw_ocr_text, ["Nơi thường trú"], r'.*?(?=\n|$)'),
            "date_of_issue": extract_field(raw_ocr_text, ["Ngày cấp"], r'\d{2}/\d{2}/\d{4}'),
            "place_of_issue": extract_field(raw_ocr_text, ["Nơi cấp"], r'.*?(?=\n|$)')
        }

        # Xử lý kết quả
        for key, value in parsed_data.items():
            if value:
                # Loại bỏ các ký tự đặc biệt không cần thiết
                value = re.sub(r'[^\w\s/.,-]', '', value)
                # Loại bỏ khoảng trắng thừa
                value = ' '.join(value.split())
                parsed_data[key] = value

        # Đặc biệt xử lý cho trường họ tên
        if "full_name" in parsed_data:
            # Tìm dòng chứa "Họ và tên" hoặc "Full name"
            lines = raw_ocr_text.split('\n')
            for i, line in enumerate(lines):
                if "Họ và tên" in line or "Full name" in line:
                    # Lấy dòng tiếp theo nếu có
                    if i + 1 < len(lines):
                        name = lines[i + 1].strip()
                        # Loại bỏ các ký tự đặc biệt và khoảng trắng thừa
                        name = re.sub(r'[^\w\s]', '', name)
                        name = ' '.join(name.split())
                        if name:
                            parsed_data["full_name"] = name
                            break

        # Chỉ giữ lại các trường có giá trị
        parsed_data = {k: v for k, v in parsed_data.items() if v}

        return JSONResponse(content={"status": "success", "extracted_data": parsed_data})

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/ocr", response_model=OCRResponse)
async def process_image(file: UploadFile = File(...)):
    """
    Xử lý hình ảnh và trích xuất văn bản
    """
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File phải là hình ảnh")
        
        # Đọc nội dung file
        contents = await file.read()
        
        # Xử lý OCR
        result = await ocr_service.process_image(contents)
        
        return OCRResponse(
            success=True,
            text=result,
            message="Xử lý thành công"
        )
    except Exception as e:
        logging.error(f"Lỗi khi xử lý hình ảnh: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-text")
async def process_text(text: str):
    """
    Xử lý văn bản với LLaMA model
    """
    try:
        # Tạo prompt
        prompt = f"Xử lý văn bản sau: {text}"
        
        # Sinh văn bản với LLaMA
        output = llm(
            prompt,
            max_tokens=512,
            temperature=0.8,
            top_p=0.95,
            stop=["User:", "\n"],
            echo=True
        )
        
        return {
            "success": True,
            "result": output["choices"][0]["text"],
            "message": "Xử lý thành công"
        }
    except Exception as e:
        logging.error(f"Lỗi khi xử lý văn bản: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 