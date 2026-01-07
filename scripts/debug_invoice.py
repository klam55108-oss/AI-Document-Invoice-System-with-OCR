
import asyncio
import os
from dotenv import load_dotenv
from interface.dashboard.queries import get_invoice_list, get_invoice_detail

async def debug_invoice():
    load_dotenv()
    invoices = await get_invoice_list()
    target = next((inv for inv in invoices if "9.png" in inv.file_name), None)
    
    if not target:
        print("Invoice '9.png' not found.")
        return
    
    print(f"ID: {target.id}")
    print(f"Status: {target.processing_status}")
    print(f"Error: {target.error_message}")
    
    detail = await get_invoice_detail(target.id)
    if detail and "extracted_data" in detail:
        print("\nExtracted Data:")
        print(detail["extracted_data"])
    else:
        print("\nNo extracted data found.")

if __name__ == "__main__":
    asyncio.run(debug_invoice())
