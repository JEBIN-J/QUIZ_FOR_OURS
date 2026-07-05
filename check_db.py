import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')
django.setup()
from quiz.models import Quiz
q = Quiz.objects.get(id=6)
print(f"Shuffle: {q.shuffle_questions}")
