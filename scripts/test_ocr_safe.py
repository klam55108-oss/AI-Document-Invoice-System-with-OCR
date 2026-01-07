#!/usr/bin/env python3
"""Test OCR processing with resource limits."""

import asyncio
import sys
from pathlib import Path

from ingestion.image_processor import process_image

async def main():
    """Test OCR processing."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_ocr_safe.py <image_path>")
        sys.exit(1)
    
    image_path = Path(sys.argv[1])
    
    if not image_path.exists():
        print(f"❌ File not found: {image_path}")
        sys.exit(1)
    
    print(f"🔍 Processing image: {image_path}")
    print(f"   File size: {image_path.stat().st_size / 1024:.2f} KB")
    
    try:
        # Set timeout for entire operation (180 seconds for larger images)
        # OCR processing may take longer for larger or complex images
        timeout = 180.0
        if image_path.stat().st_size > 2 * 1024 * 1024:  # > 2MB
            timeout = 300.0  # 5 minutes for larger images
        
        result = await asyncio.wait_for(
            process_image(image_path),
            timeout=timeout
        )
        
        print(f"✅ OCR processing completed")
        print(f"   Text length: {len(result.get('text', ''))} characters")
        print(f"   Lines extracted: {result.get('metadata', {}).get('line_count', 0)}")
        print(f"   Confidence: {result.get('metadata', {}).get('avg_confidence', 0):.2f}")
        
        if result.get('text'):
            print(f"\n📄 Extracted text (first 200 chars):")
            print(result['text'][:200])
        
    except asyncio.TimeoutError:
        print("❌ OCR processing timed out after 90 seconds")
        sys.exit(1)
    except Exception as e:
        print(f"❌ OCR processing failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

