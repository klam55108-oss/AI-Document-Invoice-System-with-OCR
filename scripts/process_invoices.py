#!/usr/bin/env python3
"""Consolidated script to process invoice images from any directory."""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional

import httpx


async def process_invoice(
    relative_path: str, 
    base_url: str = "http://localhost:8000",
    force_reprocess: bool = False,
    category: Optional[str] = None,
    group: Optional[str] = None,
    job_id: Optional[str] = None,
) -> dict:
    """Process a single invoice file."""
    url = f"{base_url}/api/v1/invoices/process"
    payload = {
        "file_path": relative_path,
        "force_reprocess": force_reprocess,
        "category": category,
        "group": group,
        "job_id": job_id,
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"❌ Error processing {relative_path}: {e.response.status_code} - {e.response.text}")
            return {"status": "error", "file": relative_path, "error": str(e)}
        except Exception as e:
            print(f"❌ Unexpected error processing {relative_path}: {str(e)}")
            return {"status": "error", "file": relative_path, "error": str(e)}


async def process_invoices(
    search_dir: Path,
    pattern: str = "*",
    recursive: bool = False,
    base_url: str = "http://localhost:8000",
    force_reprocess: bool = False,
    data_root: Path = Path("data"),
    category: Optional[str] = None,
    group: Optional[str] = None,
):
    """Process invoice images using flexible search criteria."""
    
    # Supported image extensions
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".pdf", ".tiff"}
    
    # Resolve search directory
    if not search_dir.is_absolute():
        search_dir = Path.cwd() / search_dir
        
    if not search_dir.exists():
        print(f"❌ Directory not found: {search_dir}")
        return

    # Find files
    if recursive:
        files = list(search_dir.rglob(pattern))
    else:
        files = list(search_dir.glob(pattern))
        
    # Filter for image/pdf files
    invoice_files = sorted([
        f for f in files 
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ])
    
    if not invoice_files:
        print(f"❌ No matching invoice files found in {search_dir}")
        return
    
    print(f"📄 Found {len(invoice_files)} invoice files to process")
    print(f"🌐 API endpoint: {base_url}")
    print(f"🔄 Force reprocess: {force_reprocess}")
    
    import uuid
    job_id = str(uuid.uuid4())
    print(f"🆔 Job ID: {job_id}")
    print("-" * 60)
    
    results = []
    for i, file_path in enumerate(invoice_files, 1):
        # The API expects path relative to 'data/' directory
        try:
            # Attempt to get path relative to data root if within it
            if file_path.is_relative_to(data_root.absolute()) or file_path.is_relative_to(data_root):
                # Handle cases where data_root is relative or absolute
                try:
                    relative_path = str(file_path.relative_to(data_root.absolute()))
                except ValueError:
                    relative_path = str(file_path.relative_to(data_root))
            else:
                # Fallback to filename if outside data root (API might reject this depending on implementation)
                print(f"⚠️ Warning: {file_path.name} is outside {data_root}. Sending basename.")
                relative_path = file_path.name
        except ValueError:
            relative_path = file_path.name

        print(f"[{i}/{len(invoice_files)}] Processing {relative_path}...", end=" ", flush=True)
        
        # If group is not provided, use the parent folder name as group
        file_group = group
        if not file_group and file_path.parent != search_dir:
            file_group = file_path.parent.name
            
        result = await process_invoice(
            relative_path=relative_path, 
            base_url=base_url, 
            force_reprocess=force_reprocess,
            category=category,
            group=file_group,
            job_id=job_id
        )
        result["file"] = relative_path
        results.append(result)
        
        if result.get("status") == "success":
            invoice_id = result.get("data", {}).get("invoice_id", "N/A")
            status = result.get("data", {}).get("status", "N/A")
            print(f"✅ Success (ID: {invoice_id[:8] if invoice_id != 'N/A' else 'N/A'}..., Status: {status})")
        elif result.get("status") == "error":
            error_detail = result.get("error", "Unknown error")
            # Try to extract more details from error response
            if isinstance(error_detail, dict):
                error_msg = error_detail.get("detail", error_detail.get("message", str(error_detail)))
            else:
                error_msg = str(error_detail)
            print(f"❌ Failed: {error_msg}")
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"❌ Failed: {error_msg}")
        
        # Small delay to avoid overwhelming the API
        await asyncio.sleep(0.5)
    
    print("-" * 60)
    print(f"\n📊 Summary:")
    successful = sum(1 for r in results if r.get("status") == "success")
    failed = len(results) - successful
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    
    if failed > 0:
        print(f"\n❌ Failed files:")
        for r in results:
            if r.get("status") != "success":
                print(f"   - {r.get('file', 'unknown')}")
    
    print(f"\n💡 View results in the dashboard: http://localhost:8501")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Consolidated invoice processing script")
    parser.add_argument(
        "--dir", "-d",
        type=Path,
        default=Path("data"),
        help="Directory to search for invoices (default: data/)",
    )
    parser.add_argument(
        "--pattern", "-p",
        type=str,
        default="*",
        help="Glob pattern to match files (default: *)",
    )
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Search subdirectories recursively",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-processing of already processed files",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("data"),
        help="Root data directory for relative path resolution (default: data/)",
    )
    parser.add_argument(
        "--category", "-c",
        type=str,
        help="Logical category (e.g. Invoice, Receipt)",
    )
    parser.add_argument(
        "--group", "-g",
        type=str,
        help="Logical group/source (e.g. grok, jimeng). If not provided, folder name will be used.",
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(process_invoices(
            search_dir=args.dir,
            pattern=args.pattern,
            recursive=args.recursive,
            base_url=args.api_url,
            force_reprocess=args.force,
            data_root=args.data_root,
            category=args.category,
            group=args.group
        ))
    except KeyboardInterrupt:
        print("\n\n⚠️ Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
