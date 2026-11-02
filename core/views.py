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

from rest_framework import viewsets, filters, parsers
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import render
 
from .models import CheatSheet, Category
from .serializers import CheatSheetSerializer, CategorySerializer
from .permissions import IsOwnerOrAdminOrReadOnly
from .pagination import StandardPagination

import json
from urllib.parse import quote
from django.http import JsonResponse
 
 
from django.views.decorators.http import require_GET
# from django.contrib.auth.decorators import login_required  # enable if needed

from .models import StudentEngagement

def verification(request):
    return render(request,'googled61072f71b08753c.html') 


def _get_slides(page):
    DEFAULT_DATA = {
    'academic': [
        {
            'badge': 'Academic Excellence',
            'title': 'Learn From The Best Minds',
            'subtitle': 'UGC-approved courses, experienced faculty aur modern curriculum — sab ek jagah.',
            'bg_class': 'slide-bg-1',
            'button1_text': 'View Courses', 'button1_url': '#',
            'button2_text': 'Download Syllabus', 'button2_url': '#',
            'button3_text': 'Talk to Advisor', 'button3_url': '#',
        },
        {
            'badge': 'Research & Innovation',
            'title': 'Where Curiosity Meets Discovery',
            'subtitle': 'Live projects, funded research aur industry collaborations ke saath seekho.',
            'bg_class': 'slide-bg-3',
            'button1_text': 'Explore Labs', 'button1_url': '#',
            'button2_text': 'Faculty', 'button2_url': '#',
            'button3_text': 'Apply Now', 'button3_url': '#',
        },
    ],
    'admission': [
        {
            'badge': 'Admissions Open 2026',
            'title': 'Your Future Starts Here',
            'subtitle': 'Simple 4-step process, merit-based scholarships aur easy EMI options.',
            'bg_class': 'slide-bg-2',
            'button1_text': 'Apply Online', 'button1_url': '#',
            'button2_text': 'Eligibility', 'button2_url': '#',
            'button3_text': 'Fees Structure', 'button3_url': '#',
        },
    ],
    'campus_life': [
        {
            'badge': 'Life @ Campus',
            'title': 'More Than Just Classes',
            'subtitle': 'Clubs, sports, cultural fests aur lifelong friendships — campus ek community hai.',
            'bg_class': 'slide-bg-4',
            'button1_text': 'Clubs & Societies', 'button1_url': '#',
            'button2_text': 'Hostel', 'button2_url': '#',
            'button3_text': 'Gallery', 'button3_url': '#',
        },
    ],
    'student_corner': [
        {
            'badge': 'Student Hub',
            'title': 'Everything Students Need',
            'subtitle': 'Timetable, results, notices, scholarships aur support — all in one place.',
            'bg_class': 'slide-bg-5',
            'button1_text': 'Results', 'button1_url': '#',
            'button2_text': 'Notices', 'button2_url': '#',
            'button3_text': 'Scholarships', 'button3_url': '#',
        },
    ],
    'placements': [
        {
            'badge': '95% Placement Record',
            'title': 'Ready For The Real World',
            'subtitle': 'Top recruiters, mock interviews aur dedicated career cell — placement guaranteed.',
            'bg_class': 'slide-bg-3',
            'button1_text': 'Our Recruiters', 'button1_url': '#',
            'button2_text': 'Placement Stats', 'button2_url': '#',
            'button3_text': 'Career Cell', 'button3_url': '#',
        },
    ],
}

    qs = models.HeroSlide.objects.filter(page=page).order_by('order', 'id')
    return list(qs) if qs.exists() else DEFAULT_DATA.get(page, [])
 
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
    principal = models.messages.objects.select_related('message_user').first()
    department_model = models.Course_Department.objects.prefetch_related(
        Prefetch(
            'users',
            queryset=models.CustomUser.objects.filter(category='HOD'),
            to_attr='hod_users',
        ),
        Prefetch(
            'users',
            queryset=models.CustomUser.objects.filter(
                category__in=['TEACHING', 'STAFFS']
            ).order_by('first_name'),
            to_attr='faculty_users',
        ),
    )
     
    context = {
        'principals':principal,
        'impnotices': impnotices, 
        'departments': department_model,
        
    }
    
    return render(request,'index.html',context)

from django.db.models import Prefetch
def academic(request):
    all_timetables = models.Timetable.objects.filter(types='CLASS').select_related('uploaded_by')
    department_model = models.Course_Department.objects.prefetch_related(
        Prefetch(
            'users',
            queryset=models.CustomUser.objects.filter(category='HOD'),
            to_attr='hod_users',
        ),
        Prefetch(
            'users',
            queryset=models.CustomUser.objects.filter(
                category__in=['TEACHING', 'STAFFS']
            ).order_by('first_name'),
            to_attr='faculty_users',
        ),
    )
    info = models.info.objects.filter(page='academics').first()
    academic_calendar = models.academic_calendar.objects.all().order_by('-created_at') 
    syllabuses = models.syllabus.objects.all()
   
    
    Context = {'infomsg': info, 
               'departments': department_model, 
               'academic_calendar': academic_calendar,
               'all_timetables': all_timetables,
                  'slides': _get_slides('academic') ,
               }
     

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
    
    Context = {'infomsg': info,
               'feecategories': fee_categories,
               'scholarships': active_scholarships,
               'departments': department_model,
               'admission_desk': admission_desk ,
               'Imp_date': Imp_date,
               'Imp_doc': Imp_doc ,
               'CLCS':Admission_CLC ,
               'DTES':Admission_DTE, 
                'slides': _get_slides('admission') ,
               }
    return render(request,'Admissions.html',Context)



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
   
   
    campusdictionary = {'infomsg':info,
                        'categories':categories ,
                        'rulses': hostelrules,
                        'hostelupdates':hostelupdate,
                        'libraryupdates':libraryupdate ,
                        'libraryrulses':libraryrulse,
                        'labupdates':labupdate ,
                        'labrulses':labrulse,
                        'slides': _get_slides('campus_life') ,
                        }
    return render(request,'CampusLife.html',campusdictionary)

def placements(request):
    all_batches = models.PlacementBatch.objects.prefetch_related('branch_records').order_by('-year')
    placement_officer = models.Responsibility.objects.select_related().filter(work_name='PLACEMENT').first()
    
  
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
        
        'slides': _get_slides('placements'),
         
        
        'tpo':placement_officer,
    }
    return render(request,'Placements.html',context)

def student(request):
    return render(request,'studentcorner.html')

def about(request):
    principal = models.messages.objects.select_related('message_user').first()
    
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
            except CustomUser.DoesNotExist:
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


def contact_us(request):
 
    users_with_duties = models.CustomUser.objects.filter(duties__isnull=False).distinct()
    
    context = {
        'users': users_with_duties
    }
    return render(request, 'contact/contact_us.html', context)




 
def mask_roll_no(roll_no):
    """
    Roll No masking:
      - First 2 chars visible
      - Last 3 chars visible
      - Middle replaced with 'x'
      Example: '21CS1001' -> '21xxx001'
    """
    if roll_no is None:
        return ""
    s = str(roll_no).strip()
    if len(s) <= 5:
        return s
    middle_len = len(s) - 5
    return f"{s[:2]}{'x' * middle_len}{s[-3:]}"


def get_avatar_url(user):
    """User photo URL if exists, else generated initials avatar."""
    if user:
        try:
            if user.photo and user.photo.url:
                return user.photo.url
        except (ValueError, AttributeError):
            pass
    try:
        name = (user.get_full_name() or user.username or "U") if user else "U"
    except Exception:
        name = "U"
    return f"https://ui-avatars.com/api/?name={quote(name)}&background=0D6EFD&color=fff&size=64"


# ============================================================
# PAGE VIEW
# ============================================================

def student_engagement_page(request):
    """Renders the Bootstrap table page."""
    return render(request, "student/student_engagement.html")


# ============================================================
# JSON API
# ============================================================

@require_GET
# @login_required
def student_engagement_json(request):
    """
    Returns JSON with dynamic search.

    Query params:
        ?all=1             -> return ALL records (for client-side DataTables)
        ?search=<text>     -> optional backend search
        ?page=<int>        -> default 1
        ?per_page=<int>    -> default 10 (used only when all != 1)
    """
    try:
        search    = (request.GET.get("search") or "").strip()
        fetch_all = request.GET.get("all") in ("1", "true", "yes")

        try:
            page = max(1, int(request.GET.get("page", 1)))
        except (TypeError, ValueError):
            page = 1
        try:
            per_page = int(request.GET.get("per_page", 10))
        except (TypeError, ValueError):
            per_page = 10
        per_page = max(1, min(per_page, 100))

        qs = (
            StudentEngagement.objects
            .select_related("user", "user__deprtment")
            .all()
        )

        if search:
            qs = qs.filter(
                Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(user__username__icontains=search)
                | Q(roll_no__icontains=search)
                | Q(branch_of_student__icontains=search)
                | Q(passout_year__icontains=search)
                | Q(company_name__icontains=search)
                | Q(higher_studies_institute__icontains=search)
                | Q(nature_of_work__icontains=search)
                | Q(entrance_exam_details__icontains=search)
            )

        total = qs.count()
        ordered = qs.order_by("user__first_name", "user__last_name", "roll_no")

        if fetch_all:
            page_qs = ordered
            page = 1
            per_page = total or 0
            total_pages = 1 if total else 0
        else:
            total_pages = (total + per_page - 1) // per_page if total else 0
            start = (page - 1) * per_page
            page_qs = ordered[start:start + per_page]

        results = []
        for eng in page_qs:
            user = eng.user

            if user:
                full_name = (user.get_full_name() or "").strip() or user.username or "Unnamed"
                try:
                    department = str(user.deprtment) if user.deprtment_id else ""
                except Exception:
                    department = ""
                category = user.get_category_display() if hasattr(user, "get_category_display") else ""
            else:
                full_name, department, category = "Unnamed", "", ""

            results.append({
                "id": eng.id,
                "user_id": user.id if user else None,

                "name": full_name,
                "avatar": get_avatar_url(user),
                "roll_no": mask_roll_no(eng.roll_no),
                "branch": eng.branch_of_student or "",
                "department": department,
                "passout_year": eng.passout_year or "",
                "category": category,

                "got_placement": bool(eng.got_placement),
                "company_name": eng.company_name or "",
                "package_lpa": str(eng.package_lpa) if eng.package_lpa is not None else "",
                "offer_letter_details": eng.offer_letter_details or "",

                "opted_for_higher_studies": bool(eng.opted_for_higher_studies),
                "higher_studies_institute": eng.higher_studies_institute or "",
                "entrance_exam_details": eng.entrance_exam_details or "",

                "opted_for_entrepreneurship": bool(eng.opted_for_entrepreneurship),
                "nature_of_work": eng.nature_of_work or "",
                "annual_turnover_lpa": str(eng.annual_turnover_lpa) if eng.annual_turnover_lpa is not None else "",

                "preparing_for_competitive_exams": bool(eng.preparing_for_competitive_exams),
                "not_engaged_till_now": bool(eng.not_engaged_till_now),
            })

        return JsonResponse({
            "success": True,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "data": results,
        })

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"{type(e).__name__}: {e}", "data": []},
            status=500,
        )