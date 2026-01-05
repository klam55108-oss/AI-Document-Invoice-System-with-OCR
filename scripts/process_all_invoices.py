#!/usr/bin/env python3
"""Script to process all invoice images in the data/ directory."""

import asyncio
import sys
from pathlib import Path

import httpx


async def process_invoice(file_path: str, base_url: str = "http://localhost:8000") -> dict:
    """Process a single invoice file."""
    url = f"{base_url}/api/v1/invoices/process"
    payload = {
        "file_path": file_path,
        "force_reprocess": False,
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"❌ Error processing {file_path}: {e.response.status_code} - {e.response.text}")
            return {"status": "error", "file": file_path}
        except Exception as e:
            print(f"❌ Unexpected error processing {file_path}: {str(e)}")
            return {"status": "error", "file": file_path}


async def process_all_invoices(data_dir: Path = Path("data"), base_url: str = "http://localhost:8000"):
    """Process all invoice images in the data directory."""
    # Find all invoice image files
    invoice_files = sorted(data_dir.glob("invoice-*.png"))
    
    if not invoice_files:
        print(f"❌ No invoice files found in {data_dir}")
        return
    
    print(f"📄 Found {len(invoice_files)} invoice files to process")
    print(f"🌐 API endpoint: {base_url}")
    print("-" * 60)
    
    results = []
    for i, file_path in enumerate(invoice_files, 1):
        relative_path = file_path.name
        print(f"[{i}/{len(invoice_files)}] Processing {relative_path}...", end=" ", flush=True)
        
        result = await process_invoice(relative_path, base_url)
        results.append(result)
        
        if result.get("status") == "success":
            invoice_id = result.get("data", {}).get("invoice_id", "N/A")
            status = result.get("data", {}).get("status", "N/A")
            print(f"✅ Success (ID: {invoice_id[:8]}..., Status: {status})")
        else:
            print(f"❌ Failed")
        
        # Small delay to avoid overwhelming the API
        await asyncio.sleep(0.5)
    
    print("-" * 60)
    print(f"\n📊 Summary:")
    successful = sum(1 for r in results if r.get("status") == "success")
    failed = len(results) - successful
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"\n💡 View results in the dashboard: http://localhost:8501")
    print(f"💡 Or check API: {base_url}/api/v1/invoices")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process all invoice images")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Directory containing invoice files (default: data/)",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)",
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(process_all_invoices(args.data_dir, args.api_url))
    except KeyboardInterrupt:
        print("\n\n⚠️  Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

