"""Confidence display utility functions for dashboard UI."""

from decimal import Decimal
from typing import List, Optional


def format_confidence_score(confidence: Optional[Decimal]) -> str:
    """Format confidence score as percentage string.
    
    Args:
        confidence: Confidence score (0.0-1.0) or None
        
    Returns:
        Formatted percentage string (e.g., "95%") or "N/A"
    """
    if confidence is None:
        return "N/A"
    
    # Handle edge cases (shouldn't occur due to database constraints, but be safe)
    if confidence < 0 or confidence > 1:
        return "N/A"
    
    percentage = int(confidence * 100)
    return f"{percentage}%"


def get_confidence_color(confidence: Optional[Decimal]) -> str:
    """Get color code for confidence score (red/yellow/green).
    
    Args:
        confidence: Confidence score (0.0-1.0) or None
        
    Returns:
        Color name: "red" (<50%), "yellow" (50-70%), "green" (>70%), "grey" (None)
    """
    if confidence is None:
        return "grey"
    
    if confidence < Decimal("0.50"):
        return "red"
    elif confidence < Decimal("0.70"):
        return "yellow"
    else:
        return "green"


def get_confidence_badge(confidence: Optional[Decimal]) -> str:
    """Generate HTML badge for confidence score with color coding.
    
    Args:
        confidence: Confidence score (0.0-1.0) or None
        
    Returns:
        HTML string with styled badge
    """
    color = get_confidence_color(confidence)
    score_text = format_confidence_score(confidence)
    
    # Color mappings for Streamlit markdown
    color_styles = {
        "red": "background-color: #ff4444; color: white;",
        "yellow": "background-color: #ffaa00; color: white;",
        "green": "background-color: #44ff44; color: white;",
        "grey": "background-color: #cccccc; color: black;",
    }
    
    style = color_styles.get(color, color_styles["grey"])
    
    badge_html = f'''
    <span style="display: inline-block; padding: 4px 8px; border-radius: 4px; 
                  font-weight: bold; font-size: 12px; {style}">
        {score_text}
    </span>
    '''
    
    return badge_html.strip()


def get_confidence_tooltip(confidence: Optional[Decimal], field_name: str) -> str:
    """Generate tooltip text for confidence score.
    
    Args:
        confidence: Confidence score (0.0-1.0) or None
        field_name: Name of the field (e.g., "vendor_name")
        
    Returns:
        Tooltip text explaining the confidence score
    """
    score_text = format_confidence_score(confidence)
    
    # Make field name human-readable
    field_display = field_name.replace("_", " ").title()
    
    if confidence is None:
        return f"{field_display}: Confidence score not available"
    
    if confidence < Decimal("0.50"):
        quality = "Low"
        recommendation = "Manual review recommended"
    elif confidence < Decimal("0.70"):
        quality = "Medium"
        recommendation = "May need review"
    else:
        quality = "High"
        recommendation = "Likely accurate"
    
    tooltip = f"{field_display}: {score_text} confidence ({quality}). {recommendation}."
    
    return tooltip


def get_missing_fields_badge(missing_fields: List[str]) -> str:
    """Generate warning badge for missing fields.
    
    Args:
        missing_fields: List of field names that are missing/NULL
        
    Returns:
        HTML string with warning badge
    """
    if not missing_fields:
        return ""
    
    count = len(missing_fields)
    
    # Make field names human-readable
    field_names = [f.replace("_", " ").title() for f in missing_fields]
    field_list = ", ".join(field_names)
    
    badge_html = f'''
    <span style="display: inline-block; padding: 4px 8px; border-radius: 4px; 
                  font-weight: bold; font-size: 12px; background-color: #ff4444; color: white;">
        ⚠️ {count} Missing: {field_list}
    </span>
    '''
    
    return badge_html.strip()


def get_quality_indicator_emoji(confidence: Optional[Decimal]) -> str:
    """Get emoji indicator for confidence level.
    
    Args:
        confidence: Confidence score (0.0-1.0) or None
        
    Returns:
        Emoji character representing quality level
    """
    if confidence is None:
        return "❓"  # Unknown
    
    if confidence < Decimal("0.50"):
        return "❌"  # Poor
    elif confidence < Decimal("0.70"):
        return "⚠️"  # Warning
    else:
        return "✅"  # Good


def format_confidence_with_emoji(confidence: Optional[Decimal]) -> str:
    """Format confidence score with emoji indicator.
    
    Args:
        confidence: Confidence score (0.0-1.0) or None
        
    Returns:
        Formatted string with emoji and percentage (e.g., "✅ 95%")
    """
    emoji = get_quality_indicator_emoji(confidence)
    score = format_confidence_score(confidence)
    
    return f"{emoji} {score}"

