# Quickstart: Dashboard Improvements

**Created**: 2025-01-27  
**Purpose**: User guide for new dashboard features

## Overview

The dashboard improvements add three major enhancements:
1. **Enhanced Analytics & Visualizations** - Visual charts and graphs for data insights
2. **Data Export & Reporting** - Export invoice data to CSV and PDF
3. **Advanced Filtering & Bulk Actions** - Sophisticated filtering and bulk operations

## Enhanced Analytics & Visualizations

### Status Distribution Chart

**Location**: Invoice List tab, top section

**What it shows**: Visual breakdown of invoice processing statuses (Completed, Failed, Processing, etc.)

**How to use**:
1. Navigate to "Invoice List" tab
2. View the status distribution chart at the top
3. Hover over chart segments to see exact counts
4. Chart updates automatically when filters are applied

### Time Series Chart

**Location**: Invoice List tab, analytics section

**What it shows**: Processing volume trends over time (daily, weekly, or monthly)

**How to use**:
1. Navigate to "Invoice List" tab
2. Scroll to analytics section
3. Select time aggregation (daily/weekly/monthly) from dropdown
4. View trends in invoice processing volume

### Vendor Analysis Chart

**Location**: Invoice List tab, analytics section

**What it shows**: Top vendors by invoice count or total amount

**How to use**:
1. Navigate to "Invoice List" tab
2. Scroll to analytics section
3. View vendor analysis chart
4. Toggle between "By Count" and "By Amount" views
5. See top 10 vendors with their metrics

### Financial Summary Charts

**Location**: Invoice List tab, analytics section

**What it shows**: 
- Total amounts across all invoices
- Tax breakdown by rate
- Currency distribution

**How to use**:
1. Navigate to "Invoice List" tab
2. Scroll to financial summary section
3. View aggregated financial metrics
4. Charts show data for completed invoices only

## Data Export & Reporting

### Export Invoice List to CSV

**Location**: Invoice List tab, export button

**What it exports**: All visible invoices with their data (respects current filters)

**How to use**:
1. Apply any desired filters to the invoice list
2. Click "Export to CSV" button (top right of invoice list)
3. CSV file downloads automatically
4. File includes all columns visible in the list

**CSV Contents**:
- Invoice ID, File Name, Status, Vendor, Amount, Confidence, etc.
- All extracted data fields
- Validation summary

### Export Invoice Detail to PDF

**Location**: Invoice Detail tab, export button

**What it exports**: Complete invoice information including:
- Invoice metadata
- Extracted data
- Validation results
- File preview (if available)

**How to use**:
1. Navigate to "Invoice Detail" tab
2. Select or enter an invoice ID
3. Wait for invoice details to load
4. Click "Export to PDF" button (top right)
5. PDF file downloads automatically

**PDF Contents**:
- Formatted invoice report
- All extracted fields with proper formatting
- Validation results with explanations
- Professional layout suitable for reporting

## Advanced Filtering

### Filter by Vendor

**Location**: Sidebar filters

**How to use**:
1. Open sidebar (if not already open)
2. Find "Vendor" filter dropdown
3. Select vendor from list (autocomplete available)
4. Invoice list updates automatically
5. Remove filter by selecting "All Vendors"

### Filter by Amount Range

**Location**: Sidebar filters

**How to use**:
1. Open sidebar
2. Find "Amount Range" section
3. Enter minimum amount (optional)
4. Enter maximum amount (optional)
5. Invoice list shows only invoices within range
6. Clear by removing values

### Filter by Confidence Score

**Location**: Sidebar filters

**How to use**:
1. Open sidebar
2. Find "Minimum Confidence" slider
3. Adjust slider to desired threshold (0-100%)
4. Invoice list shows only invoices with confidence >= threshold
5. Useful for finding low-quality extractions

### Filter by Validation Status

**Location**: Sidebar filters

**How to use**:
1. Open sidebar
2. Find "Validation Status" dropdown
3. Select: "All", "Passed", "Failed", or "Warnings"
4. Invoice list shows only invoices matching validation status
5. Combine with other filters for precise searches

### Viewing Active Filters

**Location**: Invoice List tab, below filters

**What it shows**: All currently active filters with ability to remove individually

**How to use**:
1. Apply multiple filters
2. View active filters displayed as tags/chips
3. Click "×" on any filter tag to remove it
4. Click "Reset All Filters" to clear everything

## Bulk Actions

### Bulk Reprocess Invoices

**Location**: Invoice List tab, bulk actions section

**What it does**: Queues selected invoices for reprocessing

**How to use**:
1. Navigate to "Invoice List" tab
2. Select multiple invoices using checkboxes (or row selection)
3. Click "Bulk Reprocess" button
4. Confirm action in dialog
5. View progress indicator
6. See summary of queued invoices

**Limitations**:
- Maximum 100 invoices per bulk operation
- Reprocessing is queued (not immediate)
- Check processing status in invoice list

## Improved File Preview

### Handling Missing Files

**Location**: Invoice Detail tab, File Preview section

**What it shows**: 
- File preview if file exists
- Helpful message if file missing
- File metadata (hash, size, type) even when missing
- Option to reprocess

**How it works**:
1. System attempts to locate file in `data/` directory
2. If not found, checks `data/encrypted/` directory
3. If still not found, shows:
   - Warning message
   - File metadata (hash, size, type)
   - Suggestion to reprocess if file is available elsewhere
   - File path that was expected

**User Actions**:
- If file was moved: Move file back to expected location
- If file was deleted: Reprocess from original source
- If file path changed: System will attempt to find it

## Enhanced Validation Display

### Improved Failed Validation Display

**Location**: Invoice Detail tab, Validation Analysis section

**What's improved**:
- Failed validations shown prominently at top
- Clear error messages with context
- Expected vs. Actual values in side-by-side comparison
- Suggested actions for fixing issues

**How to use**:
1. Navigate to "Invoice Detail" tab
2. Select invoice with validation failures
3. Scroll to "Validation Analysis" section
4. View failed validations (red indicators)
5. Read error messages and suggested fixes
6. Compare expected vs. actual values

### Improved Warning Display

**Location**: Invoice Detail tab, Validation Analysis section

**What's improved**:
- Warnings shown with caution styling (orange/yellow)
- Clear distinction from failures
- Contextual information about why warning occurred

**How to use**:
1. View warnings section (below failures)
2. Read warning messages
3. Understand impact (warnings don't block processing)
4. Take action if needed

### Passed Validations

**Location**: Invoice Detail tab, Validation Analysis section (collapsed)

**What's improved**:
- Passed validations grouped in expandable section
- Reduces visual clutter
- Still accessible for review

**How to use**:
1. Click "View X Passed Rules" expander
2. Review all passed validation rules
3. See validation details and timestamps

## Handling Missing Data

### Missing Financial Fields

**Location**: Invoice Detail tab, Extracted Data section

**What it shows**: 
- Clear indicators when fields are missing
- Explanations for why data might be missing
- Visual distinction between missing and zero values

**Common Scenarios**:
- **No Subtotal**: Some invoices don't show subtotal separately
  - Display: "Subtotal: Not Available (not found in invoice)"
  - Explanation: Invoice format doesn't include subtotal field
  
- **No Tax Amount**: Some invoices are tax-exempt
  - Display: "Tax Amount: Not Available (tax-exempt invoice)"
  - Explanation: Invoice doesn't include tax
  
- **Low Confidence**: Field extracted but confidence is low
  - Display: "Vendor: [Name] (Low Confidence: 45%)"
  - Explanation: Field was extracted but confidence is below threshold

**How to interpret**:
- "Not Available" = Field not found in invoice (normal for some invoice types)
- "Low Confidence" = Field extracted but may be inaccurate
- Empty value = Extraction attempted but failed

## Performance Tips

1. **Large Datasets**: If you have 1000+ invoices, use filters to reduce dataset size before exporting
2. **Chart Performance**: Charts automatically aggregate data for performance
3. **Bulk Actions**: Limit bulk operations to 100 invoices for best performance
4. **Export Size**: Large exports (>500 invoices) may take longer - progress indicator will show

## Troubleshooting

### Charts Not Displaying

**Issue**: Charts show "No data available"

**Solutions**:
- Check that invoices have been processed
- Verify filters aren't excluding all invoices
- Ensure invoices have required data (e.g., vendor for vendor analysis)

### Export Fails

**Issue**: Export button doesn't work or file doesn't download

**Solutions**:
- Check browser download settings
- Ensure you have invoices selected (for list export)
- Verify invoice is loaded (for detail export)
- Check browser console for errors

### Filters Not Working

**Issue**: Filters don't update the invoice list

**Solutions**:
- Click "Apply Filters" button if present
- Check that filter values are valid
- Try resetting all filters and reapplying
- Refresh the page if filters seem stuck

### File Preview Shows "File Not Found"

**Issue**: File preview shows error even though file exists

**Solutions**:
- Check that file is in `data/` directory
- Verify file path in database matches actual location
- Try reprocessing the invoice
- Check file permissions

## Next Steps

After exploring the dashboard improvements:
1. Try exporting some invoice data to CSV
2. Generate a PDF report for an invoice
3. Use advanced filters to find specific invoices
4. View analytics to understand processing patterns
5. Use bulk actions to reprocess multiple invoices

For more information, see the main project documentation in `/docs/`.

