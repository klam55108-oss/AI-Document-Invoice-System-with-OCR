#!/bin/bash

# Process Invoices in the data/ directory
python scripts/process_invoices.py --recursive


# python scripts/process_invoices.py --recursive --dir data/jimeng --force --concurrency 2
# python scripts/process_invoices.py --dir data/jimeng --pattern "invoice-1.png" --force --background --api-url "http://127.0.0.1:8800"
# python3 scripts/process_invoices.py --category "Invoice" --group "Vendor_X" --dir data/vendor_x


# curl -X POST "http://localhost:8000/api/v1/invoices/process" \
#  -H "Content-Type: application/json" \
#  -d '{"file_path": "jimeng/invoice-5.png"}'

# python scripts/process_invoices.py --dir data/jimeng --pattern "invoice-6.png" --force