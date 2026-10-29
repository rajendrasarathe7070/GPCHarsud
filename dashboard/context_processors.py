from .config import DASHBOARD_CONFIG
from .utils import has_view_perm, get_model

def sidebar_menus(request):
    if not request.user.is_authenticated:
        return {}
    
    allowed_tables = []
    
    # Staff ho ya Student, dono ke liye same logic chalega.
    # user.has_perm() automatically User permissions + Group permissions check karta hai.
    for cfg in DASHBOARD_CONFIG:
        # Agar user ke paas view permission hai
        if has_view_perm(request.user, cfg["key"]):
            model = get_model(cfg["key"])
            if model:  # Make sure model exists in DB
                allowed_tables.append({
                    "key": cfg["key"],
                    "label": cfg["label"],
                    "icon": cfg.get("icon", "bi-table"),
                })
                
    return {"sidebar_tables": allowed_tables}