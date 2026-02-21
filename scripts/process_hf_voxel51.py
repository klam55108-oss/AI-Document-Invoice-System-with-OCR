#!/usr/bin/env python3
"""
Specialized script to process Voxel51 HuggingFace dataset using FiftyOne.
This script utilizes FiftyOne for intelligent dataset management and the 
FastAPI endpoint for extraction processing.
"""

import asyncio
import os
import sys
import uuid
import json
from pathlib import Path
from typing import Optional, List

import httpx
import fiftyone as fo
import fiftyone.utils.huggingface as founh
from tqdm import tqdm

# Add project root to path
sys.path.append(os.getcwd())

from core.config import settings

VOXEL51_DATASET_ID = "Voxel51/high-quality-invoice-images-for-ocr"
HF_DATA_DIR = Path("data/hf_invoices")

from huggingface_hub import hf_hub_download

async def call_process_api(
    relative_path: str,
    base_url: str,
    category: str = "Invoice",
    group: str = "Voxel51",
    force_reprocess: bool = False,
    background: bool = False,
) -> dict:
    """Call the FastAPI endpoint to process an invoice."""
    url = f"{base_url}/api/v1/invoices/process"
    payload = {
        "file_path": relative_path,
        "force_reprocess": force_reprocess,
        "category": category,
        "group": group,
        "background": background,
    }
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

def ensure_local_copy(sample, target_dir: Path) -> str:
    """Ensure the sample image exists in our data/hf_invoices folder."""
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract the filename from the path stored in the HF metadata
    # Voxel51 stores paths like 'data/batch1-0494.jpg'
    filename = sample.filepath.replace("\\", "/").split("/")[-1]
    if "batches" in sample.filepath: # Handle nested paths if any
         # Get relative path from 'data' if it exists
         parts = sample.filepath.split("data/")
         hf_repo_path = "data/" + parts[-1] if len(parts) > 1 else sample.filepath
    else:
         hf_repo_path = f"data/{filename}"

    target_path = target_dir / filename
    
    if not target_path.exists():
        print(f"   📥 Downloading {hf_repo_path} from Hub...")
        try:
            # surgical download to avoid 429
            downloaded_path = hf_hub_download(
                repo_id=VOXEL51_DATASET_ID,
                filename=hf_repo_path,
                repo_type="dataset",
                local_dir="data/hf_temp"
            )
            import shutil
            shutil.copy2(downloaded_path, target_path)
        except Exception as e:
            print(f"   ⚠️ Failed to download {hf_repo_path}: {e}")
            raise
    
    # Return path relative to project's data directory
    return os.path.relpath(target_path, "data")

async def process_hf_dataset(
    limit: int = 10,
    only_annotated: bool = True,
    base_url: str = f"http://localhost:{settings.API_PORT}",
    concurrency: int = 1, # Reduced concurrency to avoid API 429s as well
    force: bool = False
):
    """Load and process the Voxel51 dataset using FiftyOne."""
    print(f"🔍 Loading FiftyOne dataset metadata: {VOXEL51_DATASET_ID}")
    
    # The fix: Do NOT let FiftyOne download all media.
    # By passing a reasonably large max_samples (e.g. 2000), we get the metadata 
    # for all annotated ones WITHOUT triggering the full 8k download.
    dataset = founh.load_from_hub(VOXEL51_DATASET_ID, max_samples=2000 if only_annotated else 8181)
    
    view = dataset
    if only_annotated:
        view = dataset.exists("json_annotation")
        print(f"✅ Filtered for annotated samples: {len(view)} found in cache")
    
    if limit > 0:
        view = view.limit(limit)
    
    samples = list(view)
    if not samples:
        print("❌ No samples found matching criteria.")
        return

    print(f"🚀 Processing {len(samples)} samples...")
    
    semaphore = asyncio.Semaphore(concurrency)
    
    async def process_sample(i, sample):
        async with semaphore:
            # Ensure file is in our expected data directory for the API
            rel_path = ensure_local_copy(sample, HF_DATA_DIR)
            
            print(f"[{i+1}/{len(samples)}] Processing {rel_path}...")
            
            result = await call_process_api(
                relative_path=rel_path,
                base_url=base_url,
                force_reprocess=force
            )
            
            if result.get("status") == "success":
                inv_id = result.get("data", {}).get("invoice_id", "")[:8]
                print(f"   ✅ Done: {rel_path} (ID: {inv_id})")
            else:
                print(f"   ❌ Failed: {rel_path} - {result.get('error')}")
            
            return result

    tasks = [process_sample(i, s) for i, s in enumerate(samples)]
    results = await asyncio.gather(*tasks)
    
    success = sum(1 for r in results if r.get("status") == "success")
    print(f"\n📊 Processed {len(results)} samples. Success: {success}, Failed: {len(results)-success}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process Voxel51 HF dataset")
    parser.add_argument("--limit", type=int, default=10, help="Number of samples to process")
    parser.add_argument("--all", action="store_true", help="Process all samples")
    parser.add_argument("--unannotated", action="store_true", help="Include unannotated samples")
    parser.add_argument("--concurrency", type=int, default=3, help="Concurrent tasks")
    parser.add_argument("--force", action="store_true", help="Force reprocessing")
    
    args = parser.parse_args()
    
    limit = 0 if args.all else args.limit
    only_annotated = not args.unannotated
    
    asyncio.run(process_hf_dataset(
        limit=limit,
        only_annotated=only_annotated,
        concurrency=args.concurrency,
        force=args.force
    ))
