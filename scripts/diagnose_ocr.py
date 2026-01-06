#!/usr/bin/env python3
"""Diagnostic script to check OCR output for vendor name extraction issues."""

import asyncio
import sys
from pathlib import Path

from ingestion.image_processor import process_image


async def diagnose_ocr(file_path: str):
    """Diagnose OCR output for a specific invoice file."""
    path = Path(file_path)
    
    if not path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"🔍 Analyzing OCR output for: {file_path}")
    print("=" * 80)
    
    # Run OCR
    result = await process_image(path)
    
    raw_text = result.get("text", "")
    metadata = result.get("metadata", {})
    
    print(f"\n📊 OCR Metadata:")
    print(f"   Processor: {metadata.get('processor', 'unknown')}")
    print(f"   Average Confidence: {metadata.get('avg_confidence', 0):.2%}")
    print(f"   Line Count: {metadata.get('line_count', 0)}")
    print(f"   Text Length: {len(raw_text)} characters")
    
    print(f"\n📝 Extracted Text (first 2000 chars):")
    print("-" * 80)
    print(raw_text[:2000])
    if len(raw_text) > 2000:
        print(f"\n... (truncated, total {len(raw_text)} characters)")
    print("-" * 80)
    
    # Check for Chinese vendor-related keywords
    print(f"\n🔎 Vendor Name Detection:")
    vendor_keywords = ["销售方", "购买方", "示例商贸公司", "DeepSeek", "科技有限公司"]
    found_keywords = []
    
    for keyword in vendor_keywords:
        if keyword in raw_text:
            found_keywords.append(keyword)
            # Find context around the keyword
            idx = raw_text.find(keyword)
            start = max(0, idx - 50)
            end = min(len(raw_text), idx + len(keyword) + 50)
            context = raw_text[start:end].replace("\n", " ")
            print(f"   ✅ Found '{keyword}' in text")
            print(f"      Context: ...{context}...")
    
    if not found_keywords:
        print("   ❌ No vendor-related keywords found in OCR output!")
        print("   This suggests PaddleOCR may not be extracting the text correctly.")
    else:
        print(f"   ✅ Found {len(found_keywords)} vendor-related keyword(s)")
    
    # Check if "销售方" is present (seller field)
    if "销售方" in raw_text:
        print(f"\n✅ '销售方' (seller) field detected in OCR output")
        # Try to extract what comes after 销售方
        idx = raw_text.find("销售方")
        after_seller = raw_text[idx:idx+100].replace("\n", " ")
        print(f"   Text after '销售方': {after_seller}")
    else:
        print(f"\n❌ '销售方' (seller) field NOT found in OCR output")
        print(f"   This is likely an OCR issue - PaddleOCR may not be reading this field correctly")
    
    print("\n" + "=" * 80)
    print("\n💡 Diagnosis:")
    if "销售方" not in raw_text:
        print("   ⚠️  ISSUE: PaddleOCR is not extracting the '销售方' field from the invoice.")
        print("   Possible causes:")
        print("   1. Image quality/resolution issues")
        print("   2. Font/styling that PaddleOCR struggles with")
        print("   3. Layout complexity (text in unusual positions)")
        print("   4. PaddleOCR model limitations for this specific invoice format")
        print("\n   Solutions:")
        print("   1. Try preprocessing the image (enhance contrast, resize)")
        print("   2. Use a different OCR engine (e.g., EasyOCR, Tesseract)")
        print("   3. Use Docling for PDFs instead of PaddleOCR for images")
    elif not any(kw in raw_text for kw in ["示例商贸公司", "DeepSeek"]):
        print("   ⚠️  ISSUE: OCR extracted '销售方' but vendor name text may be garbled or missing")
        print("   The LLM extraction may be failing to parse the vendor name correctly.")
    else:
        print("   ✅ OCR appears to be working correctly.")
        print("   The issue is likely in the LLM extraction phase, not OCR.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/diagnose_ocr.py <path_to_invoice_image>")
        print("Example: python scripts/diagnose_ocr.py data/jimeng/invoice-4.png")
        sys.exit(1)
    
    file_path = sys.argv[1]
    asyncio.run(diagnose_ocr(file_path))

