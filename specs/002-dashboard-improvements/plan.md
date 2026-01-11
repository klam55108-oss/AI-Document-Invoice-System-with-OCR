# Implementation Plan: Dashboard Improvements

**Branch**: `002-dashboard-improvements` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-dashboard-improvements/spec.md`

## Summary

Enhance the Streamlit dashboard at http://localhost:${UI_PORT:-8501}/ with comprehensive improvements to both "Invoice List" and "Invoice Detail" tabs. The improvements focus on: (1) Enhanced analytics and visualizations for data-driven insights, (2) Data export capabilities for external reporting, (3) Advanced filtering and bulk actions for operational efficiency, (4) Robust file path resolution and missing file handling, (5) Improved validation result display with actionable error messages, and (6) Graceful handling of missing invoice data fields (subtotal, tax_amount, etc.) following industry-standard invoice processing patterns.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: Streamlit >=1.39.0, pandas >=2.2.0, plotly >=5.18.0 (for charts), reportlab >=4.0.0 (for PDF export), sqlalchemy[asyncio] >=2.0.36  
**Storage**: PostgreSQL (existing), file system for exports  
**Testing**: pytest >=8.3.0, pytest-asyncio >=0.24.0, httpx >=0.27.0  
**Target Platform**: Web browser (Streamlit app), Linux/macOS server  
**Project Type**: Web application (Streamlit dashboard)  
**Performance Goals**: Dashboard loads in < 2s (p95), chart rendering < 1s, export generation < 5s for 500 invoices  
**Constraints**: p95 response time < 500ms for API calls, < 2s for async operations, memory < 512MB per request, must handle 10,000 invoices without degradation  
**Scale/Scope**: Single Streamlit application, 2 main tabs with multiple enhancements, supports 10k+ invoice records

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with all constitution principles:

### I. Code Quality Standards
- [x] Type hints defined for all function signatures
- [x] Static analysis tools (ruff, mypy) configured and passing
- [x] Error handling strategy defined with structured logging
- [x] Security practices identified (input validation, encryption, parameterized queries)
- [x] Dependencies will be pinned with exact versions

### II. Testing Discipline
- [x] Test-driven development (TDD) approach confirmed
- [x] Test coverage targets defined (80% core, 60% overall)
- [x] Test categories identified (unit, integration, contract)
- [x] Async test patterns defined (pytest-asyncio)
- [x] CI/CD test automation planned

### III. User Experience Consistency
- [x] API response format standards defined
- [x] Error message format and user guidance strategy defined
- [x] UI consistency patterns identified (if applicable)
- [x] Loading states and progress indicators planned

### IV. Performance Requirements
- [x] Latency targets defined (p95 < 500ms sync, < 2s async initiation)
- [x] Database query optimization strategy identified
- [x] Memory usage bounds defined (< 512MB per request)
- [x] Caching strategy planned
- [x] Async I/O patterns confirmed
- [x] Performance regression testing planned

## Project Structure

### Documentation (this feature)

```text
specs/002-dashboard-improvements/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
interface/dashboard/
├── app.py                    # Main Streamlit application (enhanced)
├── queries.py                # Database query utilities (enhanced)
├── components/               # New: Reusable UI components
│   ├── __init__.py
│   ├── charts.py            # Chart generation utilities
│   ├── file_preview.py       # File preview with path resolution
│   ├── validation_display.py # Enhanced validation result display
│   └── export_utils.py      # CSV/PDF export functions
└── utils/                    # New: Utility functions
    ├── __init__.py
    ├── path_resolver.py      # File path resolution logic
    ├── data_formatters.py    # Data formatting utilities
    └── filters.py            # Advanced filtering logic

tests/
├── integration/
│   └── test_dashboard_improvements.py  # Integration tests for dashboard
└── unit/
    ├── test_charts.py                   # Chart generation tests
    ├── test_file_preview.py             # File preview tests
    ├── test_validation_display.py       # Validation display tests
    └── test_export_utils.py             # Export utility tests
```

**Structure Decision**: Extend existing Streamlit dashboard structure with modular components and utilities. New components are organized in `components/` directory for reusability, and utilities in `utils/` for shared logic. This maintains separation of concerns while keeping the dashboard structure simple.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - all improvements align with existing architecture and constitution principles.

## Phase 0: Research Complete ✅

**Research Document**: [research.md](./research.md)

**Key Decisions**:
1. **File Path Resolution**: Implement robust resolution with fallback to encrypted directory
2. **Missing Data Handling**: Show clear indicators with explanations, distinguish missing from zero
3. **Validation Display**: Group by severity, show actionable error messages
4. **Chart Library**: Use Plotly for interactive visualizations
5. **Export Libraries**: pandas for CSV, reportlab for PDF
6. **Filtering**: Database-level filtering with session state persistence
7. **Bulk Actions**: Queue-based with progress tracking, limit to 100 invoices

## Phase 1: Design Complete ✅

**Data Model**: [data-model.md](./data-model.md)
- FilterState for session state management
- ExportRequest for export operations
- BulkAction for bulk operations
- ChartData structures for visualizations
- Enhanced validation display structures

**API Contracts**: [contracts/openapi.yaml](./contracts/openapi.yaml)
- Bulk reprocess endpoint
- Analytics endpoints (status distribution, time series, vendor analysis, financial summary)

**Quickstart Guide**: [quickstart.md](./quickstart.md)
- User guide for all new features
- Troubleshooting section
- Performance tips

**Agent Context**: Updated with new technologies (Plotly, reportlab)

## Next Steps

Ready for `/speckit.tasks` command to break down implementation into actionable tasks.
