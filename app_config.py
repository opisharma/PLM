# app_config.py

# --- Centralized Theme and Language Configuration ---

# Global variables to hold the current state
CURRENT_THEME = "light"
CURRENT_LANGUAGE = "en"

THEMES = {
    "light": {
        "bg": "#f8f9fc",
        "fg": "#2c3e50",
        "card_bg": "#ffffff",
        "header_bg": "#2c3e50",
        "header_fg": "#ffffff",
        "footer_bg": "#34495e",
        "footer_fg": "#ecf0f1",
        "entry_bg": "#ffffff",
        "entry_fg": "#000000",
        "button_bg": "#3498db",
        "button_fg": "#ffffff",
    },
    "dark": {
        "bg": "#2c3e50",
        "fg": "#ecf0f1",
        "card_bg": "#34495e",
        "header_bg": "#1a252f",
        "header_fg": "#ffffff",
        "footer_bg": "#1a252f",
        "footer_fg": "#ecf0f1",
        "entry_bg": "#5d6d7e",
        "entry_fg": "#ffffff",
        "button_bg": "#2980b9",
        "button_fg": "#ffffff",
    },
}

def get_theme_colors():
    """Returns the color dictionary for the current theme."""
    return THEMES.get(CURRENT_THEME, THEMES["light"])

def set_theme(theme_name):
    """Sets the global application theme."""
    global CURRENT_THEME
    if theme_name in THEMES:
        CURRENT_THEME = theme_name

def set_language(lang_code):
    """Sets the global application language."""
    global CURRENT_LANGUAGE
    CURRENT_LANGUAGE = lang_code
