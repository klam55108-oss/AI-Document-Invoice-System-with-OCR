## Tasks

```text
upload invoices → parse/OCR → extract structured fields → validate/self-correct → store → query/chat.
上传发票 → 解析/OCR → 提取结构化字段 → 验证/自动纠错 → 存储 → 查询/聊天
```

## Improvement Prompts

### 5: docling/paddle OCR not work accurately

```
In the application, the term file_path is ambiguous.
If it actually represents just a file name (e.g. invoice-1.png), it should be renamed to file_name. This is clearer and avoids confusion with filesystem or storage paths.

Paths like grok/f1.webp or jimeng/f2.png are not true file paths in a storage sense.
Here, grok and jimeng function as logical categories or groups, used to organize related files. This information should be stored explicitly as metadata (e.g. category or group), rather than being embedded in a path string.

I also recommend introducing a job_id in metadata to represent a batch processing unit.
For example, when two folders are uploaded together, a single job_id identifies that batch processing run, while each folder name maps naturally to a category/group. This cleanly separates processing context from file organization.

In summary, each file should be treated as:

Asset: the individual file itself (e.g. an image or PDF)

Category / Group: the logical collection the asset belongs to

Job: the batch or processing execution that produced or handled the asset

All three should be captured explicitly in a structured metadata object. This model is clear, scalable, and aligns well with batch processing, auditability, and SaaS design best practices.
```

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

## TODO

- PaddleOCR, deepseek-ocr
- LlamaIndex, langchain
- Docling, pyPDF
- pgvector, chromadb
- Streamlit, react+vite, gradio
- pgqueuer
- sentence-transformers, text-embedding-3-small, nomic-embed-text
- Deepseek-V3, gpt-4o
- fastapi
- PostgreSQL + pgvector
- sqlalchemy, pydantic 2.0


## Tips

- DeepSeek-V3 (deepseek-chat) has 128k tokens (context window)
- Only the last 10 messages are sent: 'core/config.py: CHATBOT_CONTEXT_WINDOW: int = 10'
- prompt engineering

```text
role: "system" -> System Prompt
role: "user" / "assistant" -> (Previous conversation history)
role: "user" -> Dynamic User Prompt (retrieved data + current question)
```

## TODO

- snowflake
- Vanna.ai/LangChain SQL Agent
- vLLM
- Langragh
