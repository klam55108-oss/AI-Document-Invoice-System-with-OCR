"""Export utilities for invoice data to CSV and PDF formats."""

import io
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def export_invoice_list_to_csv(invoices: list[dict[str, Any]], output_path: Path | str | None = None) -> bytes:
    """Export invoice list to CSV format.

    Args:
        invoices: List of invoice dictionaries with fields like:
            - invoice_id, file_name, processing_status, vendor_name,
              total_amount, currency, created_at, etc.
        output_path: Optional path to save CSV file. If None, returns bytes.

    Returns:
        CSV file content as bytes if output_path is None, otherwise writes to file
    """
    if not invoices:
        # Return empty CSV with headers
        df = pd.DataFrame(columns=[
            "Invoice ID", "File Name", "Status", "Vendor", "Total Amount",
            "Currency", "Invoice Date", "Created At"
        ])
    else:
        # Prepare data for DataFrame
        rows = []
        for inv in invoices:
            rows.append({
                "Invoice ID": str(inv.get("invoice_id", "")),
                "File Name": inv.get("file_name", ""),
                "Status": inv.get("processing_status", ""),
                "Vendor": inv.get("vendor_name", ""),
                "Total Amount": float(inv.get("total_amount", 0)) if inv.get("total_amount") else None,
                "Currency": inv.get("currency", ""),
                "Invoice Date": inv.get("invoice_date").isoformat() if inv.get("invoice_date") else "",
                "Created At": inv.get("created_at").isoformat() if inv.get("created_at") else "",
            })
        
        df = pd.DataFrame(rows)
    
    # Convert to CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")
    
    if output_path:
        Path(output_path).write_bytes(csv_bytes)
    
    return csv_bytes


def export_invoice_detail_to_pdf(
    invoice_detail: dict[str, Any],
    output_path: Path | str | None = None,
) -> bytes:
    """Export invoice detail to PDF format.

    Args:
        invoice_detail: Invoice detail dictionary with:
            - invoice_id, file_name, processing_status, vendor_name,
              extracted_data, validation_results, etc.
        output_path: Optional path to save PDF file. If None, returns bytes.

    Returns:
        PDF file content as bytes if output_path is None, otherwise writes to file
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("Invoice Detail Report", styles["Title"])
    story.append(title)
    story.append(Spacer(1, 0.2 * inch))
    
    # Basic Information
    story.append(Paragraph("Basic Information", styles["Heading2"]))
    basic_data = [
        ["Invoice ID:", str(invoice_detail.get("invoice_id", ""))],
        ["File Name:", invoice_detail.get("file_name", "")],
        ["Status:", str(invoice_detail.get("processing_status", ""))],
        ["Created At:", invoice_detail.get("created_at").isoformat() if invoice_detail.get("created_at") else ""],
    ]
    basic_table = Table(basic_data, colWidths=[2 * inch, 4 * inch])
    basic_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(basic_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Extracted Data
    extracted = invoice_detail.get("extracted_data")
    if extracted:
        story.append(Paragraph("Extracted Data", styles["Heading2"]))
        extracted_data = [
            ["Vendor:", extracted.get("vendor_name", "")],
            ["Invoice Number:", extracted.get("invoice_number", "")],
            ["Invoice Date:", extracted.get("invoice_date").isoformat() if extracted.get("invoice_date") else ""],
            ["Total Amount:", f"{extracted.get('currency', '')} {extracted.get('total_amount', 0):,.2f}" if extracted.get("total_amount") else ""],
            ["Subtotal:", f"{extracted.get('currency', '')} {extracted.get('subtotal', 0):,.2f}" if extracted.get("subtotal") else ""],
            ["Tax Amount:", f"{extracted.get('currency', '')} {extracted.get('tax_amount', 0):,.2f}" if extracted.get("tax_amount") else ""],
        ]
        extracted_table = Table(extracted_data, colWidths=[2 * inch, 4 * inch])
        extracted_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(extracted_table)
        story.append(Spacer(1, 0.3 * inch))
    
    # Validation Results
    validation_results = invoice_detail.get("validation_results", [])
    if validation_results:
        story.append(Paragraph("Validation Results", styles["Heading2"]))
        val_data = [["Rule", "Status", "Message"]]
        for result in validation_results:
            val_data.append([
                result.get("rule_name", ""),
                result.get("status", ""),
                result.get("error_message", "")[:50] if result.get("error_message") else "",
            ])
        val_table = Table(val_data, colWidths=[2 * inch, 1.5 * inch, 2.5 * inch])
        val_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(val_table)
    
    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    if output_path:
        Path(output_path).write_bytes(pdf_bytes)
    
    return pdf_bytes

