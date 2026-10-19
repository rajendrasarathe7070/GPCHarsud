import os
import pandas as pd
import django

# Django Settings Initialize karein
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clg.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import StudentEngagement  # Apne app ka sahi naam likhein

User = get_user_model()

def update_branch_by_email():
    excel_path = 'students_data_template.xlsx'
    
    # Excel read karein aur headers ke extra spaces saaf karein
    df = pd.read_excel(excel_path)
    df.columns = df.columns.str.strip()

    updated_count = 0
    not_found_count = 0

    print("🚀 Email se Branch update loop shuru ho raha hai...")

    for index, row in df.iterrows():
        excel_email = str(row.get('Email Id', '')).strip()
        excel_branch = str(row.get('Branch', '')).strip()

        # Check karein ki email aur branch dono khali na hon
        if excel_email and excel_branch and excel_email != 'nan' and excel_branch != 'nan':
            
            # 1. User table me email match karke user object nikaalein
            user_obj = User.objects.filter(email=excel_email).first()

            if user_obj:
                # 2. StudentEngagement table me user_id se match karke branch_of_student fill karein
                updated_rows = StudentEngagement.objects.filter(user_id=user_obj.id).update(
                    branch_of_student=excel_branch
                )
                
                if updated_rows > 0:
                    print(f"✅ Success [Row {index+2}]: Email {excel_email} ke liye branch_of_student = '{excel_branch}' copy-paste ho gaya.")
                    updated_count += 1
                else:
                    print(f"⚠️ Alert [Row {index+2}]: User mila par StudentEngagement table me iski row nahi mili.")
            else:
                print(f"❌ Match Failed [Row {index+2}]: Email {excel_email} ka koi user database me nahi mila.")
                not_found_count += 1

    print(f"\n📊 Summary -> Total Updated: {updated_count}, Not Found: {not_found_count}")

if __name__ == '__main__':
    update_branch_by_email()
