try:
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang="ch")
    import inspect
    print("OCR method args:", inspect.signature(ocr.ocr))
except Exception as e:
    print("Error:", e)
