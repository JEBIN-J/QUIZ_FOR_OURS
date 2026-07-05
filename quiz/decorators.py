from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import UserRegister

def student_required(view_func):
    """
    Decorator for views that checks that the user is logged in as a student
    using the UserRegister custom session logic.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        student_id = request.session.get('student_id')
        if student_id:
            try:
                request.student = UserRegister.objects.get(id=student_id)
                return view_func(request, *args, **kwargs)
            except UserRegister.DoesNotExist:
                # Session is stale/invalid
                del request.session['student_id']
                
        messages.warning(request, "Please log in to access this page.")
        return redirect('quiz:login')
        
    return _wrapped_view
