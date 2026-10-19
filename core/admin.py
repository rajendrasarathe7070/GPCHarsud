from django.contrib import admin
from . import models
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Responsibility
from django.contrib import admin
 
 
from two_factor.admin import AdminSiteOTPRequired
from .models import FeeCategory, FeeStructure, Scholarship , Pro_DTE_CLC_Admission , CampusCategory , CampusImage , PlacementBatch , BranchPlacement , StudentEngagement
from django.contrib import admin



class DepartmentListFilter(admin.SimpleListFilter):
    title = 'Department' # एडमिन पैनल में दिखने वाला नाम
    parameter_name = 'department'

    def lookups(self, request, model_admin):
        # यहाँ अपने डिपार्टमेंट के कोड और नाम लिखें
        return (
            ('cs', 'CS'),
            ('civil', 'Civil'),
            ('et', 'ET'),
            ('me', 'ME'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user__department=self.value())
        return queryset


@admin.register(StudentEngagement)
class StudentEngagementAdmin(admin.ModelAdmin):
    list_display = (
        'get_student_name', 
        'roll_no', 
        
        'passout_year', 
        'got_placement', 
        'opted_for_higher_studies', 
        'opted_for_entrepreneurship',
        'not_engaged_till_now'
    )

    # 2. 'user__department' को हटाकर यहाँ 'DepartmentListFilter' को रख दें
    list_filter = (
        DepartmentListFilter,  # कस्टम फ़िल्टर यहाँ लगाया
        'passout_year', 
        'got_placement', 
        'opted_for_higher_studies', 
        'opted_for_entrepreneurship',
        'not_engaged_till_now'
    )

    search_fields = (
        'user__username', 
        'user__first_name', 
        'user__email', 
        'roll_no', 
        'company_name'
    )

    fieldsets = (
        ('Student Reference', {'fields': ('user', 'roll_no', 'passout_year')}),
        ('Placement Details', {
            'fields': ('got_placement', 'company_name', 'package_lpa', 'offer_letter_details'),
            'classes': ('collapse',),
        }),
        ('Higher Studies Details', {
            'fields': ('opted_for_higher_studies', 'higher_studies_institute', 'entrance_exam_details'),
            'classes': ('collapse',),
        }),
        ('Entrepreneurship / Self Employment', {
            'fields': ('opted_for_entrepreneurship', 'nature_of_work', 'annual_turnover_lpa'),
            'classes': ('collapse',),
        }),
        ('Others', {'fields': ('preparing_for_competitive_exams', 'not_engaged_till_now')}),
    )

    @admin.display(ordering='user__first_name', description='Student Name')
    def get_student_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username

    @admin.display(ordering='user__department', description='Department')
    def get_department(self, obj):
        return obj.passout_year
    
    
    

class BranchPlacementInline(admin.TabularInline):
    model = BranchPlacement
    extra = 1
    # यदि आप चाहते हैं कि फ़ील्ड्स एडमिन में एक लाइन में टेबल की तरह दिखें
    fields = (
        's_no', 'branch_name', 'final_year_students', 
        'students_placed', 'companies_visited', 
        'highest_package', 'lowest_package', 'average_package'
    )

@admin.register(PlacementBatch)
class PlacementBatchAdmin(admin.ModelAdmin):
    list_display = ('year', 'created_at')
    inlines = [BranchPlacementInline]

class CampusImageInline(admin.TabularInline):
    model = CampusImage
    extra = 1   

@admin.register(CampusCategory)
class CampusCategoryAdmin(admin.ModelAdmin):
    inlines = [CampusImageInline]
 

@admin.register(Pro_DTE_CLC_Admission)
class ProDTECLCAdmissionAdmin(admin.ModelAdmin):
    # 'catogry' को सबसे पहले रखा है ताकि लिस्ट में पहचानना आसान हो
    list_display = ('catogry', 'id', 'title', 'short_dis')
    
    # इसके जरिए डेटा पहले कैटेगरी (DTE फिर CLC) के हिसाब से और फिर ID के हिसाब से ग्रुप होकर दिखेगा
    ordering = ('catogry', 'id')
    
    # साइड में क्विक फिल्टर भी रहेगा
    list_filter = ('catogry',)
    
    search_fields = ('title', 'dis')

    def short_dis(self, obj):
        if obj.dis:
            return obj.dis[:50] + '...' if len(obj.dis) > 50 else obj.dis
        return "-"
    short_dis.short_description = 'विवरण (Description)'
 
class FeeStructureInline(admin.TabularInline):
    model = FeeStructure
    extra = 1

@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    inlines = [FeeStructureInline]

@admin.register(Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')
    list_filter = ('is_active',)

class OTPAdminSite(AdminSiteOTPRequired, admin.AdminSite):
    pass

admin.site.__class__ = OTPAdminSite
 
 

# Hum default UserAdmin ko extend kar rahe hain taaki humari extra fields admin panel me dikhein
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Admin list view me dikhne wali fields
    list_display = ['username', 'email', 'first_name', 'last_name', 'category', 'phone', 'is_staff']
    
    # User edit page par humari extra fields ko jodne ke liye
    fieldsets = UserAdmin.fieldsets + (
        ('College Staff Info', {'fields': ('photo',  'phone', 'study', 'slug', 'deprtment' ,'category','experience','joining_date')}),
    )
    # User create page par extra fields dikhane ke liye
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('User Info', {'fields': ('photo', 'phone','study' ,'slug','deprtment','category','experience','joining_date')}),
    )
    


class TimetableAdmin(admin.ModelAdmin):
   
    list_display = ('branch', 'year', 'uploaded_by', 'uploaded_at')

    readonly_fields = ('uploaded_by',)

   
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # अगर नया टाइम टेबल क्रिएट हो रहा है
            obj.uploaded_by = request.user
        else:    
            obj.uploaded_by = request.user
            
        super().save_model(request, obj, form, change)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Responsibility)
admin.site.register(models.Course_Department)
admin.site.register(models.Timetable, TimetableAdmin)

admin.site.register(models.Notice)
admin.site.register(models.info)
admin.site.register(models.academic_calendar)
admin.site.register(models.Imp_date_and_document)
# admin.site.register(models.Pro_DTE_CLC_Admission)
 
admin.site.register(models.RulseUpdate_Campus)


admin.site.register(models.syllabus)
 

