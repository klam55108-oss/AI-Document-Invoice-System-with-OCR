# Research: Dashboard Improvements

**Created**: 2025-01-27  
**Purpose**: Document research findings and technology decisions for dashboard improvements

## Research Questions

### 1. File Path Resolution and Missing File Handling

**Question**: How should the dashboard handle cases where source files are not found on disk?

**Findings**:
- Invoice file paths are stored relative to `data/` directory in the database
- Files may be encrypted and stored in `data/encrypted/` directory
- Files can be moved or deleted after processing, causing "Source file not found on disk" errors
- Dashboard currently checks absolute paths without resolving relative paths correctly

**Decision**: Implement robust file path resolution with fallback strategies:
1. Resolve relative paths from `data/` directory
2. Check encrypted file location if original not found
3. Display helpful error messages with actionable guidance
4. Show file metadata even when file is missing (hash, size, type)
5. Provide option to reprocess if file is missing

**Rationale**: Standard invoice processing systems handle missing files gracefully by showing available metadata and providing recovery options. This maintains user workflow even when files are moved.

**Alternatives Considered**:
- Blocking access when file missing: Rejected - too restrictive, breaks user workflow
- Storing absolute paths: Rejected - breaks portability, doesn't solve file movement issue

### 2. Missing Data Field Handling

**Question**: How should missing invoice data fields (subtotal, tax_amount, etc.) be displayed?

**Findings**:
- Invoice formats vary significantly (some don't have subtotal, some don't have tax)
- ExtractedData model allows NULL for all financial fields
- Current dashboard shows "—" for missing values but doesn't explain why
- Industry standard: Show clear indicators when data is missing and explain context

**Decision**: Implement intelligent missing data handling:
1. Display "Not Available" with context (e.g., "Subtotal not found in invoice")
2. Group related fields logically (e.g., if no subtotal, show explanation for tax calculation)
3. Use visual indicators (icons, colors) to distinguish missing vs. zero values
4. Provide tooltips explaining why data might be missing
5. Show confidence scores to indicate extraction quality

**Rationale**: Follows industry best practices for invoice processing UIs. Clear communication about missing data helps users understand extraction quality and make informed decisions.

**Alternatives Considered**:
- Show zero for missing values: Rejected - misleading, zero is different from missing
- Hide missing fields: Rejected - users need to see what was attempted to extract

### 3. Validation Result Display Enhancement

**Question**: How to improve the display of failed and warning validation results?

**Findings**:
- Current display shows validation items in containers but lacks actionable guidance
- Failed validations need clear explanations and suggested actions
- Warnings should be distinct from failures but still visible
- Industry standard: Group by severity, show context, provide remediation steps

**Decision**: Enhanced validation display with:
1. Group validation results by severity (Failed → Warnings → Passed)
2. Show visual hierarchy: Failed items prominently, warnings with caution styling
3. Include actionable error messages with suggested fixes
4. Display expected vs. actual values in clear comparison format
5. Add expandable details for complex validation rules
6. Show validation rule descriptions and business context

**Rationale**: Improves user experience by making validation results actionable. Users can quickly identify issues and understand how to resolve them.

**Alternatives Considered**:
- Tabbed interface for validation: Rejected - adds complexity, reduces visibility
- Collapse all passed validations: Accepted - reduces clutter while maintaining access

### 4. Chart Library Selection

**Question**: Which library should be used for dashboard visualizations?

**Findings**:
- Streamlit has built-in charting via `st.line_chart`, `st.bar_chart`, but limited customization
- Plotly provides interactive charts with better customization
- Plotly Express simplifies common chart creation
- Streamlit supports Plotly via `st.plotly_chart`

**Decision**: Use Plotly for all visualizations:
- Plotly Express for simple charts (bar, line, pie)
- Plotly Graph Objects for advanced customization
- Streamlit's native charts for simple metrics only

**Rationale**: Plotly provides interactive, professional charts that enhance user experience. It's well-integrated with Streamlit and supports the required chart types.

**Alternatives Considered**:
- Matplotlib: Rejected - static charts, less interactive
- Altair: Rejected - less common, smaller community
- Streamlit native only: Rejected - insufficient customization for analytics needs

### 5. Export Format and Library

**Question**: How to implement CSV and PDF export functionality?

**Findings**:
- CSV export: pandas `to_csv()` is standard, Streamlit `st.download_button` for file download
- PDF export: reportlab is standard Python library for PDF generation
- PDF should include: invoice metadata, extracted data, validation results, formatted layout
- Large exports (>500 invoices) may need pagination or batch processing

**Decision**: 
- CSV: Use pandas DataFrame.to_csv() with Streamlit download button
- PDF: Use reportlab for structured PDF generation with proper formatting
- For large exports: Implement progress indicators and optional pagination

**Rationale**: Standard Python libraries with proven track records. Reportlab provides full control over PDF layout and formatting.

**Alternatives Considered**:
- WeasyPrint for PDF: Rejected - HTML-to-PDF, less control over layout
- fpdf: Rejected - lower-level API, more complex
- Excel export: Deferred - can be added later if needed

### 6. Advanced Filtering Implementation

**Question**: How to implement advanced filtering with multiple criteria?

**Findings**:
- Streamlit provides `st.selectbox`, `st.slider`, `st.number_input` for filters
- Filter state should persist in session state
- Database queries need to support multiple filter combinations
- Performance: Filters should be applied at database level, not in-memory

**Decision**: 
- Use Streamlit session state for filter persistence
- Extend `get_invoice_list()` query function to support all filter types
- Apply filters in SQL WHERE clauses for performance
- Show active filters as removable chips/tags
- Display filter result count

**Rationale**: Leverages Streamlit's built-in state management and ensures performance by filtering at database level.

**Alternatives Considered**:
- Client-side filtering: Rejected - doesn't scale, poor performance
- URL parameters: Rejected - adds complexity, Streamlit session state is sufficient

### 7. Bulk Actions Implementation

**Question**: How to implement bulk actions on selected invoices?

**Findings**:
- Streamlit's `st.dataframe` supports row selection
- Bulk actions need to queue operations (reprocessing is async)
- Need progress tracking for bulk operations
- Should show success/failure summary

**Decision**:
- Use Streamlit's dataframe selection to get selected invoice IDs
- Create background job queue for bulk reprocessing
- Show progress with `st.progress` and status updates
- Display summary of successful/failed operations
- Limit bulk operations to 100 invoices per batch

**Rationale**: Aligns with existing job queue architecture and provides good user feedback for long-running operations.

**Alternatives Considered**:
- Synchronous bulk processing: Rejected - blocks UI, poor UX
- No limit on bulk size: Rejected - risk of timeouts, poor performance

## Technology Stack Decisions

### New Dependencies

- **plotly >=5.18.0**: Interactive charting library
- **reportlab >=4.0.0**: PDF generation library
- **openpyxl >=3.1.0**: Already in dependencies, may be used for Excel export in future

### Existing Dependencies (No Changes)

- **streamlit >=1.39.0**: Dashboard framework
- **pandas >=2.2.0**: Data manipulation and CSV export
- **sqlalchemy[asyncio] >=2.0.36**: Database queries

## Performance Considerations

1. **Chart Rendering**: Use data aggregation at database level before charting
2. **Export Generation**: Stream large exports to avoid memory issues
3. **Filter Queries**: Ensure proper database indexes on filter columns
4. **File Path Resolution**: Cache resolved paths in session state to avoid repeated file system checks

## Security Considerations

1. **File Path Validation**: Sanitize file paths to prevent directory traversal
2. **Export Data**: Ensure sensitive data is handled appropriately in exports
3. **Bulk Actions**: Validate user permissions before allowing bulk operations
4. **Input Validation**: Validate all filter inputs to prevent SQL injection

## Accessibility Considerations

1. **Chart Accessibility**: Ensure charts have proper labels and alt text
2. **Error Messages**: Use clear, non-technical language
3. **Color Coding**: Don't rely solely on color for information (use icons/text)
4. **Keyboard Navigation**: Ensure all interactive elements are keyboard accessible

## Testing Strategy

1. **Unit Tests**: Test individual components (charts, exports, filters)
2. **Integration Tests**: Test full dashboard workflows
3. **Performance Tests**: Verify dashboard loads within performance targets
4. **Error Handling Tests**: Test missing files, missing data, validation edge cases

