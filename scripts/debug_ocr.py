#!/usr/bin/env python3
"""Consolidated diagnostic script for OCR processing."""

import asyncio
import sys
import argparse
from pathlib import Path

# Add project root to path
import os
sys.path.append(os.getcwd())

from ingestion.image_processor import process_image

async def diagnose_ocr(file_path: Path, timeout: float = 180.0, dump_raw: bool = False):
    """Diagnose OCR output for a specific invoice file."""
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return

    print(f"🔍 Analyzing OCR output for: {file_path}")
    print(f"   File size: {file_path.stat().st_size / 1024:.2f} KB")
    print("=" * 80)
    
    try:
        # Run OCR with timeout
        result = await asyncio.wait_for(
            process_image(file_path),
            timeout=timeout
        )
        
        raw_text = result.get("text", "")
        metadata = result.get("metadata", {})
        
        print(f"✅ OCR processing completed")
        print(f"\n📊 OCR Metadata:")
        print(f"   Processor: {metadata.get('processor', 'unknown')}")
        print(f"   Average Confidence: {metadata.get('avg_confidence', 0):.2%}")
        print(f"   Line Count: {metadata.get('line_count', 0)}")
        print(f"   Text Length: {len(raw_text)} characters")
        
        if dump_raw:
            print(f"\n📝 Full Extracted Text:")
            print("-" * 80)
            print(raw_text)
            print("-" * 80)
        else:
            print(f"\n📝 Extracted Text Preview (first 1000 chars):")
            print("-" * 80)
            print(raw_text[:1000])
            if len(raw_text) > 1000:
                print(f"\n... (truncated, total {len(raw_text)} characters, use --raw to see all)")
            print("-" * 80)
        
        # Keyword detection logic from diagnose_ocr.py
        print(f"\n🔎 Key Field Detection:")
        vendor_keywords = ["销售方", "购买方", "示例商贸公司", "DeepSeek", "科技有限公司"]
        found_keywords = []
        
        for keyword in vendor_keywords:
            if keyword in raw_text:
                found_keywords.append(keyword)
                idx = raw_text.find(keyword)
                start = max(0, idx - 40)
                end = min(len(raw_text), idx + len(keyword) + 40)
                context = raw_text[start:end].replace("\n", " ")
                print(f"   ✅ Found '{keyword}' | Context: ...{context}...")
        
        if "销售方" not in raw_text:
            print("   ❌ '销售方' (seller) field NOT found in OCR output")
            print("   💡 TIP: If this is a PDF, ensure Docling is installed. If an image, PaddleOCR may be failing.")
        
    except asyncio.TimeoutError:
        print(f"❌ OCR processing timed out after {timeout} seconds")
    except Exception as e:
        print(f"❌ OCR processing failed: {type(e).__name__}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Consolidated OCR debugging tool")
    parser.add_argument("file", type=Path, help="Path to the invoice image or PDF")
    parser.add_argument("--timeout", type=float, default=180.0, help="Timeout in seconds (default: 180)")
    parser.add_argument("--raw", action="store_true", help="Print full extracted text")
    parser.add_argument("--paddle-debug", action="store_true", help="Dump raw PaddleOCR structure (if applicable)")
    
    args = parser.parse_args()
    
    if args.paddle_debug:
        # Incorporate logic from dump_paddle_result.py
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang="ch")
            result = ocr.ocr(str(args.file))
            print("\n📦 Raw PaddleOCR Result:")
            print(result)
        except Exception as e:
            print(f"❌ PaddleOCR debug failed: {e}")
        return

    asyncio.run(diagnose_ocr(args.file, timeout=args.timeout, dump_raw=args.raw))

if __name__ == "__main__":
    main()
