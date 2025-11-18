"""
Mobile Sidebar Toggle Button Utility
Provides a consistent mobile-friendly sidebar toggle across all pages
"""

import streamlit as st

def add_mobile_sidebar_toggle():
    """
    Add a persistent mobile sidebar toggle button to the page.
    Call this at the beginning of any page to enable the toggle button.
    """
    st.markdown("""
    <style>
        /* Mobile sidebar toggle button - Always visible on mobile */
        .sidebar-toggle-btn {
            position: fixed;
            top: 12px;
            left: 12px;
            z-index: 10000;
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            border: 3px solid #10b981;
            border-radius: 10px;
            cursor: pointer;
            color: white;
            font-size: 24px;
            font-weight: bold;
            display: none;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
            padding: 0;
            font-family: Arial, sans-serif;
            line-height: 1;
        }
        
        .sidebar-toggle-btn:hover {
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
            transform: scale(1.08);
            box-shadow: 0 6px 16px rgba(16, 185, 129, 0.6);
        }
        
        .sidebar-toggle-btn:active {
            transform: scale(0.92);
        }
        
        /* Show on mobile and tablet */
        @media (max-width: 1024px) {
            .sidebar-toggle-btn {
                display: flex !important;
            }
        }
    </style>
    
    <button class="sidebar-toggle-btn" onclick="toggleSidebar()" title="Toggle Sidebar">☰</button>
    
    <script>
        function toggleSidebar() {
            // Find the sidebar element
            const sidebar = document.querySelector('[data-testid="stSidebar"]');
            
            if (sidebar) {
                // Check if sidebar is currently visible
                const isVisible = sidebar.offsetWidth > 0;
                
                if (isVisible) {
                    // Hide sidebar by clicking the collapse button
                    const collapseBtn = document.querySelector('[data-testid="collapsedControl"]');
                    if (collapseBtn) {
                        collapseBtn.click();
                    }
                } else {
                    // Show sidebar by clicking the collapse button
                    const collapseBtn = document.querySelector('[data-testid="collapsedControl"]');
                    if (collapseBtn) {
                        collapseBtn.click();
                    }
                }
            }
            
            // Haptic feedback for mobile
            if (navigator.vibrate) {
                navigator.vibrate(20);
            }
        }
        
        // Add keyboard shortcut (Ctrl+M on desktop)
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'm') {
                toggleSidebar();
            }
        });
    </script>
    """, unsafe_allow_html=True)
