import os
import sys
import django
import mysql.connector

# 1. Django Environment Setup
# 'your_project_name' को अपने असली Django प्रोजेक्ट के नाम (जिस फोल्डर में settings.py है) से बदलें
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clg.settings')
django.setup()

# Django Model को इम्पोर्ट करें
# 'your_app_name' को अपने ऐप के नाम से बदलें
from core.models import pyq

def migrate_data():
    print("MySQL से डेटा Django ORM में ट्रांसफर हो रहा है...")

    try:
        # 2. Raw MySQL Database से कनेक्ट करें
        # अपनी MySQL क्रेडेंशियल्स डालें
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="231208",
            database="diploma_papers_db"
        )
        cursor = conn.cursor(dictionary=True) # dictionary=True से कॉलम के नाम की की (key) मिलेगी

        # 3. question_papers टेबल से डेटा सेलेक्ट करें
        # कॉलम के नाम अगर आपकी टेबल में अलग हैं, तो उन्हें यहाँ बदल लें
        query = "SELECT id, paper_code, paper_name, year, session, pdf_link FROM question_papers"
        cursor.execute(query)
        rows = cursor.fetchall()

        count = 0
        for row in rows:
            # Django ORM का इस्तेमाल करके डेटा इन्सर्ट या अपडेट (get_or_create) करें
            # इससे डुप्लीकेट id होने पर एरर नहीं आएगा
            obj, created = pyq.objects.get_or_create(
                id=row['id'],
                defaults={
                    'paper_code': row['paper_code'],
                    'paper_name': row['paper_name'],
                    'year': row['year'],
                    'session': row['session'],
                    'pdf_link': row['pdf_link']
                }
            )
            if created:
                count += 1

        print(self_message := f"सफलतापूर्वक {count} नए रिकॉर्ड्स Django DB में भर दिए गए हैं!")

    except mysql.connector.Error as err:
        print(f"MySQL एरर: {err}")
    except Exception as e:
        print(f"कोई अन्य एरर आई: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    migrate_data()
