import os
import pandas as pd
import django

# 1. Django Settings initialize karein (apne project ka sahi naam 'myproject' ki jagah likhein)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clg.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def import_students_from_excel(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' nahi mili!")
        return

    try:
        # Excel file ko read karein
        df = pd.read_excel(file_path)
        
        # 🔥 Sabhi columns ke naam me se aaspas ki extra spaces hatayein (Error Fix)
        df.columns = df.columns.str.strip()
        
        created_count = 0
        skipped_count = 0

        for index, row in df.iterrows():
            # Data read karke extra spaces clean karein
            email = str(row['Email Id']).strip()
            roll_no = str(row['Roll No.']).strip()
            mobile_no = str(row['Mobile No.']).strip()
            education = str(row['Your Educations']).strip()
            student_name = str(row['Name of Student']).strip()

            # Excel numbers me lagne wale '.0' float format ko clear karein
            if roll_no.endswith('.0'): roll_no = roll_no.split('.')[0]
            if mobile_no.endswith('.0'): mobile_no = mobile_no.split('.')[0]

            # Required details check karein
            if not email or email == 'nan' or not roll_no or roll_no == 'nan':
                print(f"Skipped Row {index+2}: Email ya Roll No khali hai.")
                skipped_count += 1
                continue

            # Django user me unique identity ke liye email ko username bana rahe hain
            username_field = email 

            # Check karein ki user database me pehle se toh nahi hai
            if not User.objects.filter(username=username_field).exists():
                
                # Roll No ko default password banayenge jo securely HASH hoga
                password_to_hash = roll_no 

                # User account create karna aapke exact model fields ke sath
                User.objects.create_user(
                    username=username_field,
                    email=email,
                    password=password_to_hash,
                    first_name=student_name,  # 'Name of Student' column se
                    phone=mobile_no,          # Aapke model ka 'phone' field
                    study=education,          # Aapke model ka 'study' field
                    category='STUDENT',       # CATEGORY_CHOICES me se 'STUDENT'
                    deprtment_id=1            # Department ki default value 1
                )
                print(f"Success: Student {student_name} ({email}) ka account securely ban gaya.")
                created_count += 1
            else:
                print(f"Skipped: User {email} pehle se exist karta hai.")
                skipped_count += 1
                
        print(f"\n--- Final Execution Report ---")
        print(f"Total Accounts Created: {created_count}")
        print(f"Total Skipped: {skipped_count}")

    except Exception as e:
        print(f"Koi error aayi: {e}")

if __name__ == '__main__':
    # Apni Excel file ka sahi naam aur path yahan dalein
    excel_file_path = 'students_data.xlsx' 
    import_students_from_excel(excel_file_path)
