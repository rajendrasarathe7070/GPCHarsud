from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
import requests
import time
from django.utils import timezone
from decimal import Decimal
from django.conf import settings
 

class info(models.Model):
    choices_page=[
         ('academics','academics'),
         ('admissions','admissions'),
         ('campus','campus'),
         ('studentcorners','studentcorners'),
         ('placement','placement'),
    ]
    id=models.AutoField(primary_key=True)
    infos=models.CharField(null=True,blank=True,max_length=100 , verbose_name="Add Your First Alert")
    infos_2 = models.CharField(max_length=100,blank=True, null=True,verbose_name="Add Your Second Alert")
    date=models.DateField(auto_now_add=True)
    page=models.CharField(unique=True,choices=choices_page,verbose_name="Page /Category",max_length=100)
    
    def __str__(self):
        return f"{self.infos} ({self.get_page_display()})"
    # self.infos
 
# this is model for all  inmportance notices
class Notice(models.Model):
    NOTICE_TYPES = [
        ('GRAND', 'Grand Notice'),
        ('EVENTS', 'EVENTS Notice'),
        ('PLACEMENTS', 'PLACEMENTS Notice'),
       
    ]

    title = models.CharField(max_length=200, verbose_name="Notice Title")
    content = models.TextField(verbose_name="Notice Content" , default=None, null=True, blank=True)
    notice_type = models.CharField(
        max_length=10, 
        choices=NOTICE_TYPES, 
        
        verbose_name="Notice Type"
    )
    notice_pdf = models.FileField(upload_to='notices/', null=True, blank=True, verbose_name="Notice PDF")
    add_to_grand = models.BooleanField(
        default=None, 
        verbose_name="Add All Notices"
    )
    
    slug = models.SlugField(unique=True, null=True, blank=True, verbose_name="Slug")
    created_at = models.DateTimeField(auto_now_add=False, verbose_name="Created At"  , default=timezone.now)
    created_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True,  blank=True, verbose_name="Created By")

    def __str__(self):
        return f"{self.title} ({self.get_notice_type_display()})"


class Course_Department(models.Model):
    Department_name = models.CharField(max_length=100)
    Department_hod = models.CharField(max_length=100, default=None, null=True, verbose_name='HOD Name')
    hod_photo = models.ImageField(upload_to='hod_photos/', null=True, blank=True, verbose_name='HOD Photo')
    hod_qualification = models.CharField(max_length=100, default=None, null=True, verbose_name='HOD Qualification')
    hod_experience = models.PositiveIntegerField(default=0, null=True, verbose_name='HOD Experience in Years')
    Department_description = models.TextField()
    
    Department_crausal_image_1 = models.ImageField(upload_to='department_crausal/', null=True, blank=True)
    Department_crausal_image_2 = models.ImageField(upload_to='department_crausal/', null=True, blank=True)  
    Department_crausal_image_3 = models.ImageField(upload_to='department_crausal/', null=True, blank=True)
     
    TYPES = [
        ('Computer_Science','Computer_Science'),
        ('Mechanical_Engineering', 'Mechanical_Engineering'),
        ('Civil_Engineering', 'Civil_Engineering'),
        ('ET_&_TELECOMMUNICATION','ET_&_TELECOMMUNICATION'),
       
    ]
     
    Course_name = models.CharField(choices=TYPES , max_length=100,default=None, null=True, verbose_name='Course Name')
    Course_image = models.ImageField(upload_to='course_images/', null=True, blank=True, verbose_name='Course Image')
    Course_code = models.CharField(max_length=5, default=None, null=True, verbose_name='Course Code')
    # hod_Name = models.CharField(max_length=100, default=None, null=True, verbose_name='HOD Name')
    Course_duration = models.CharField(max_length=10, default=None, null=True, verbose_name='Course Duration')
    Course_eligibility = models.CharField(max_length=100, default=None, null=True, verbose_name='Course Eligibility')
    Course_seats_ppt= models.PositiveIntegerField(default=30, null=True, verbose_name='PPT Seats')
    Course_seats_eklavya= models.PositiveIntegerField(default=30, null=True , verbose_name='Eklavya Seats')
    Mode_of_study = models.CharField(max_length=50, default=None, null=True, verbose_name='Mode of Study')
 
    def __str__(self):
        return f"{self.Department_name} - {self.Course_name}"

class CustomUser(AbstractUser):
    
    CATEGORY_CHOICES = [
        ('PRINCIPAL', 'Principal'),
         ('HOD', 'Head of Department'), 
        ('TEACHING', 'Teaching Faculty'),
        ('STAFFS', 'Academic Staff'),
         ('STUDENT', 'Student'),
    ]
    slug=models.SlugField(unique=True, null=True, blank=True)
    photo=models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    
    phone = models.CharField(max_length=15, null=True,default=None, verbose_name='Phone Number')
    study = models.CharField(max_length=100,verbose_name='Your Educations',null=True)
    experience = models.PositiveIntegerField(default=0, verbose_name='Experience in Years', null=True)
    joining_date = models.DateField(  null=True,  blank=True )
    deprtment = models.ForeignKey(Course_Department, on_delete=models.SET_NULL, null=True, default=None, verbose_name='Department', related_name='users')

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='TEACHING')
    

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    
class StudentEngagement(models.Model):
    """
    छात्र के एंगेजमेंट स्टेटस के लिए मॉडल।
    यह आपके Custom User Model से जुड़ा हुआ है।
    """
    
    # Custom User Model से वन-टू-वन रिलेशन (एक यूजर का एक ही एंगेजमेंट रिकॉर्ड होगा)
    # अगर एक यूजर के कई सालों के अलग-अलग रिकॉर्ड रखने हैं, तो ForeignKey का उपयोग करें।
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="engagement_details",
        verbose_name="Student User"
        ,blank=True, null=True
    )
    
    # --- Remaining Student Details ---
    # नाम, मोबाइल, ईमेल, डिपार्टमेंट और जॉइनिंग डेट यूजर मॉडल से ही एक्सेस होंगे
    roll_no = models.CharField(max_length=50, unique=True, verbose_name="Roll No.")
    branch_of_student= models.CharField(max_length=50, blank=True, null=True)
    passout_year = models.CharField(verbose_name="Passout Year" , max_length=50 , blank=True, null=True)

    # --- Placement Details ---
    got_placement = models.BooleanField(default=False, verbose_name="Got Placement (Yes/No)")
    company_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="If Yes, Name of Placed Company")
    package_lpa = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Package in LPA")
    offer_letter_details = models.TextField(blank=True, null=True, verbose_name="Offer Letter Details")

    # --- Higher Studies Details ---
    opted_for_higher_studies = models.BooleanField(default=False, verbose_name="Opted for Higher Studies (Yes/No)")
    higher_studies_institute = models.CharField(max_length=255, blank=True, null=True, verbose_name="If yes, Institute Name")
    entrance_exam_details = models.CharField(max_length=100, blank=True, null=True, verbose_name="Entrance Exam Details (CAT, GATE, OTHERS)")

    # --- Entrepreneurship/Self Employment Details ---
    opted_for_entrepreneurship = models.BooleanField(default=False, verbose_name="Opted for Entrepreneurship/Self Employment")
    nature_of_work = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nature of Work")
    annual_turnover_lpa = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, verbose_name="Annual Turnover in LPA")

    # --- Others / Not Engaged ---
    preparing_for_competitive_exams = models.BooleanField(default=False, verbose_name="Preparing for Competitive Exams (UPSC, SSC, MPPSC, Banking, etc.)")
    not_engaged_till_now = models.BooleanField(default=False, verbose_name="Not Engaged till Now (Yes/No)")

    def __str__(self):
        # यहाँ हम सीधे यूजर मॉडल से छात्र का नाम और डिपार्टमेंट एक्सेस कर रहे हैं
        return f"{self.user.first_name} ({self.roll_no} "

# --- Master Responsibility Table (Pehle ki tarah hi single table) ---
class Responsibility(models.Model):
    WORK_CHOICES = [
       ('ADMISSION', 'Admission Desk In-Charge'),
        ('LIBRARY', 'Library Head'),
        ('EXAM', 'Exam Cell Coordinator'),
        ('SPORTS', 'Sports Committee Head'),
        ('PLACEMENT', 'Training & Placement Officer'),
        ('HOSTEL', 'Hostel Warden'),
        ('ANTI_RAGGING', 'Anti-Ragging Squad Leader'),
        ('WEBSITE', 'College Website In-Charge'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='duties')
    work_name = models.CharField(max_length=30, choices=WORK_CHOICES, unique=False)
    work_position = models.CharField(max_length=100, null=True , default=None , blank=True, verbose_name="Position/Role in the Work") 
    assigned_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_work_name_display()} -> {self.user.get_full_name()}"

class Timetable(models.Model):
    TTtypes = [
        ('CLASS', 'Main Class timetable'),
        ('LAB', ' Lab timetable'),
    ]
    BRANCH_CHOICES = [
        ('CS', 'Computer Science'),
        ('ME', 'Mechanical Engineering'),
        ('EE', 'Electrical Engineering'),
        ('CE', 'Civil Engineering'),
    ]
    
    # यहाँ हमने सिर्फ 3 साल रखे हैं
    YEAR_CHOICES = [
        (1, '1st Year'),
        (2, '2nd Year'),
        (3, '3rd Year'),
    ]

     
    types = models.CharField(max_length=10, choices=TTtypes, verbose_name="Timetable Type" , default=None, null=True)
    branch = models.CharField(max_length=5, choices=BRANCH_CHOICES)
    year = models.IntegerField(choices=YEAR_CHOICES)
    
    timetable_image_1 = models.ImageField(upload_to='timetables/' , null=True , verbose_name="Timetable 1/2-sem", default=None)
    timetable_image_2 = models.ImageField(upload_to='timetables/' , null=True , verbose_name="Timetable 2/2-sem", default=None)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.types } == {self.branch} - Year {self.year} -  (By: {self.uploaded_by})"

class academic_calendar(models.Model):
    title = models.CharField(max_length=200, verbose_name="Calendar Title") 
    calendar_pdf = models.FileField(upload_to='academic_calendars/', null=True, blank=True, verbose_name="Calendar PDF")
    created_at = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return f"{self.title} (By: {self.created_at.strftime('%Y-%m-%d')})"
    
    


class FeeCategory(models.Model):
   
    name = models.CharField(max_length=255, verbose_name="फ़ीस श्रेणी का नाम (जैसे: ONE-TIME FEES)")
    order = models.PositiveIntegerField(default=1, verbose_name="दिखाने का क्रम (Order)")

    class Meta:
        verbose_name = "Fee Category"
        verbose_name_plural = "Fee Categories"
        ordering = ['order']

    def __str__(self):
        return self.name


class FeeStructure(models.Model):
    """
    विशिष्ट फ़ीस कंपोनेंट और अलग-अलग छात्रों के लिए उसका विवरण
    """
    FREQUENCY_CHOICES = [
        ('one_time', 'एक बार / एडमिशन के समय'),
        ('annual', 'सालाना'),
        ('semester', 'प्रति सेमेस्टर'),
        ('annual_semester', 'सालाना / सेमेस्टर'),
        ('monthly_semester', 'मासिक / सेमेस्टर'),
    ]

    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE, related_name='components', verbose_name="मुख्य श्रेणी")
    sub_no = models.CharField(max_length=5, verbose_name="S.No. (जैसे: A, B, C)")
    particular = models.CharField(max_length=255, verbose_name="Fee Component (फीस का प्रकार)")
    frequency = models.CharField(max_length=50, choices=FREQUENCY_CHOICES, verbose_name="Frequency (कब ली जाएगी)")
    
    # विभिन्न श्रेणियों के लिए फ़ीस (Text field रखा गया है ताकि ₹ 0.00, 免, या Govt Pay जैसी चीज़ें भी लिखी जा सकें)
    regular_amount = models.CharField(max_length=100, default="₹ 0.00", verbose_name="Regular Students (सामान्य छात्र)")
    tfw_amount = models.CharField(max_length=100, default="₹ 0.00", verbose_name="TFW Students (टी.एफ.डब्ल्यू)")
    eklavya_amount = models.CharField(max_length=100, default="₹ 0.00", verbose_name="Eklavya Hostel Students")

    class Meta:
        verbose_name = "Fee Component"
        verbose_name_plural = "Fee Components"
        ordering = ['category__order', 'sub_no']

    def __str__(self):
        return f"{self.category.name} - {self.sub_no}. {self.particular}"


class Scholarship(models.Model):
    """
    दाईं तरफ के कार्ड में दिखाई जाने वाली स्कॉलरशिप योजनाओं के लिए मॉडल
    """
    title = models.CharField(max_length=255, verbose_name="स्कॉलरशिप का नाम")
    description = models.TextField(verbose_name="योजना का संक्षिप्त विवरण")
    link = models.URLField(blank=True, null=True, verbose_name="अप्लाई करने/जानकारी की लिंक")
    is_active = models.BooleanField(default=True, verbose_name="सक्रिय है या नहीं")

    class Meta:
        verbose_name = "Scholarship Information"
        verbose_name_plural = "Scholarship Information"

    def __str__(self):
        return self.title

class Imp_date_and_document(models.Model):
    choices_types=[
        ('IMPDATES','Important Dates'),
        ('DOCUMENTS','Required Documents'),
    ]
    id=models.AutoField(primary_key=True)
    text = models.CharField(max_length=150, verbose_name="Name of Date/Document" , default=None, null=True)
    types = models.CharField(max_length=100, choices=choices_types, verbose_name="Type of Document/Date")
    date=models.DateField(auto_now_add=False)
   
    
    def __str__(self):
        return f"{self.get_types_display()}-> {self.text}"
    
class Pro_DTE_CLC_Admission(models.Model):
    id=models.AutoField(primary_key=True)
    catogry = models.CharField(max_length=50 , choices=[('DTE','Centralized Counseling Steps (DTE)') , ('CLC','College Level Counseling (CLC)')] , default=None)
    title = models.CharField(max_length=50 , null=True , default=None)
    dis = models.TextField(default=None , null=True ,verbose_name="Discription on DTE" ,)
    sub_dis = models.TextField(verbose_name="Sub-Discription on DTE",blank=True , default=None , null=True)
    
    
    
class CampusCategory(models.Model):
    
    CATEGORY_CHOICES = [
        ('main_entrance', 'Main Entrance'),
        ('academic_building', 'Academic Building'),
        ('classroom', 'Classroom'),
        ('laboratory', 'Laboratory'),
        ('library', 'Library'),
        ('playground', 'Playground'),
        ('hostel', 'Hostel'),
        ('auditorium', 'Auditorium'),
        ('canteen', 'Canteen'),
        ('events', 'Events'),
    ]
    
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    category_img = models.ImageField(upload_to='campus_photos/' , blank=True, null=True)

    def __str__(self):
        return self.get_name_display()

class CampusImage(models.Model):
    # Foreign Key की मदद से एक कैटेगरी में जितनी चाहें उतनी इमेजेस जोड़ सकते हैं
    category = models.ForeignKey(CampusCategory, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='campus_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category.get_name_display()} - Image {self.id}"
 
 
    
   

class RulseUpdate_Campus(models.Model):
    CATEGORY = [('HOSTELUPDATE','Hostel Update'),
                ('HOSTELRULSE','Hostel Rulse'),
                ('LIBRARYUPDATE','Library updates book'),
                ('LIBRARYRULSE','Library rulse'),
                ('LABUPDATE','Lab updates practicals'),
                ('LABRULSE','Lab rulse'),
                
                ]
    id= models.AutoField(primary_key=True)
    text = models.CharField(max_length=100 , null=True,blank=True)
    categorys = models.CharField(choices=CATEGORY , default=None , max_length=50)
    uploaded_at = models.DateField(auto_now_add=True,blank=True, null=True)
    
    def __str__(self):
        return f"{self.categorys} -> {self.text} -> {self.uploaded_at}"
    
class PlacementBatch(models.Model):
    """
    प्लेसमेंट वर्ष या बैच (जैसे: Placement Drive 2025-26)
    """
    year = models.CharField(max_length=50, verbose_name="प्लेसमेंट वर्ष / बैच (जैसे: 2025-26)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Placement Batch"
        verbose_name_plural = "Placement Batches"

    def __str__(self):
        return self.year
    
    @property
    def total_students_placed(self):
        return sum(r.students_placed for r in self.branch_records.all())

    @property
    def total_offers(self):
        return sum(r.companies_visited for r in self.branch_records.all())

    @property
    def max_highest_package(self):
        # float (0.00) की जगह Decimal('0.00') का इस्तेमाल किया गया है
        packages = [r.highest_package for r in self.branch_records.all() if r.highest_package > 0]
        return max(packages) if packages else Decimal('0.00')

    @property
    def avg_package(self):
        packages = [r.average_package for r in self.branch_records.all() if r.average_package > 0]
        if not packages:
            return Decimal('0.00')
        # Decimal का सम करके उसकी लेंथ से डिवाइड किया और 2 डेसिमल प्लेस तक राउंड किया
        return (sum(packages) / len(packages)).quantize(Decimal('0.01'))

    @property
    def median_package(self):
        records = self.branch_records.all()
        packages = []
        for r in records:
            if r.highest_package > 0: packages.append(r.highest_package)
            if r.lowest_package > 0: packages.append(r.lowest_package)
            if r.average_package > 0: packages.append(r.average_package)
        
        packages = sorted(packages)
        n = len(packages)
        if n == 0:
            return Decimal('0.00')
        elif n % 2 == 1:
            return packages[n // 2].quantize(Decimal('0.01'))
        else:
            mid = n // 2
            # Decimal वैल्यूज का एवरेज निकाल कर उसे राउंड किया
            return ((packages[mid - 1] + packages[mid]) / 2).quantize(Decimal('0.01'))

    
    @classmethod
    def grand_students_placed(cls):
        # सभी बैचेस के सभी प्लेस्ड छात्रों का कुल जोड़
        return sum(batch.total_students_placed for batch in cls.objects.prefetch_related('branch_records'))

    @classmethod
    def grand_companies_visited(cls):
        # सभी बैचेस में विज़िट करने वाली कुल कंपनियाँ
        return sum(batch.total_offers for batch in cls.objects.prefetch_related('branch_records'))

    @classmethod
    def grand_highest_package(cls):
        # सभी बैचेस में से सबसे ज़्यादा हाईएस्ट पैकेज
        packages = [batch.max_highest_package for batch in cls.objects.prefetch_related('branch_records') if batch.max_highest_package > 0]
        return max(packages) if packages else Decimal('0.00')

    @classmethod
    def grand_avg_package(cls):
        
        packages = [batch.avg_package for batch in cls.objects.prefetch_related('branch_records') if batch.avg_package > 0]
        if not packages:
            return Decimal('0.00')
        return (sum(packages) / len(packages)).quantize(Decimal('0.01'))
    
    @classmethod
    def grand_lowest_package(cls):
        from .models import BranchPlacement
        packages = [r.lowest_package for r in BranchPlacement.objects.all() if r.lowest_package > 0]
        return min(packages) if packages else Decimal('0.00')

class BranchPlacement(models.Model):
    
    batch = models.ForeignKey(
        PlacementBatch, 
        on_delete=models.CASCADE, 
        related_name='branch_records', 
        verbose_name="प्लेसमेंट बैच"
    )
    s_no = models.CharField(max_length=5, verbose_name="No. / S.No. (जैसे: 1, 2, 3)")
    branch_name = models.CharField(max_length=255, verbose_name="Branch Name (शाखा का नाम)")
    
    # छात्रों की संख्या
    final_year_students = models.PositiveIntegerField(default=0, verbose_name="Number of Students in Final Year")
    students_placed = models.PositiveIntegerField(default=0, verbose_name="Number of Students Placed")
    companies_visited = models.PositiveIntegerField(default=0, verbose_name="Number of Companies Visited")
    
    # पैकेज विवरण (डिफ़ॉल्ट वैल्यू को Decimal के रूप में रखा गया है)
    highest_package = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name="Highest Package offered (LPA)")
    lowest_package = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name="Lowest Package offered (LPA)")
    average_package = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name="Average Package offered (LPA)")

    class Meta:
        verbose_name = "Branch Placement Record"
        verbose_name_plural = "Branch Placement Records"
        ordering = ['batch', 's_no']

    def __str__(self):
        return f"{self.batch.year} - {self.branch_name}"
    
    
class syllabus(models.Model):
    id = models.AutoField(primary_key=True)
    braches = [('CSE','Computer science'),
             ('CIVIL','Civil Engg.'),
             ('ET','Electronics and telycommunication'),
             ('ME','Mechanical Engg .')
    ]
    sem = [('FIRST','FIRST'),
           ('SECOND','SECOND'),
           ('THEARD','THEARD'),
           ('FOURTH','FOURTH'),
           ('FIFTH','FIFTH'),
           ('SIXTH','SIXTH'),
           ]

    brach = models.CharField(choices=braches, max_length=50 , blank=True, null=True ,verbose_name="Select Branch ")
    semester = models.CharField(choices=sem,max_length=50 , blank=True, null=True)
    syllabus = models.FileField(upload_to="syllabuss" , blank=True, null=True)
    syllabus_link = models.URLField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.brach} , {self.semester}"
    
    