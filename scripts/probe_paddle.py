try:
    from paddleocr import PaddleOCR
    import inspect
    print("PaddleOCR args:", inspect.signature(PaddleOCR.__init__))
except Exception as e:
    print("Error:", e)
