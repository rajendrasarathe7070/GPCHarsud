from django.conf import settings

APP_LABEL = getattr(settings, "DASHBOARD_APP_LABEL", "core")

# ⚠️ IMPORTANT: Key = model_name.lower() from Django
# jaisa `python manage.py shell → Model._meta.model_name` deta hai
# Class ka naam python me CamelCase hota hai, par model_name lowercase-with-underscores hota hai.
# e.g.  class Course_Department  →  "course_department"

DASHBOARD_CONFIG = [
    {"key": "info",                    "label": "Info & Alerts",          "icon": "bi-megaphone",         "group_by": "page",         "exclude_fields": []},
    {"key": "notice",                  "label": "Notices",                "icon": "bi-file-earmark",      "group_by": "notice_type",  "exclude_fields": []},
    {"key": "course_department",       "label": "Departments",            "icon": "bi-building",          "group_by": "Course_name",  "exclude_fields": []},   # ⚠️ FIXED
    {"key": "customuser",              "label": "Users",                  "icon": "bi-people",            "group_by": "category",     "exclude_fields": ["password", "last_login", "is_superuser", "is_staff", "is_active", "date_joined", "user_permissions"]},
    {"key": "studentengagement",       "label": "Student Engagement",     "icon": "bi-mortarboard",       "group_by": None,           "exclude_fields": []},
    {"key": "responsibility",          "label": "Responsibilities",       "icon": "bi-person-badge",      "group_by": "work_name",    "exclude_fields": []},
    {"key": "timetable",               "label": "Timetables",             "icon": "bi-calendar3",         "group_by": "types",        "exclude_fields": []},
    {"key": "academic_calendar",       "label": "Academic Calendar",      "icon": "bi-calendar-event",    "group_by": None,           "exclude_fields": []},
    {"key": "feecategory",             "label": "Fee Categories",         "icon": "bi-cash-coin",         "group_by": None,           "exclude_fields": []},
    {"key": "feestructure",            "label": "Fee Structure",          "icon": "bi-cash-stack",        "group_by": "frequency",    "exclude_fields": []},
    {"key": "scholarship",             "label": "Scholarships",           "icon": "bi-award",             "group_by": None,           "exclude_fields": []},
    {"key": "imp_date_and_document",   "label": "Important Dates/Docs",   "icon": "bi-journal-text",      "group_by": "types",        "exclude_fields": []},
    {"key": "pro_dte_clc_admission",   "label": "DTE/CLC Admission",      "icon": "bi-clipboard-check",   "group_by": "catogry",      "exclude_fields": []},
    {"key": "campuscategory",          "label": "Campus Categories",      "icon": "bi-image",             "group_by": None,           "exclude_fields": []},
    {"key": "campusimage",             "label": "Campus Photos",          "icon": "bi-images",            "group_by": None,           "exclude_fields": []},
    {"key": "rulseupdate_campus",      "label": "Rules & Updates",        "icon": "bi-shield-check",      "group_by": "categorys",    "exclude_fields": []},
    {"key": "placementbatch",          "label": "Placement Batches",      "icon": "bi-briefcase",         "group_by": None,           "exclude_fields": []},
    {"key": "branchplacement",         "label": "Branch Placements",      "icon": "bi-graph-up",          "group_by": None,           "exclude_fields": []},
    {"key": "syllabus",                "label": "Syllabus",               "icon": "bi-book",              "group_by": "brach",        "exclude_fields": []},
    {"key": "pyq",                     "label": "Previous Year Papers",   "icon": "bi-file-earmark-text", "group_by": None,           "exclude_fields": []},
    {"key": "category",                "label": "Cheatsheet Categories",  "icon": "bi-tags",              "group_by": None,           "exclude_fields": []},
    {"key": "cheatsheet",              "label": "Cheatsheets / Notes",    "icon": "bi-journal-code",      "group_by": None,           "exclude_fields": []},
]

STUDENT_EXTRA_CARDS = getattr(settings, "STUDENT_EXTRA_CARDS", [])

MAX_ROWS_PER_GROUP = 300
PREVIEW_LIMIT = 3