#### Accessing the Database Directly

To connect to the PostgreSQL database manually for inspection or debugging, run:

```bash
psql -h localhost -p 5432 -U rag -d rag
```

You may be prompted for the password specified in your `.env` file as `POSTGRES_PASSWORD`.
