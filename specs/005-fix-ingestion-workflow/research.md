# Research: Fix Ingestion Workflow Issues

**Date**: 2025-01-27  
**Feature**: Fix Ingestion Workflow  
**Status**: Complete

## Problem Statement

The ingestion workflow has multiple issues:
1. `scripts/process_invoices.py` not working well
2. POST API `/api/v1/invoices/process` not working well
3. Dashboard at `localhost:8501` cannot display invoices list
4. Potential schema mismatches between database and code
5. Probe files (`probe_paddle*.py`, `debug_invoice.py`) in root directory need cleanup

## Root Cause Analysis

### 1. Schema Migration Status

**Finding**: Migration `8c2b9c709184` refactored the schema:
- Renamed `file_path` → `storage_path` in `invoices` table
- Added new columns: `category`, `group`, `job_id`
- Dropped old `file_path` column

**Code Status**: 
- ✅ `core/models.py` correctly uses `storage_path`
- ✅ `interface/api/routes/invoices.py` correctly uses `storage_path`
- ✅ `ingestion/orchestrator.py` correctly uses `storage_path`

**Potential Issue**: Database may not have the latest migration applied, causing schema mismatch errors.

### 2. Dashboard Query Issues

**Finding**: `interface/dashboard/queries.py` uses proper SQLAlchemy models and should work correctly. However:
- Dashboard creates new engine/session for each query (inefficient but should work)
- Queries use `outerjoin` which should handle missing extracted_data gracefully
- Potential issue: If database schema is out of sync, queries will fail

**Potential Issues**:
- Database connection errors not handled gracefully in dashboard
- Missing error messages when queries fail
- Schema mismatch causing query failures

### 3. API Processing Endpoint

**Finding**: `POST /api/v1/invoices/process` endpoint:
- Uses `request.file_path` to construct file path
- Calls `process_invoice_file()` which should work
- Has proper error handling with rollback

**Potential Issues**:
- File path resolution issues (relative vs absolute)
- Database session management in background tasks
- Schema mismatch causing model errors

### 4. Process Script Issues

**Finding**: `scripts/process_invoices.py`:
- Makes HTTP requests to API endpoint
- Handles path resolution relative to `data/` directory
- Has error handling

**Potential Issues**:
- API endpoint not responding
- File path resolution incorrect
- Database errors not visible in script output

### 5. File Structure Issues

**Finding**: Root directory contains:
- `probe_paddle.py`
- `probe_paddle_ocr.py`
- `debug_invoice.py`

These are temporary debugging files that should be moved to `scripts/` or removed.

## Technical Decisions

### Decision 1: Verify Database Schema

**Decision**: Run Alembic migrations to ensure database schema matches code models.

**Rationale**: Schema mismatches are the most likely cause of failures. Ensuring migrations are applied will eliminate this as a variable.

**Alternatives Considered**:
- Manual schema inspection - too time-consuming
- Code changes to match old schema - would break future migrations

### Decision 2: Add Comprehensive Error Logging

**Decision**: Add detailed error logging at all failure points to identify root causes.

**Rationale**: Current error messages may not be detailed enough to diagnose issues. Better logging will help identify specific failure points.

**Alternatives Considered**:
- Only log at API level - insufficient for debugging
- Log everything - too verbose, chose targeted logging

### Decision 3: Improve Error Handling in Dashboard

**Decision**: Add try-catch blocks and user-friendly error messages in dashboard queries.

**Rationale**: Dashboard failures should be visible to users with actionable error messages, not silent failures.

**Alternatives Considered**:
- Let errors propagate - poor user experience
- Hide all errors - makes debugging impossible

### Decision 4: Clean Up Probe Files

**Decision**: Move probe files to `scripts/` directory or remove if no longer needed.

**Rationale**: Root directory should only contain project configuration files, not temporary debugging scripts.

**Alternatives Considered**:
- Keep in root with `.gitignore` - still clutters workspace
- Delete immediately - might need them for reference, move instead

### Decision 5: Add Database Health Check

**Decision**: Add health check endpoint and dashboard initialization check to verify database connectivity and schema.

**Rationale**: Early detection of database issues prevents cryptic errors later in the workflow.

**Alternatives Considered**:
- Only check on first query - too late, user already sees error
- Check on every request - too expensive, check on startup

## Testing Strategy

1. **Schema Verification**: Run `alembic upgrade head` and verify no errors
2. **API Testing**: Test POST `/api/v1/invoices/process` with valid file
3. **Dashboard Testing**: Verify dashboard loads and displays invoice list
4. **Script Testing**: Run `scripts/process_invoices.py` with test files
5. **Error Path Testing**: Test with missing files, invalid paths, database errors

## Dependencies

- Alembic migrations must be up to date
- Database connection must be configured correctly
- File system permissions for `data/` directory
- All Python dependencies installed

## Risks

1. **Data Loss**: Running migrations on production database could cause issues if not tested first
2. **Breaking Changes**: Schema changes might break existing queries if not handled carefully
3. **Performance**: Additional error checking might add latency (minimal impact expected)

## Next Steps

1. Verify database schema matches models
2. Add comprehensive error logging
3. Improve dashboard error handling
4. Test all endpoints and scripts
5. Clean up probe files
6. Document debugging procedures

