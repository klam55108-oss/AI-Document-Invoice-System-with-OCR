"""Adapter for GokulRajaR/invoice-ocr-json dataset."""

import json
from pathlib import Path
from decimal import Decimal
from typing import List
from PIL import Image
import imagehash
from datasets import load_dataset

from ingestion.hf_datasets.base_adapter import BaseDatasetAdapter
from brain.schemas import CanonicalInvoiceSchema, LineItem
from core.logging import get_logger

logger = get_logger(__name__)

class GokulRajaAdapter(BaseDatasetAdapter):
    """Adapter for GokulRajaR dataset."""

    DATASET_ID = "GokulRajaR/invoice-ocr-json"
    LOCAL_DIR = Path("data/hf_datasets/gokulraja")

    async def load(self, limit: int = 10) -> List[CanonicalInvoiceSchema]:
        """Load and normalize GokulRajaR records."""
        self.LOCAL_DIR.mkdir(parents=True, exist_ok=True)

        try:
            ds = load_dataset(self.DATASET_ID, split="train", streaming=True)
            results = []
            
            count = 0
            for row in ds:
                if count >= limit:
                    break
                
                try:
                    img = row["file"]
                    img_id = str(row.get("id") or count)
                    local_filename = f"gokul_{img_id}.jpg"
                    local_path = self.LOCAL_DIR / local_filename
                    
                    if not local_path.exists():
                        img.convert("RGB").save(local_path, "JPEG")
                    
                    img_hash = str(imagehash.phash(img))
                    
                    # GokulRajaR has 'data' which is a JSON-like string
                    import json
                    import ast
                    
                    labels = {}
                    data_str = row.get("data")
                    if data_str:
                        if isinstance(data_str, dict):
                            labels = data_str
                        else:
                            try:
                                labels = json.loads(data_str)
                            except json.JSONDecodeError:
                                try:
                                    labels = ast.literal_eval(data_str)
                                except Exception:
                                    logger.warning(f"Failed to parse GokulRajaR data: {data_str[:100]}")
                    
                    # Safe Decimal conversion helper
                    def safe_decimal(val):
                        if val is None or val == "": return None
                        try:
                            clean_val = "".join(c for c in str(val) if c.isdigit() or c in ".-")
                            return Decimal(clean_val) if clean_val else None
                        except: return None

                    line_items = []
                    for idx, item in enumerate(labels.get("line_items", [])):
                        if isinstance(item, dict):
                          line_items.append(LineItem(
                              description=item.get("description"),
                              quantity=safe_decimal(item.get("quantity")),
                              unit_price=safe_decimal(item.get("unit_price")),
                              amount=safe_decimal(item.get("amount")),
                              line_order=idx
                          ))

                    results.append(CanonicalInvoiceSchema(
                        source_dataset="gokulraja",
                        source_id=img_id,
                        image_path=str(local_path),
                        file_name=local_filename,
                        invoice_number=labels.get("invoice_number"),
                        vendor_name=labels.get("vendor_name") or labels.get("seller", {}).get("name"),
                        line_items=line_items,
                        total_amount=safe_decimal(labels.get("total_amount")),
                        tax_amount=safe_decimal(labels.get("total_tax_amount") or labels.get("tax_amount")),
                        currency=labels.get("currency", "USD"),
                        raw_ocr_text=row.get("ocr_text") or row.get("text"),
                        annotation_confidence=Decimal("0.9"),
                        image_hash=img_hash
                    ))
                    count += 1
                except Exception as e:
                    logger.warning(f"Error processing GokulRajaR row: {e}")
                    continue
            
            return results

        except Exception as e:
            logger.error(f"Failed to load GokulRajaR dataset: {e}")
            return []
