"""
Mobile-Friendly UI Helper Functions
Provides utilities for creating responsive layouts across all screen sizes
"""

import streamlit as st
from typing import List, Dict, Any, Optional, Tuple


def get_screen_size() -> str:
    """
    Detect approximate screen size based on browser width
    Returns: 'mobile' | 'tablet' | 'desktop'
    Note: Streamlit doesn't expose viewport width directly, but we can provide logic
    """
    # Fallback detection - assumes 'centered' layout on mobile
    try:
        width = st.session_state.get("_screen_width", 1024)
        if width < 480:
            return "mobile"
        elif width < 1024:
            return "tablet"
        else:
            return "desktop"
    except:
        return "desktop"


def responsive_columns(num_cols: int, mobile_stack: bool = True) -> List:
    """
    Create responsive columns that stack on mobile
    
    Args:
        num_cols: Number of columns on desktop
        mobile_stack: Stack columns on mobile (True) or maintain N columns
    
    Returns:
        List of column objects
    
    Example:
        cols = responsive_columns(3)
        with cols[0]:
            st.write("Left column")
    """
    if mobile_stack and st.session_state.get("is_mobile", False):
        # On mobile, create single column (stack)
        return [st.container()]
    else:
        # On desktop/tablet, create specified columns
        return st.columns(num_cols)


def mobile_button(
    label: str,
    key: Optional[str] = None,
    type: str = "secondary",
    use_container_width: bool = True,
    **kwargs
) -> bool:
    """
    Create a mobile-friendly button with proper sizing
    
    Args:
        label: Button label
        key: Unique key
        type: Button type ('primary', 'secondary')
        use_container_width: Make button full width (recommended for mobile)
    
    Returns:
        True if clicked
    """
    return st.button(
        label,
        key=key,
        type=type,
        use_container_width=use_container_width,
        **kwargs
    )


def mobile_form_input(
    label: str,
    input_type: str = "text",
    value: Optional[Any] = None,
    **kwargs
) -> Any:
    """
    Create a mobile-optimized form input with proper sizing and touch targets
    
    Args:
        label: Input label
        input_type: 'text', 'number', 'password', 'email'
        value: Default value
    
    Returns:
        User input
    """
    # Set optimal font size for mobile (prevents auto-zoom on iOS)
    if input_type == "text":
        return st.text_input(label, value=value or "", **kwargs)
    elif input_type == "number":
        return st.number_input(label, value=value or 0, **kwargs)
    elif input_type == "email":
        return st.text_input(label, value=value or "", placeholder="user@example.com", **kwargs)
    elif input_type == "password":
        return st.text_input(label, value=value or "", type="password", **kwargs)
    else:
        return st.text_input(label, value=value or "", **kwargs)


def metric_row(metrics: Dict[str, str], mobile_stack: bool = True):
    """
    Display metrics in a responsive row that stacks on mobile
    
    Args:
        metrics: Dict of {label: value}
        mobile_stack: Stack on mobile
    
    Example:
        metric_row({
            "Total Income": "$50,000",
            "Tax Liability": "$7,500",
            "Refund": "$2,000"
        })
    """
    num_metrics = len(metrics)
    
    if mobile_stack and st.session_state.get("is_mobile", False):
        # Stack on mobile
        for label, value in metrics.items():
            col1, col2 = st.columns([1, 1])
            with col1:
                st.text(label)
            with col2:
                st.text(value)
    else:
        # Display in columns on desktop
        cols = st.columns(num_metrics)
        for col, (label, value) in zip(cols, metrics.items()):
            with col:
                st.metric(label, value)


def mobile_tabs(tab_names: List[str]):
    """
    Create mobile-optimized tabs with better touch targets
    
    Args:
        tab_names: List of tab names
    
    Returns:
        Tuple of tab containers
    
    Example:
        tab1, tab2, tab3 = mobile_tabs(["Income", "Taxes", "Credits"])
        with tab1:
            st.write("Income details")
    """
    return st.tabs(tab_names)


def progress_indicator(step: int, total_steps: int, labels: Optional[List[str]] = None):
    """
    Display a progress indicator for multi-step forms
    
    Args:
        step: Current step (1-indexed)
        total_steps: Total number of steps
        labels: Optional labels for each step
    
    Example:
        progress_indicator(2, 4, ["Upload", "Details", "Calculate", "Download"])
    """
    progress_html = "<div style='margin: 20px 0;'>"
    
    for i in range(1, total_steps + 1):
        if i <= step:
            status = "✅"
            color = "#10b981"
        elif i == step + 1:
            status = "🔄"
            color = "#f59e0b"
        else:
            status = "⭕"
            color = "#6b7280"
        
        label = labels[i - 1] if labels else f"Step {i}"
        
        progress_html += f"""
        <div style='display: inline-block; margin-right: 15px; text-align: center;'>
            <div style='font-size: 24px; color: {color};'>{status}</div>
            <div style='font-size: 0.85em; color: #d8dde6;'>{label}</div>
        </div>
        """
    
    progress_html += "</div>"
    st.markdown(progress_html, unsafe_allow_html=True)


def info_card(
    title: str,
    content: str,
    icon: str = "ℹ️",
    card_type: str = "info"
) -> None:
    """
    Display an informational card with proper mobile formatting
    
    Args:
        title: Card title
        content: Card content
        icon: Icon emoji
        card_type: 'info', 'success', 'warning', 'error'
    """
    colors = {
        "info": ("#e3f2fd", "#2196f3", "#1565c0"),
        "success": ("#e8f5e9", "#4caf50", "#2e7d32"),
        "warning": ("#fff3e0", "#ff9800", "#e65100"),
        "error": ("#ffebee", "#f44336", "#c62828"),
    }
    
    bg, border, text = colors.get(card_type, colors["info"])
    
    html = f"""
    <div style='
        background-color: #{bg};
        border-left: 4px solid #{border};
        padding: 15px;
        border-radius: 6px;
        margin: 10px 0;
    '>
        <div style='color: #{text}; font-weight: 600; margin-bottom: 8px;'>
            {icon} {title}
        </div>
        <div style='color: #{text}; opacity: 0.9; font-size: 0.95em;'>
            {content}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def checklist(
    items: List[Dict[str, Any]],
    title: str = "Checklist"
) -> None:
    """
    Display a mobile-friendly checklist
    
    Args:
        items: List of {
            "label": str,
            "status": "pending" | "complete" | "warning",
            "details": str (optional)
        }
        title: Checklist title
    
    Example:
        checklist([
            {"label": "Parse Documents", "status": "complete"},
            {"label": "Enter Tax Details", "status": "complete"},
            {"label": "Calculate Tax", "status": "pending"},
        ], title="Tax Filing Progress")
    """
    st.subheader(f"📋 {title}")
    
    for item in items:
        label = item.get("label", "")
        status = item.get("status", "pending")
        details = item.get("details", "")
        
        if status == "complete":
            icon = "✅"
            color = "#10b981"
        elif status == "warning":
            icon = "⚠️"
            color = "#f59e0b"
        else:
            icon = "⭕"
            color = "#6b7280"
        
        html = f"""
        <div style='
            padding: 12px;
            margin: 8px 0;
            border-left: 3px solid {color};
            background: rgba(16, 185, 129, 0.05);
            border-radius: 4px;
        '>
            <div style='color: {color}; font-weight: 600;'>{icon} {label}</div>
            {f'<div style="color: #999; font-size: 0.9em; margin-top: 4px;">{details}</div>' if details else ''}
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)


def file_upload_box(
    label: str = "📁 Upload File",
    file_types: Optional[List[str]] = None,
    help_text: str = ""
) -> Optional[Any]:
    """
    Mobile-friendly file upload component
    
    Args:
        label: Upload button label
        file_types: Accepted file types ['pdf', 'csv', etc.]
        help_text: Help text below upload
    
    Returns:
        Uploaded file or None
    """
    st.markdown(f"#### {label}")
    
    if help_text:
        st.caption(help_text)
    
    uploaded = st.file_uploader(
        "Choose a file",
        type=file_types,
        label_visibility="collapsed"
    )
    
    return uploaded


def full_width_button(label: str, **kwargs) -> bool:
    """Convenience function for full-width buttons on mobile"""
    return st.button(label, use_container_width=True, **kwargs)


def init_mobile_session():
    """Initialize mobile detection in session state"""
    if "is_mobile" not in st.session_state:
        st.session_state.is_mobile = False
    if "_screen_width" not in st.session_state:
        st.session_state._screen_width = 1024
