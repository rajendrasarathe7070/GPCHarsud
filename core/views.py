from django.shortcuts import render ,redirect 
from django.http import HttpResponse
# from .models import Paper
from django.contrib.auth.forms import UserCreationForm ,authenticate
from django.contrib import messages 
from django.contrib.auth import login 
from django.contrib.auth import logout as django_logout
from django.contrib.auth.models import  User 
# Create your views here.
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from . import models
from .models import PlacementBatch
from rest_framework import serializers
from django.db.models import Q                # (agar Q chahiye)
from .models import Notice, CheatSheet, Category
from django.contrib import messages
from .models import StudentEngagement , Course_Department

def verification(request):
    return render(request,'googled61072f71b08753c.html') 
 
def singup(request):
    if request.method=='POST':
    
        fname=request.POST.get('fname')
        lname=request.POST.get('lname')
        emil=request.POST.get('email')
        pass1=request.POST.get('passwd')
        pass2=request.POST.get('passwd2')
        
        #verification '
        print(pass1,pass2)

        if 6 < len(pass2):
            user = User.objects.create_user(
            username=emil, 
            email=emil, 
            password=pass2,
            first_name=fname,
            last_name=lname)
            user.save() #
            messages.success(request,f'{fname} your accaunt is created successfuly ! ')
        
        else:
            data={'error':'passwd is not same !'}
            return render(request,'404.html', data)
        

    # else:
        # form = UserCreationForm()
    return render(request,'index.html')

def login(request):
    if request.method=='POST':
        email=request.POST.get('email')
        pass1=request.POST.get('passwd')
        
        user=authenticate(request,username=email,password=pass1)
        if not user is None:
            login(request)
        return redirect(home)
    else:
        return render(request,'404.html')
    
@login_required
def logout(request):
    if request.method=='POST':
        django_logout(request)
        return redirect('/')
    return redirect('/')

def home(request):
    
    return render(request,"index.html")

def index(request):
    impnotices =  Notice.objects.select_related('created_by').all().order_by('-created_at')

    department_model = Course_Department.objects.all()
    # सिर्फ उन यूज़र्स को गेट करेगा जिनकी केटेगरी HOD है
  
   
    
    
    return render(request,'index.html', {'impnotices': impnotices, 'departments': department_model})

def academic(request):
    all_timetables = models.Timetable.objects.filter(types='CLASS').select_related('uploaded_by')
    department_model = models.Course_Department.objects.all()
    info = models.info.objects.filter(page='academics').first()
    academic_calendar = models.academic_calendar.objects.all().order_by('-created_at') 
    syllabuses = models.syllabus.objects.all()
    print(syllabuses)
    
    Context = {'infomsg': info, 
               'departments': department_model, 
               'academic_calendar': academic_calendar,
               'all_timetables': all_timetables}
     

    for sylabus in syllabuses:
        if sylabus.brach == 'CSE':
            Context.setdefault('CSE',[]).append(sylabus)
        elif sylabus.brach == 'CIVIL':
            Context.setdefault('CIVIL',[]).append(sylabus) 
        elif sylabus.brach == 'ME':
            Context.setdefault('ME',[]).append(sylabus)
        elif sylabus.brach == 'ET':
            Context.setdefault('ET',[]).append(sylabus)  
             
    
    print(Context['CSE'] , Context['CIVIL'])
            
    
    
    
    return render(request, 'academic.html',Context)

def admission(request):
    fee_categories = models.FeeCategory.objects.prefetch_related('components').all()
    department_model = models.Course_Department.objects.all()
    active_scholarships = models.Scholarship.objects.filter(is_active=True)
    admission_desk = models.Responsibility.objects.filter(work_name='ADMISSION').all()
    Imp_date = models.Imp_date_and_document.objects.filter(types='IMPDATES').all()
    Imp_doc = models.Imp_date_and_document.objects.filter(types='DOCUMENTS').all()
    Admission_CLC= models.Pro_DTE_CLC_Admission.objects.filter(catogry='CLC')
    Admission_DTE= models.Pro_DTE_CLC_Admission.objects.filter(catogry='DTE')
    
    info = models.info.objects.filter(page='admissions').first()
    return render(request,'Admissions.html',{'infomsg': info,'feecategories': fee_categories,'scholarships': active_scholarships, 'departments': department_model, 'admission_desk': admission_desk , 'Imp_date': Imp_date, 'Imp_doc': Imp_doc , 'CLCS':Admission_CLC , 'DTES':Admission_DTE})



def campuslife(request):
    # categories = models.CampusCategory.objects.all()
    info = models.info.objects.filter(page='campus').first()
    categories = models.CampusCategory.objects.prefetch_related('images').all()
    hostelrules = models.RulseUpdate_Campus.objects.filter(categorys='HOSTELRULSE')
    hostelupdate = models.RulseUpdate_Campus.objects.filter(categorys='HOSTELUPDATE')
    libraryupdate = models.RulseUpdate_Campus.objects.filter(categorys='LIBRARYUPDATE')
    libraryrulse = models.RulseUpdate_Campus.objects.filter(categorys='LIBRARYRULSE')  
    labupdate = models.RulseUpdate_Campus.objects.filter(categorys='LABUPDATE')
    labrulse = models.RulseUpdate_Campus.objects.filter(categorys='LABRULSE')
    
    print(libraryrulse,libraryupdate)
    campusdictionary = {'infomsg':info,
                        'categories':categories ,
                        'rulses': hostelrules,
                        'hostelupdates':hostelupdate,
                        'libraryupdates':libraryupdate ,
                        'libraryrulses':libraryrulse,
                        'labupdates':labupdate ,
                        'labrulses':labrulse,
                        
                        }
    return render(request,'CampusLife.html',campusdictionary)

def placements(request):
    all_batches = models.PlacementBatch.objects.prefetch_related('branch_records').order_by('-year')
    
     
    placement_students = models.CustomUser.objects.filter(
        category='STUDENT', 
        engagement_details__isnull=False
    ).select_related('engagement_details').filter(engagement_details__got_placement=True)

    # 2. ड्रॉपडाउन फ़िल्टर के लिए वेरिएबल्स के नाम पूरी तरह यूनीक (Unique) रखें
    filter_batches = models.StudentEngagement.objects.filter(got_placement=True).values_list('passout_year', flat=True).distinct()
    filter_branches = models.StudentEngagement.objects.filter(got_placement=True).values_list('branch_of_student', flat=True).distinct()

    # 3. रिक्वेस्ट से फ़िल्टर वैल्यूज़ प्राप्त करना
    selected_filter_batch = request.GET.get('batch_id')     
    selected_filter_branch = request.GET.get('branch')       

    # 4. यदि यूज़र ने फ़िल्टर चुना है, तो केवल छात्रों की लिस्ट को फ़िल्टर करें
    if selected_filter_batch:
        placement_students = placement_students.filter(engagement_details__passout_year=selected_filter_batch)
    
    if selected_filter_branch:
        placement_students = placement_students.filter(engagement_details__branch_of_student=selected_filter_branch)

    # 5. कॉन्टेक्स्ट (Context) डिक्शनरी - इसमें आपके पुराने वेरिएबल्स को बिना छेड़े नए फ़िल्टर जोड़े गए हैं
    
    
    selected_batch_id = request.GET.get('batch_id')
    
     
    selected_batch = None
    if all_batches.exists():
        if selected_batch_id:
            
            selected_batch = next((b for b in all_batches if str(b.id) == str(selected_batch_id)), all_batches.first())
        else:
            selected_batch = all_batches.first()
            
            
    context = {
        # पुराने वेरिएबल्स (जिन्हें आपने बताया, इन्हें बिल्कुल नहीं बदला गया है)
        'all_batches': all_batches,       
        'selected_batch': selected_batch, 
        'grand_students_placed': PlacementBatch.grand_students_placed(),
        'grand_companies_visited': PlacementBatch.grand_companies_visited(),
        'grand_highest_package': PlacementBatch.grand_highest_package(),
        'grand_avg_package': PlacementBatch.grand_avg_package(),
        'grand_lowest_package': PlacementBatch.grand_lowest_package(),
        
        # नए यूनिक वेरिएबल्स (टेबल और ड्रॉपडाउन फ़िल्टर के लिए)
        'placed_students': placement_students,
        'filter_batches': filter_batches,
        'filter_branches': filter_branches,
        'selected_filter_batch': selected_filter_batch,
        'selected_filter_branch': selected_filter_branch,
    }
    return render(request,'Placements.html',context)

def student(request):
    return render(request,'studentcorner.html')

def about(request):
    principal = models.CustomUser.objects.filter(category='PRINCIPAL').first()
    
    context = {
        'principal':principal,
    }
     
    return render(request,'About.html',context)

def contact(request):
    return render(request,'Contact.html')


    
    
  # अपने सही मॉडल पाथ से इम्पोर्ट करें

def company_student_verification(request):
    student_data = None
    searched = False

    if request.method == "POST":
        student_email = request.POST.get('student_email', '').strip()
        roll_no = request.POST.get('roll_no', '').strip()
        searched = True

        # दोनों फ़ील्ड्स अनिवार्य हैं
        if not student_email or not roll_no:
            messages.error(request, "कृपया छात्र का ईमेल और रोल नंबर दोनों दर्ज करें।")
        else:
            try:
                # 1. पहले User मॉडल में STUDENT कैटेगरी और दिए गए ईमेल के आधार पर छात्र को ढूँढें
                # select_related का उपयोग करके engagement_details को एक साथ फ़ेच कर रहे हैं
                student_user = models.CustomUser.objects.select_related('engagement_details').get(
                    email__iexact=student_email,
                    category='STUDENT'
                )

                # 2. सुरक्षा जाँच: क्या इस यूजर के वन-टू-वन रिकॉर्ड का रोल नंबर फ़ॉर्म के रोल नंबर से मैच करता है?
                if (hasattr(student_user, 'engagement_details') and 
                    student_user.engagement_details and 
                    student_user.engagement_details.roll_no == roll_no):
                    
                    student_data = student_user
                    messages.success(request, "छात्र का रिकॉर्ड सफलतापूर्वक सत्यापित (Verified) हो गया है!")
                else:
                    messages.error(request, "दर्ज किया गया रोल नंबर इस ईमेल आईडी से मेल नहीं खाता है।")
                    return redirect('placements')
            except User.DoesNotExist:
                messages.error(request, "दिए गए विवरण (Email/Roll No) के अनुसार कोई छात्र रिकॉर्ड नहीं मिला।")
                return redirect('placements')
                

    context = {
        'student': student_data,
        'searched': searched
    }
    return render(request, 'company_verify.html', context)


from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny
from django.shortcuts import render
from .models import pyq
from .serializers import PYQSerializer
from .permissions import IsAdminOrReadOnly

class PYQViewSet(viewsets.ModelViewSet):
    queryset = pyq.objects.all().order_by("-id")
    serializer_class = PYQSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["paper_name", "paper_code", "year", "session"]
    ordering_fields = ["id", "year", "created_at"]


def pyq_page(request):
    # Public page — staff-only buttons JS me hide honge
    return render(request, "pyq/pyqs.html", {"is_staff": request.user.is_staff})

from rest_framework import viewsets, filters, parsers
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import render
 
from .models import CheatSheet, Category
from .serializers import CheatSheetSerializer, CategorySerializer
from .permissions import IsOwnerOrAdminOrReadOnly
from .pagination import StandardPagination


class CheatSheetViewSet(viewsets.ModelViewSet):
    serializer_class   = CheatSheetSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]
    pagination_class   = StandardPagination

    # 🆕 file upload + JSON dono accept
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "is_public", "owner"]
    search_fields    = ["title", "content", "category__name"]
    ordering_fields  = ["created_at", "updated_at", "title"]
    ordering         = ["-created_at"]

    def get_queryset(self):
        qs = CheatSheet.objects.select_related("owner", "category")
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return qs
        if user.is_authenticated:
            return qs.filter(Q(is_public=True) | Q(owner=user))   # ✅
        return qs.filter(is_public=True)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None


def cheatsheet_page(request):
    return render(request, "cheatsheets/list.html")