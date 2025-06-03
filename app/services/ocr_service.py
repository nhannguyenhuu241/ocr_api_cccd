import easyocr
import numpy as np
import cv2
from io import BytesIO
from PIL import Image
import logging

class OCRService:
    def __init__(self):
        # Khởi tạo EasyOCR với ngôn ngữ tiếng Việt
        self.reader = easyocr.Reader(['vi'])
        
    async def process_image(self, image_bytes: bytes) -> str:
        """
        Xử lý hình ảnh và trích xuất văn bản
        """
        try:
            # Chuyển đổi bytes thành numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Tiền xử lý hình ảnh
            img = self._preprocess_image(img)
            
            # Thực hiện OCR
            results = self.reader.readtext(img)
            
            # Kết hợp các kết quả
            text = ' '.join([result[1] for result in results])
            
            return text
            
        except Exception as e:
            logging.error(f"Lỗi trong quá trình xử lý OCR: {str(e)}")
            raise
    
    def _preprocess_image(self, img):
        """
        Tiền xử lý hình ảnh để cải thiện kết quả OCR
        """
        # Chuyển đổi sang grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Áp dụng adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Khử nhiễu
        denoised = cv2.fastNlMeansDenoising(thresh)
        
        return denoised 