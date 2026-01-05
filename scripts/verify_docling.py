import asyncio
from pathlib import Path
from ingestion.pdf_processor import process_pdf
from brain.extractor import extract_invoice_data
import json

async def test_processing():
    # Note: Replace with a real PDF path if available for local testing
    # For now, we simulate the path to verify the logic flow
    test_pdf = Path("data/sample_invoice.pdf")
    
    if not test_pdf.exists():
        print(f"Test PDF not found at {test_pdf}, skipping actual conversion but verifying imports.")
        return

    print(f"Processing {test_pdf}...")
    result = await process_pdf(test_pdf)
    
    print("\n--- Docling Result ---")
    print(f"Pages: {result['pages']}")
    print(f"Tables found: {len(result.get('tables', []))}")
    print(f"Text length: {len(result['text'])}")
    print(f"Metadata: {json.dumps(result['metadata'], indent=2)}")
    
    if result.get('tables'):
        print("\n--- First Table ---")
        print(result['tables'][0])

    print("\n--- Extracting Data ---")
    extracted = await extract_invoice_data(result['text'], result)
    
    print("\n--- Extracted Data ---")
    print(f"Vendor: {extracted.vendor_name}")
    print(f"Invoice #: {extracted.invoice_number}")
    print(f"Total: {extracted.total_amount}")
    print(f"Line items count: {len(extracted.line_items)}")

if __name__ == "__main__":
    asyncio.run(test_processing())
