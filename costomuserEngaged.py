import os
import pandas as pd
import django

# Django Initialize
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clg.settings')
django.setup()

from core.models import StudentEngagement  # Apne app ka sahi naam likhein

def update_passout_year():
    excel_path = 'students_data_template.xlsx'
    df = pd.read_excel(excel_path)
    df.columns = df.columns.str.strip()

    for index, row in df.iterrows():
        # Excel se Roll No aur Passout Year nikalein
        excel_roll = str(row.get('Roll No.', '')).strip()
        excel_year = str(row.get('Passout Year', '')).strip()

        # Float format '.0' ko saaf karein agar ho toh
        if excel_roll.endswith('.0'): excel_roll = excel_roll.split('.')[0]
        if excel_year.endswith('.0'): excel_year = excel_year.split('.')[0]

        if excel_roll and excel_year and excel_year != 'nan':
            # Database me Roll No se direct match karke update karein
            updated_rows = StudentEngagement.objects.filter(roll_no=excel_roll).update(passout_year=excel_year)
            
            if updated_rows > 0:
                print(f"✅ Roll No: {excel_roll} -> Passout Year '{excel_year}' successfully copy-paste ho gaya.")
            else:
                print(f"❌ Roll No: {excel_roll} database me nahi mila.")

if __name__ == '__main__':
    update_passout_year()
