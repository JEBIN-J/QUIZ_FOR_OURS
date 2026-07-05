from django.utils import timezone
from .models import UserRegister

class StudentAuthMiddleware:
    """
    Middleware to attach the logged-in student object to the request.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        student_id = request.session.get('student_id')
        request.student = None
        if student_id:
            try:
                request.student = UserRegister.objects.get(id=student_id)
            except UserRegister.DoesNotExist:
                pass
                
        response = self.get_response(request)
        return response

class ActiveUserMiddleware:
    """
    Middleware to track user activity.
    Updates the 'last_active' field for logged-in students.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        student_id = request.session.get('student_id')
        if student_id:
            try:
                UserRegister.objects.filter(id=student_id).update(last_active=timezone.now())
            except Exception:
                pass
                
        return response
