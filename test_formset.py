import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')
django.setup()

from quiz.forms import QuizConditionFormSet
from quiz.models import Quiz

quiz = Quiz.objects.get(id=6)

data = {
    'conditions-TOTAL_FORMS': '1',
    'conditions-INITIAL_FORMS': '0',
    'conditions-MIN_NUM_FORMS': '0',
    'conditions-MAX_NUM_FORMS': '1000',
    'conditions-0-text': 'Test condition',
}

formset = QuizConditionFormSet(data, instance=quiz)
if formset.is_valid():
    print("SAVING...")
    saved = formset.save()
    print("SAVED INSTANCES:", saved)
    print("DB COUNT:", quiz.conditions.count())
    # Clean up
    for s in saved:
        s.delete()
else:
    print("ERRORS:", formset.errors)
