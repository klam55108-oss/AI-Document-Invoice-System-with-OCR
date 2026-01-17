"""Image processing using configurable OCR providers."""

import asyncio
import base64
import os
import tempfile
from mimetypes import guess_type
from pathlib import Path
from typing import Any
from PIL import Image

from core.config import settings
from core.logging import get_logger
from core.ocr.configuration import resolve_provider

logger = get_logger(__name__)

# Initialize PaddleOCR (CPU mode by default for compatibility)
# This will download the models on first use
_ocr_engine = None
_ocr_lock = asyncio.Lock()
_ocr_initializing = False
_memory_threshold_mb = 1024  # Minimum free memory recommended (1GB)
_critical_memory_threshold_mb = 300  # Critical threshold to avoid OS kill (300MB)
_ocr_semaphore = asyncio.Semaphore(1)  # Strictly limit to 1 concurrent OCR task


def check_system_resources() -> tuple[bool, str]:
    """Check if the system has enough resources to run OCR.

    Returns:
        A tuple of (is_healthy, status_message)
    """
    try:
        import psutil
        vm = psutil.virtual_memory()
        free_mb = vm.available / (1024 * 1024)
        
        if free_mb < _memory_threshold_mb:
            msg = f"Low memory: {free_mb:.1f}MB available, recommendation: at least {_memory_threshold_mb}MB"
            logger.warning(msg)
            return False, msg
            
        return True, f"System resources healthy: {free_mb:.1f}MB available"
    except ImportError:
        # psutil not installed, skip check
        return True, "Resource check skipped (psutil not installed)"
    except Exception as e:
        logger.warning(f"Failed to check system resources: {str(e)}")
        return True, "Resource check failed"


def _init_ocr_engine_sync(lang: str = "ch"):
    """Synchronous PaddleOCR initialization (runs in thread pool).
    
    This function should NOT be called directly from async code.
    Use get_ocr_engine() instead.
    """
    global _ocr_engine
    try:
        import os
        import warnings
        from contextlib import redirect_stderr, redirect_stdout
        from io import StringIO
        
        # Disable model source connectivity check to speed up initialization
        os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")
        # Optimization for CPU execution
        os.environ.setdefault("OMP_NUM_THREADS", "1")
        os.environ.setdefault("MKL_NUM_THREADS", "1")
        
        logger.info("Initializing PaddleOCR engine (this may take 30-60 seconds)", lang=lang)
        
        # Suppress warnings during initialization
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            # Redirect verbose output to null to suppress PaddleOCR model loading messages
            null_stream = StringIO()
            try:
                with redirect_stderr(null_stream), redirect_stdout(null_stream):
                    from paddleocr import PaddleOCR
                    # Use only widely supported arguments, others via kwargs if possible
                    # In this environment, use_gpu/show_log seem to cause issues
                    # Disabling extra features to save memory
                    init_args = {
                        "use_textline_orientation": False,
                        "use_doc_orientation_classify": False,
                        "use_doc_unwarping": False,
                        "lang": lang
                    }
                    _ocr_engine = PaddleOCR(**init_args)
            except Exception as init_error:
                # If redirect fails or engine init fails, try simpler config
                logger.warning("Preferred OCR initialization failed, trying fallback", error=str(init_error))
                from paddleocr import PaddleOCR
                _ocr_engine = PaddleOCR(
                    use_textline_orientation=True,
                    lang=lang,
                    use_gpu=False
                )
        
        logger.info("PaddleOCR engine initialized successfully", lang=lang)
        return _ocr_engine
    except ImportError:
        error_msg = "PaddleOCR library is not installed. Please install it with: pip install paddleocr"
        logger.error("PaddleOCR not installed", error=error_msg)
        raise RuntimeError(error_msg) from None
    except Exception as e:
        try:
            # Fallback to simpler config
            from paddleocr import PaddleOCR
            _ocr_engine = PaddleOCR(
                use_textline_orientation=False,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                lang=lang
            )
            logger.info("PaddleOCR initialized with fallback arguments")
            return _ocr_engine
        except Exception as fallback_error:
            error_msg = f"PaddleOCR initialization failed: {str(e)}. Fallback also failed: {str(fallback_error)}"
            logger.error("PaddleOCR initialization failed", error=error_msg)
            raise RuntimeError(error_msg) from e


def resize_image_for_ocr(file_path: Path, max_size: int = 1500) -> str:
    """Resize image to a smaller size to reduce memory usage during OCR.
    
    Returns:
        Path to the resized temporary image, or the original path if no resizing needed.
    """
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            if max(width, height) <= max_size:
                return str(file_path)
            
            # Calculate new size
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            
            # Create temp file
            temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            # Resize and save
            logger.info("Resizing image for OCR", original_size=(width, height), new_size=(new_width, new_height))
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            resized_img.save(temp_path, format="PNG")
            return temp_path
    except Exception as e:
        logger.warning(f"Failed to resize image for OCR: {str(e)}. Using original.")
        return str(file_path)


async def get_ocr_engine(lang: str = "ch"):
    """Lazy initialization of the OCR engine (non-blocking).
    
    This function runs PaddleOCR initialization in a thread pool to avoid
    blocking the async event loop. Initialization is thread-safe and only
    happens once using an asyncio.Lock.
    
    Args:
        lang: Language code for OCR. Default "ch" (Chinese) supports both Chinese and English.
              Use "en" for English-only, "ch" for Chinese (which also handles English).
    
    Returns:
        PaddleOCR engine instance
        
    Raises:
        RuntimeError: If PaddleOCR is not available or cannot be initialized
    """
    global _ocr_engine, _ocr_initializing
    
    # Fast path: already initialized
    if _ocr_engine is not None:
        return _ocr_engine
    
    # Async lock ensures only one coro initializes the engine
    async with _ocr_lock:
        # Double-check after acquiring lock
        if _ocr_engine is not None:
            return _ocr_engine
        
        # Mark as initializing
        _ocr_initializing = True
        
        try:
            logger.info("Starting PaddleOCR initialization in thread pool...")
            # Run initialization in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            # Note: _init_ocr_engine_sync is a CPU-bound task
            _ocr_engine = await loop.run_in_executor(None, _init_ocr_engine_sync, lang)
            return _ocr_engine
        except Exception as e:
            logger.error("Failed to initialize PaddleOCR in thread pool", error=str(e))
            raise
        finally:
            _ocr_initializing = False


async def process_image(file_path: Path, provider_id: str | None = None) -> dict[str, Any]:
    """Process image file using selected OCR provider.

    Args:
        file_path: Path to image file
        provider_id: Optional OCR provider override

    Returns:
        Dictionary with extracted text and metadata
    """
    resolved_provider = resolve_provider(provider_id)
    if resolved_provider == "paddleocr":
        return await _process_image_with_paddleocr(file_path)
    if resolved_provider == "deepseek-ocr":
        return await _process_image_with_deepseek(file_path)
    raise ValueError(f"Unsupported OCR provider: {resolved_provider}")


async def _process_image_with_paddleocr(file_path: Path) -> dict[str, Any]:
    """Process image file using PaddleOCR to extract text.

    Args:
        file_path: Path to image file

    Returns:
        Dictionary with extracted text and metadata
    """
    # Validate file exists before attempting OCR (saves resources)
    if not file_path.exists():
        error_msg = f"Image file not found: {file_path}"
        logger.error("OCR processing failed - file not found", path=str(file_path), error=error_msg)
        raise FileNotFoundError(error_msg)
    
    # Check file size to avoid processing empty or corrupted files
    try:
        file_size = file_path.stat().st_size
        if file_size == 0:
            error_msg = f"Image file is empty: {file_path}"
            logger.error("OCR processing failed - empty file", path=str(file_path), error=error_msg)
            raise ValueError(error_msg)
        if file_size > 100 * 1024 * 1024:  # 100MB limit
            error_msg = f"Image file too large: {file_size} bytes (max 100MB)"
            logger.error("OCR processing failed - file too large", path=str(file_path), error=error_msg)
            raise ValueError(error_msg)
    except OSError as e:
        error_msg = f"Cannot access image file: {file_path} - {str(e)}"
        logger.error("OCR processing failed - file access error", path=str(file_path), error=error_msg)
        raise OSError(error_msg) from e
    
    logger.info("Starting OCR processing", path=str(file_path), file_size=file_size)

    # Check system resources before starting OCR
    is_healthy, resource_msg = check_system_resources()
    if not is_healthy:
        try:
            import psutil
            free_mb = psutil.virtual_memory().available / (1024 * 1024)
            if free_mb < _critical_memory_threshold_mb:
                error_msg = f"Critically low memory: {free_mb:.1f}MB available. OCR aborted to prevent system crash."
                logger.error(resource_msg)
                raise RuntimeError(error_msg)
        except (ImportError, Exception):
            pass
        logger.warning("Starting OCR despite low resources", resource_status=resource_msg)
    else:
        logger.info(resource_msg)

    # Resize image to reduce memory pressure if it's large
    ocr_input_path = resize_image_for_ocr(file_path)
    is_temporary = ocr_input_path != str(file_path)

    try:
        # Get OCR engine (non-blocking initialization)
        ocr = await get_ocr_engine()
        
        # Run OCR in thread pool since it's CPU-intensive and blocking
        loop = asyncio.get_event_loop()
        
        def run_ocr():
            """Run OCR in thread pool."""
            import time
            start_time = time.time()
            try:
                # PaddleOCR expects string path or numpy array
                # Some versions use predict(), older use ocr()
                logger.info("Calling PaddleOCR", path=ocr_input_path, method="predict" if hasattr(ocr, "predict") else "ocr")
                if hasattr(ocr, "predict"):
                    result = ocr.predict(ocr_input_path)
                else:
                    result = ocr.ocr(ocr_input_path)
                elapsed = time.time() - start_time
                logger.info("PaddleOCR call completed", path=ocr_input_path, elapsed_seconds=round(elapsed, 2))
                return result
            except Exception as ocr_error:
                elapsed = time.time() - start_time
                logger.error("PaddleOCR call failed", path=ocr_input_path, error=str(ocr_error), elapsed_seconds=round(elapsed, 2))
                raise
        
        # Run OCR with timeout (configurable, default 300 seconds for first-time processing)
        # First-time processing may take longer due to model loading and warmup
        ocr_timeout = 300.0  # 5 minutes - increased to account for model loading
        
        # Increase timeout for larger images (roughly 60 seconds per MB)
        if file_size > 2 * 1024 * 1024:  # > 2MB
            ocr_timeout = max(ocr_timeout, (file_size / (1024 * 1024)) * 60)
            ocr_timeout = min(ocr_timeout, 900.0)  # Cap at 15 minutes for very large images
        
        try:
            logger.info("Acquiring OCR semaphore...", path=str(file_path))
            async with _ocr_semaphore:
                logger.info("Starting OCR processing", path=str(file_path), timeout_seconds=ocr_timeout, file_size_mb=round(file_size/(1024*1024), 2))
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, run_ocr),
                    timeout=ocr_timeout
                )
        except asyncio.TimeoutError:
            error_msg = f"OCR processing timed out after {ocr_timeout} seconds. The image may be too large, complex, or PaddleOCR may be unresponsive. Try a smaller image or check system resources."
            logger.error("OCR processing timeout", path=str(file_path), timeout=ocr_timeout, file_size=file_size, file_size_mb=round(file_size/(1024*1024), 2))
            raise RuntimeError(error_msg) from None

        if not result:
            logger.warning("OCR returned no results", path=str(file_path))
        return {
            "text": "",
            "metadata": {
                "file_path": str(file_path),
                "processor": "paddleocr",
                "status": "no_text_found",
            },
        }

        extracted_text = []
        confidences = []

        # Handle different result structures
        res0 = result[0]
        
        # New OCRResult object from PaddleX/PaddleOCR newer versions
        # It often behaves like a dict or has these attributes
        if hasattr(res0, "rec_texts") and hasattr(res0, "rec_scores"):
            extracted_text = res0.rec_texts
            confidences = [float(c) for c in res0.rec_scores]
        elif isinstance(res0, dict) and "rec_texts" in res0 and "rec_scores" in res0:
            extracted_text = res0["rec_texts"]
            confidences = [float(c) for c in res0["rec_scores"]]
        # Legacy list-of-lists structure: [ [[ [coords], (text, confidence) ], ...] ]
        elif isinstance(res0, list):
            for line in res0:
                if len(line) > 1 and isinstance(line[1], (tuple, list)):
                    text, confidence = line[1]
                    extracted_text.append(text)
                    confidences.append(float(confidence))
        else:
            logger.warning("Unknown OCR result structure", type=str(type(res0)))

        full_text = "\n".join(extracted_text)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        logger.info(
            "OCR processing completed",
            path=str(file_path),
            text_length=len(full_text),
            confidence=avg_confidence,
        )

        return {
            "text": full_text,
            "metadata": {
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "processor": "paddleocr",
                "avg_confidence": avg_confidence,
                "line_count": len(extracted_text),
                "was_resized": is_temporary,
            },
        }

    except ImportError as e:
        error_msg = f"OCR library not available: {str(e)}. Please install PaddleOCR."
        logger.error("OCR processing failed - library not available", path=str(file_path), error=error_msg)
        raise RuntimeError(error_msg) from e
    except FileNotFoundError as e:
        error_msg = f"Image file not found: {file_path}"
        logger.error("OCR processing failed - file not found", path=str(file_path), error=error_msg)
        raise FileNotFoundError(error_msg) from e
    except Exception as e:
        error_type = type(e).__name__
        error_msg = f"OCR processing failed: {str(e)}"
        logger.error(
            "OCR processing failed",
            path=str(file_path),
            error_type=error_type,
            error=str(e),
            exc_info=True,
        )
        # Re-raise with context for orchestrator to handle
        raise RuntimeError(f"Image processing failed ({error_type}): {str(e)}") from e
    finally:
        # Cleanup temporary file if created
        if "is_temporary" in locals() and is_temporary and "ocr_input_path" in locals() and os.path.exists(ocr_input_path):
            try:
                os.unlink(ocr_input_path)
                logger.debug("Cleaned up temporary OCR input file", path=ocr_input_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temporary OCR input file: {str(cleanup_error)}")


def _build_image_data_url(file_path: Path) -> str:
    mime_type, _ = guess_type(str(file_path))
    if not mime_type:
        mime_type = "application/octet-stream"
    encoded = base64.b64encode(file_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _run_deepseek_ocr_sync(image_path: Path) -> str:
    import openai

    api_key = settings.DEEPSEEK_API_KEY or settings.OPENAI_API_KEY
    if not api_key:
        raise RuntimeError("DeepSeek OCR requires DEEPSEEK_API_KEY or OPENAI_API_KEY")

    client = openai.OpenAI(
        api_key=api_key,
        base_url=settings.DEEPSEEK_OCR_BASE_URL,
    )
    prompt = (
        "Extract all visible text from this image. "
        "Return plain text only, preserving line breaks when possible."
    )
    response = client.chat.completions.create(
        model=settings.DEEPSEEK_OCR_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": _build_image_data_url(image_path)}},
                ],
            }
        ],
        temperature=0.0,
    )
    return response.choices[0].message.content or ""


async def _process_image_with_deepseek(file_path: Path) -> dict[str, Any]:
    """Process image file using DeepSeek OCR (remote, CPU-only).

    Args:
        file_path: Path to image file

    Returns:
        Dictionary with extracted text and metadata
    """
    # Validate file exists before attempting OCR (saves resources)
    if not file_path.exists():
        error_msg = f"Image file not found: {file_path}"
        logger.error("OCR processing failed - file not found", path=str(file_path), error=error_msg)
        raise FileNotFoundError(error_msg)

    # Check file size to avoid processing empty or corrupted files
    try:
        file_size = file_path.stat().st_size
        if file_size == 0:
            error_msg = f"Image file is empty: {file_path}"
            logger.error("OCR processing failed - empty file", path=str(file_path), error=error_msg)
            raise ValueError(error_msg)
        if file_size > 25 * 1024 * 1024:  # 25MB limit for API payloads
            error_msg = f"Image file too large: {file_size} bytes (max 25MB)"
            logger.error("OCR processing failed - file too large", path=str(file_path), error=error_msg)
            raise ValueError(error_msg)
    except OSError as e:
        error_msg = f"Cannot access image file: {file_path} - {str(e)}"
        logger.error("OCR processing failed - file access error", path=str(file_path), error=error_msg)
        raise OSError(error_msg) from e

    logger.info("Starting DeepSeek OCR processing", path=str(file_path), file_size=file_size)

    # Resize image to reduce memory pressure if it's large
    ocr_input_path = resize_image_for_ocr(file_path)
    is_temporary = ocr_input_path != str(file_path)

    try:
        loop = asyncio.get_event_loop()
        ocr_timeout = settings.OCR_TIMEOUT_SECONDS
        if file_size > 2 * 1024 * 1024:
            ocr_timeout = max(ocr_timeout, (file_size / (1024 * 1024)) * 30)

        async with _ocr_semaphore:
            text = await asyncio.wait_for(
                loop.run_in_executor(None, _run_deepseek_ocr_sync, Path(ocr_input_path)),
                timeout=ocr_timeout,
            )

        if not text:
            logger.warning("DeepSeek OCR returned no results", path=str(file_path))
            return {
                "text": "",
                "metadata": {
                    "file_path": str(file_path),
                    "processor": "deepseek-ocr",
                    "status": "no_text_found",
                },
            }

        logger.info(
            "DeepSeek OCR processing completed",
            path=str(file_path),
            text_length=len(text),
        )

        return {
            "text": text,
            "metadata": {
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "processor": "deepseek-ocr",
                "was_resized": is_temporary,
            },
        }
    except asyncio.TimeoutError:
        error_msg = f"DeepSeek OCR timed out after {settings.OCR_TIMEOUT_SECONDS} seconds"
        logger.error("DeepSeek OCR processing timeout", path=str(file_path), timeout=settings.OCR_TIMEOUT_SECONDS)
        raise RuntimeError(error_msg) from None
    except Exception as e:
        error_type = type(e).__name__
        error_msg = f"DeepSeek OCR processing failed: {str(e)}"
        logger.error(
            "DeepSeek OCR processing failed",
            path=str(file_path),
            error_type=error_type,
            error=str(e),
            exc_info=True,
        )
        raise RuntimeError(f"Image processing failed ({error_type}): {str(e)}") from e
    finally:
        if "is_temporary" in locals() and is_temporary and "ocr_input_path" in locals() and os.path.exists(ocr_input_path):
            try:
                os.unlink(ocr_input_path)
                logger.debug("Cleaned up temporary OCR input file", path=ocr_input_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temporary OCR input file: {str(cleanup_error)}")

