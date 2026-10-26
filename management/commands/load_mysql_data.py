import mysql.connector
from django.core.management.base import BaseCommand
from your_app_name.models import pyq  # 'your_app_name' को अपने असली ऐप नाम से बदलें
from django.utils.timezone import make_aware
from datetime import datetime

class Command(BaseCommand):
    help = 'Local MySQL database se Django model me data fill karne ki script'

    def handle(self, *args, **options):
        # 1. Local MySQL Database Connection की जानकारी भरें
        try:
            mysql_conn = mysql.connector.connect(
                host="localhost",
                user="root",        # अपना MySQL यूजरनेम डालें
                password="231208", # अपना MySQL पासवर्ड डालें
                database="diploma_papers_db.question_papers"        # अपना MySQL डेटाबेस नाम डालें
            )
            cursor = mysql_conn.cursor(dictionary=True) # dictionary=True से डेटा कॉलम नाम के साथ मिलता है
            self.stdout.write(self.style.SUCCESS("MySQL Database se successfully connect ho gaye!"))
        except mysql.connector.Error as err:
            self.stdout.write(self.style.ERROR(f"Database connection fail: {err}"))
            return

        # 2. अपनी लोकल MySQL टेबल से डेटा निकालने की क्वेरी
        # 'your_old_table' को अपनी MySQL टेबल के नाम से बदलें
        query = "SELECT paper_code, paper_name, year, session, pdf_link, pdf_file FROM your_old_table"
        cursor.execute(query)
        rows = cursor.fetchall()

        self.stdout.write(f"Total {len(rows)} records mile. Django me insert ho raha hai...")

        count = 0
        # 3. डेटा को Django ORM के ज़रिए लूप में सेव करना
        for row in rows:
            # duplicate एंट्रीज से बचने के लिए safe check (optional)
            # यहाँ माना गया है कि paper_code और year का कॉम्बिनेशन यूनिक हो सकता है
            exists = pyq.objects.filter(
                paper_code=row['paper_code'], 
                year=row['year'], 
                session=row['session']
            ).exists()

            if not exists:
                pyq.objects.create(
                    paper_code=row['paper_code'],
                    paper_name=row['paper_name'],
                    year=row['year'],
                    session=row['session'],
                    pdf_link=row['pdf_link'],
                   
                )
                count += 1

        # Connection बंद करें
        cursor.close()
        mysql_conn.close()

        self.stdout.write(self.style.SUCCESS(f"Badhai ho! Total {count} naye records fill ho chuke hain."))
