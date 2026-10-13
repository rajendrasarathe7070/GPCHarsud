import os
import django

# Django environment setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clg.settings') 
django.setup()

from django.core.management import call_command

# Pura data UTF-8 format me write karne ke liye (admin ko exclude kiya hai)
with open('mysql_data_fixed.json', 'w', encoding='utf-8') as f:
    try:
        call_command(
            'dumpdata', 
            database='mysql_db', 
            natural_foreign=True, 
            natural_primary=True, 
            exclude=['contenttypes', 'auth.Permission', 'admin'], # <-- Yahan 'admin' add kiya
            indent=4, 
            stdout=f
        )
        print("🎉 Success! Nayi mysql_data_fixed.json file ban gayi hai.")
    except Exception as e:
        print(f"❌ Error aayi: {e}")
