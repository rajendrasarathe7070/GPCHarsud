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
        return redirect(home)
    return redirect(home)

def home(request):
    
    return render(request,"index.html")

def index(request):
    # impnotices = models.Notice.objects.all().order_by('-created_at')
     
    impnotices = models.Notice.objects.select_related('created_by').all().order_by('-created_at')

    department_model = models.Course_Department.objects.all()
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
    
    
    
    selected_batch_id = request.GET.get('batch_id')
    
     
    selected_batch = None
    if all_batches.exists():
        if selected_batch_id:
            
            selected_batch = next((b for b in all_batches if str(b.id) == str(selected_batch_id)), all_batches.first())
        else:
            selected_batch = all_batches.first()
            
            
    context = {
        'all_batches': all_batches,       
        'selected_batch': selected_batch, 
          
          'grand_students_placed': PlacementBatch.grand_students_placed(),
        'grand_companies_visited': PlacementBatch.grand_companies_visited(),
        'grand_highest_package': PlacementBatch.grand_highest_package(),
        'grand_avg_package': PlacementBatch.grand_avg_package(),
        'grand_lowest_package':PlacementBatch.grand_lowest_package(),
          
    }
    return render(request,'Placements.html',context)

def student(request):
    return render(request,'studentcorner.html')

def aboutu(request):
    return render(request,'about.html')

def contact(request):
    return render(request,'Contact.html')


    
    
