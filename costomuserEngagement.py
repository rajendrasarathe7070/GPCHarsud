import os
import pandas as pd
import django
from decimal import Decimal

# Django Settings initialize karein (apne project ka sahi naam 'myproject' ki jagah likhein)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clg.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from core.models import StudentEngagement  # Apne app ka sahi naam likhein

User = get_user_model()

def parse_boolean(value):
    if pd.isna(value):
        return False
    val_str = str(value).strip().lower()
    if val_str in ['yes', 'y', '1', '1.0', 'true']:
        return True
    return False

def parse_decimal(value):
    if pd.isna(value) or str(value).strip().lower() in ['nan', '', 'null']:
        return None
    try:
        return Decimal(str(value).strip())
    except Exception:
        return None

def parse_integer(value):
    if pd.isna(value):
        return 0
    try:
        return int(float(str(value).strip()))
    except Exception:
        return 0

def import_data_by_matching_user(file_path):
    if not os.path.exists(file_path):
        print(f"❌ Error: File '{file_path}' nahi mili!")
        return

    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        
        success_count = 0
        skipped_count = 0
        not_found_count = 0

        print("🚀 User Matching loop shuru ho raha hai...")

        for index, row in df.iterrows():
            try:
                # Excel se identity fields nikallein
                email_from_excel = str(row.get('Email Id', '')).strip()
                roll_no_from_excel = str(row.get('Roll No.', '')).strip()
                student_name = str(row.get('Name of Student', '')).strip()

                if roll_no_from_excel.endswith('.0'): 
                    roll_no_from_excel = roll_no_from_excel.split('.')[0]

                if not email_from_excel or email_from_excel == 'nan':
                    print(f"⚠️ Row {index+2}: Email khali hai, isliye skip kiya.")
                    skipped_count += 1
                    continue

                # 🔥 LOGIC STEP: Database me is Email ka User dhoondein aur uski Correct ID nikaalein
                matched_user = User.objects.filter(email=email_from_excel).first()

                if not matched_user:
                    print(f"❌ Match Failed [Row {index+2}]: Email '{email_from_excel}' ka koi user login account database me nahi mila. Pehle user create karein.")
                    not_found_count += 1
                    continue

                # Agar user mil gaya, toh uski correct ID humare paas aa gayi: matched_user.id
                print(f"🔍 Match Found! Email '{email_from_excel}' ki correct User ID '{matched_user.id}' mili.")

                # Baaki ka saara data parsed tarike se read karein
                p_year = parse_integer(row.get('Passout Year'))
                got_place = parse_boolean(row.get('Get Placement\n(Yes/No)') or row.get('Get Placement (Yes/No)'))
                comp_name = str(row.get('If Yes\nName of Placed Company', '')).strip()
                if comp_name == 'nan': comp_name = None
                pkg = parse_decimal(row.get('Package in\nLPA') or row.get('Package in LPA'))
                offer_details = str(row.get('Offer Letter\nDetails', '')).strip()
                if offer_details == 'nan': offer_details = None

                higher_stud = parse_boolean(row.get('Opted for Higher\nStudies (Yes/No)') or row.get('Opted for Higher Studies (Yes/No)'))
                inst_name = str(row.get('Institute Name', '')).strip()
                if inst_name == 'nan': inst_name = None
                
                entrance = str(row.get('Entrance Exam\nDetails (CAT,\nGATE,\nOTHERS)', '')).strip()
                if entrance == 'nan': entrance = None

                entrepreneur = parse_boolean(row.get('Opted for\nEntrepreneurship/\nSelf Employment') or row.get('Opted for Entrepreneurship/Self Employment'))
                work_nature = str(row.get('Nature of Work', '')).strip()
                if work_nature == 'nan': work_nature = None
                turnover = parse_decimal(row.get('Annual\nTurnover\nin LPA') or row.get('Annual Turnover in LPA'))

                comp_exams = parse_boolean(row.get('Others\nPreparing for\nCompetitive Exam\n(UPSC, SSC,\nMPPSC, Banking,', ''))
                not_engaged = parse_boolean(row.get('Not Engaged till\nNow (Yes/No)', ''))

                with transaction.atomic():
                    # Conflict se bachne ke liye update_or_create use kar rahe hain
                    # Taaki agar hum is row ko dobara chalayein toh duplicate error na aaye balki data update ho jaye
                    engagement_obj, created = StudentEngagement.objects.update_or_create(
                        user_id=matched_user.id,  # 🔥 Corrected User ID mapping
                        defaults={
                            'roll_no': roll_no_from_excel,
                            'passout_year': p_year,
                            'got_placement': got_place,
                            'company_name': comp_name,
                            'package_lpa': pkg,
                            'offer_letter_details': offer_details,
                            'opted_for_higher_studies': higher_stud,
                            'higher_studies_institute': inst_name,
                            'entrance_exam_details': entrance,
                            'opted_for_entrepreneurship': entrepreneur,
                            'nature_of_work': work_nature,
                            'annual_turnover_lpa': turnover,
                            'preparing_for_competitive_exams': comp_exams,
                            'not_engaged_till_now': not_engaged
                        }
                    )

                    if created:
                        print(f"✅ Success [Row {index+2}]: Student {student_name} ka naya engagement data fill ho gaya.")
                    else:
                        print(f"🔄 Updated [Row {index+2}]: Student {student_name} ka data conflict hone ki wajah se fresh data se update ho gaya.")
                    
                    success_count += 1

            except Exception as row_error:
                print(f"❌ Error [Row {index+2}]: Row level par issue aaya. Wajah: {row_error}")
                skipped_count += 1

        print(f"\n📊 --- Execution Summary Report ---")
        print(f"Total Matches & Data Filled: {success_count}")
        print(f"Total Skipped due to Errors: {skipped_count}")
        print(f"Total Skipped because User not in DB: {not_found_count}")

    except Exception as e:
        print(f"💥 Poori script me badi error aayi: {e}")

if __name__ == '__main__':
    excel_file_path = 'students_data_template.xlsx'
    import_data_by_matching_user(excel_file_path)
