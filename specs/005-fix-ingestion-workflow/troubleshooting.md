# Troubleshooting OCR Timeout Issues

## Problem
OCR processing is timing out for images, even with increased timeouts.

## Common Causes

1. **First-time model loading**: PaddleOCR needs to load models on first use (30-60 seconds)
2. **Large/complex images**: High-resolution or complex images take longer to process
3. **System resources**: Insufficient CPU/memory can slow down processing
4. **PaddleOCR unresponsiveness**: The OCR engine may hang on certain images

## Solutions

### 1. Pre-initialize OCR Engine
Initialize PaddleOCR at application startup to avoid first-time delays:

```python
# In interface/api/main.py lifespan
async def preload_ocr():
    """Pre-initialize OCR engine at startup."""
    try:
        from ingestion.image_processor import get_ocr_engine
        await get_ocr_engine()
        logger.info("OCR engine pre-initialized")
    except Exception as e:
        logger.warning("Failed to pre-initialize OCR engine", error=str(e))
```

### 2. Use Smaller Images
- Resize images before processing
- Use image compression
- Process images in batches

### 3. Increase System Resources
- Ensure sufficient RAM (PaddleOCR uses 2-4GB)
- Use a machine with more CPU cores
- Consider using GPU acceleration (if available)

### 4. Alternative: Skip OCR for Large Images
For very large images, consider:
- Using a different OCR library
- Processing images in chunks
- Using a cloud OCR service

## Current Timeout Settings

- Default: 180 seconds (3 minutes)
- Large images (>2MB): 45 seconds per MB, max 10 minutes
- First request: May take longer due to model loading

## Monitoring

Check invoice error messages:
```bash
python scripts/check_invoice_status.py <invoice_id>
```

Check API logs for detailed timing information.

