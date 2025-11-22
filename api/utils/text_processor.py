import os
import shutil
import pytesseract
from PIL import Image
import io


class TextProcessor:
    @staticmethod
    def _tesseract_available():
        # Support env variable or fallback
        cmd = os.environ.get("TESSERACT_CMD")
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd

    @staticmethod
    def extract_text_from_image(image_file):
        TextProcessor._tesseract_available()

        if not TextProcessor._tesseract_available():
            print("OCR Error: tesseract is not installed or not in PATH.")
            return ""

        try:
            image = Image.open(io.BytesIO(image_file.read()))
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

    @staticmethod
    def preprocess_text(text):
        text = " ".join(text.split())
        return text
