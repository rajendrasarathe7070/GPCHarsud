import random
from locust import HttpUser, task, between

# सभी #id हटाने के बाद बचे हुए यूनिक पेजों के रास्ते (Paths)
UNIQUE_PATHS = [
    "/",
    "/About",
    "/academic",
    "/admission",
    "/campus.html",
    "/events/",
    "/dashboard/login/",
    "/cheatsheets/",
    "/pyqs/",
    "/placements",
    "/student_engagement_page/",
    "/company_student_verification",
    "/contact_us",
]

class CollegeWebsiteUser(HttpUser):
    # हर रिक्वेस्ट के बीच 1 से 3 सेकंड का अंतर रहेगा
    wait_time = between(1, 3)

    @task
    def visit_random_page(self):
        # लिस्ट में से कोई भी एक पेज रैंडम तरीके से चुनेगा
        path = random.choice(UNIQUE_PATHS)
        self.client.get(path)
