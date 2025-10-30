# localization.py

from app_config import CURRENT_LANGUAGE

TRANSLATIONS = {
    "en": {
        "dashboard_title": "🧠 Life Manager Dashboard",
        "welcome_message": "✨ Welcome {user}! Manage your life efficiently ✨",
        "pending_tasks": "Pending Tasks",
        "active_meds": "Active Meds",
        "active_goals": "Active Goals",
        "monthly_expense": "Monthly Expense",
        "task_management": "Task Management",
        "expense_tracker": "Expense Tracker",
        "goal_setting": "Goal Setting",
        "medication_reminder": "Medication Reminder",
        "settings_config": "Settings & Config",
        "footer_text": "💡 Manage your life efficiently with our integrated system",
        "settings_title": "🔧 Settings & Configuration",
        "back_to_dashboard": "🏠 Back to Dashboard",
        "app_settings": "⚙️ Application Settings",
        "current_user": "👤 Current User: {user}",
        "direct_access_mode": "🌟 Direct Access Mode Enabled",
        "restart_app": "🔄 Restart Application",
        "theme_selection": "🎨 Select Theme",
        "light_theme": "Light",
        "dark_theme": "Dark",
        "language_selection": "🌐 Select Language",
        "english": "English",
        "bengali": "Bengali",
        "save_settings": "💾 Save and Restart",
        "restart_prompt_title": "Restart Required",
        "restart_prompt_message": "A restart is required to apply all changes. Restart now?",
    },
    "bn": {
        "dashboard_title": "🧠 লাইফ ম্যানেজার ড্যাশবোর্ড",
        "welcome_message": "✨ স্বাগতম {user}! আপনার জীবন দক্ষতার সাথে পরিচালনা করুন ✨",
        "pending_tasks": "অমীমাংসিত কাজ",
        "active_meds": "সক্রিয় ঔষধ",
        "active_goals": "সক্রিয় লক্ষ্য",
        "monthly_expense": "মাসিক খরচ",
        "task_management": "টাস্ক ম্যানেজমেন্ট",
        "expense_tracker": "খরচ ট্র্যাকার",
        "goal_setting": "লক্ষ্য নির্ধারণ",
        "medication_reminder": "ঔষধ অনুস্মারক",
        "settings_config": "সেটিংস এবং কনফিগারেশন",
        "footer_text": "💡 আমাদের সমন্বিত সিস্টেমের সাথে আপনার জীবন দক্ষতার সাথে পরিচালনা করুন",
        "settings_title": "🔧 সেটিংস এবং কনফিগারেশন",
        "back_to_dashboard": "🏠 ড্যাশবোর্ডে ফিরে যান",
        "app_settings": "⚙️ অ্যাপ্লিকেশন সেটিংস",
        "current_user": "👤 বর্তমান ব্যবহারকারী: {user}",
        "direct_access_mode": "🌟 সরাসরি অ্যাক্সেস মোড সক্রিয়",
        "restart_app": "🔄 অ্যাপ্লিকেশন পুনরায় চালু করুন",
        "theme_selection": "🎨 থিম নির্বাচন করুন",
        "light_theme": "লাইট",
        "dark_theme": "ডার্ক",
        "language_selection": "🌐 ভাষা নির্বাচন করুন",
        "english": "ইংরেজি",
        "bengali": "বাংলা",
        "save_settings": "💾 সংরক্ষণ এবং পুনরায় চালু করুন",
        "restart_prompt_title": "পুনরায় চালু করা প্রয়োজন",
        "restart_prompt_message": "সমস্ত পরিবর্তন প্রয়োগ করার জন্য একটি পুনঃসূচনা প্রয়োজন। এখন পুনরায় চালু করবেন?",
    }
}

def get_text(key, **kwargs):
    """
    Fetches a translated string for the given key in the current language.
    Falls back to English if the key is not found in the current language.
    """
    lang_dict = TRANSLATIONS.get(CURRENT_LANGUAGE, TRANSLATIONS["en"])
    template = lang_dict.get(key, key)
    return template.format(**kwargs)
