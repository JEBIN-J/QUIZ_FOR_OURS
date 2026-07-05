import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')
django.setup()
from quiz.models import Quiz
q = Quiz.objects.all()
try:
    print("Has index:", hasattr(q, 'index'))
    q.index(q[0])
    print("Index worked!")
except Exception as e:
    print("Error:", e)
