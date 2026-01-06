## TODO list

- Persistence of Training Data: Instead of ephemeral indices, store the invoice embeddings in a permanent pgvector table. This turns the "extracted data" into a "searchable knowledge base."
- Integration with ERP (Enterprise Resource Planning) and BI (Business Intelligence) systems:

### A. API-Led Integration (Push/Pull)
- **Webhooks (Recommended)**: Configure the FastAPI backend to "push" a JSON payload to the ERP system immediately after an invoice is marked as COMPLETED and PASSED.
- **REST API**: ERP systems can "pull" data periodically using the existing /api/v1/invoices endpoints. Add a dedicated /api/v1/export endpoint to return data in specific formats (CSV, XML, EDI).

### B. Database/Vector Store Integration

- **BI Connectors**: Connect BI tools (PowerBI, Tableau, Metabase) directly to the PostgreSQL database.
- **Semantic Search**: Use the pgvector data to power BI dashboards that can "cluster" invoices by similarity or find anomalies that traditional SQL queries might miss.

### C. Workflow Automation
- Use middleware like `n8n` or `Zapier` to monitor the `invoices` table and trigger workflows in systems like SAP, Oracle, or Microsoft Dynamics.


- 42 invoices exist in the database
- All invoices have extracted_data records
- Extracted fields are NULL: vendor_name, invoice_number, total_amount are all None
- No 'jimeng' folder in metadata (subfolder is 'uploads')
- invoice_embeddings table doesn't exist (vector search fails, but fallback should work)

### The problem

The database query used an inner join that required extracted data, and the WHERE clause with ILIKE on NULL values doesn't match. So:
- Queries like "how many invoices" return 0 results
- The LLM receives no invoice data and responds with "I couldn't find any invoices"

### Fixes applied

- Improved database query: searches file names first (always available), then tries extracted data
- Better handling of missing data: uses outer join and handles NULL extracted fields
- Aggregate query fallback: when asking "how many" or "total", retrieves all invoices if specific search fails
- Enhanced response generation: includes file names and metadata even when extracted data is missing