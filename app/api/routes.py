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

# Khởi tạo EasyOCR
reader = easyocr.Reader(['vi'], gpu=torch.cuda.is_available())

# Khởi tạo LLaMA model
model_path = "./models/Vintern-1B-v3_5-f16.gguf"
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

        # Xử lý ảnh với EasyOCR
        results = reader.readtext(img_cv)
        raw_ocr_text = ""
        for (bbox, text, prob) in results:
            if prob > 0.5:  # Chỉ lấy text có độ tin cậy > 50%
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
                match = re.search(rf'{keyword}\s*:\s*({pattern})', text, re.IGNORECASE | re.DOTALL)
                if match:
                    return match.group(1).strip()
            return ""

        parsed_data = {
            "id_number": extract_regex(raw_ocr_text, r'\b\d{12}\b'),
            "full_name": extract_field(raw_ocr_text, ["Họ và tên", "Họ tên"], r'[A-ZĐ][a-zđéèêìíòóôùúý]+(?: [A-ZĐ][a-zđéèêìíòóôùúý]+)*'),
            "date_of_birth": extract_field(raw_ocr_text, ["Ngày sinh"], r'\d{2}/\d{2}/\d{4}'),
            "gender": extract_field(raw_ocr_text, ["Giới tính"], r'Nam|Nữ|Khác'),
            "nationality": extract_field(raw_ocr_text, ["Quốc tịch"], r'[A-ZĐ][a-zđéèêìíòóôùúý]+'),
            "place_of_origin": extract_field(raw_ocr_text, ["Quê quán"], r'.*'),
            "permanent_address": extract_field(raw_ocr_text, ["Nơi thường trú"], r'.*'),
            "date_of_issue": extract_field(raw_ocr_text, ["Ngày cấp"], r'\d{2}/\d{2}/\d{4}'),
            "place_of_issue": extract_field(raw_ocr_text, ["Nơi cấp"], r'.*')
        }
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
            temperature=0.7,
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