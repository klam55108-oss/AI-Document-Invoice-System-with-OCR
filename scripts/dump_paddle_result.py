from paddleocr import PaddleOCR
from pathlib import Path

def dump_result(file_path):
    ocr = PaddleOCR(use_angle_cls=True, lang="ch")
    result = ocr.ocr(str(file_path))
    print("RESULT TYPE:", type(result))
    if result:
        res0 = result[0]
        print("RESULT[0] TYPE:", type(res0))
        print("ATTRIBUTES:", dir(res0))
        # If it has 'rec_res', it might be the recognition results
        if hasattr(res0, 'rec_res'):
            print("REC_RES:", res0.rec_res)
        # Often there's a __str__ or to_dict
        try:
            print("STR representation:", str(res0))
        except:
            pass

dump_result("data/grok/9.png")
