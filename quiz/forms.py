from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory
from .models import Quiz, Question, Choice, Category, Subject, UserRegister, QuizSection, QuizCondition
from django.contrib.auth.hashers import make_password

class RegistrationForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Email Address")
    age = forms.IntegerField(required=False, min_value=1, widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Enter Age'}), label="Age")
    gender = forms.ChoiceField(required=False, choices=[('', 'Select Gender'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], widget=forms.Select(attrs={'class': 'form-input'}), label="Gender")
    place = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter City/Place'}), label="Place")
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Enter Password'}), label="Password")
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirm Password'}), label="Confirm Password")

    class Meta:
        model = UserRegister
        fields = ['username', 'email', 'age', 'gender', 'place']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['username', 'email']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['class'] = 'form-input'
                self.fields[field_name].widget.attrs['placeholder'] = f"Enter {self.fields[field_name].label}"

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserRegister.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user_reg = super().save(commit=False)
        user_reg.password = make_password(self.cleaned_data["password"])
        if commit:
            user_reg.save()
        return user_reg


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = [
            'title', 'description', 'category', 'subject', 'academic_year', 
            'unit', 'difficulty', 'duration', 'passing_score', 'negative_marking', 
            'negative_marks_per_question', 'shuffle_questions', 'shuffle_options', 
            'max_attempts', 'start_date', 'end_date', 'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter quiz title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description...'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2025-2026'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Unit 1'}),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Duration in minutes'}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100', 'placeholder': 'Passing percentage'}),
            'negative_marking': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'negative_marks_per_question': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'e.g. 0.25'}),
            'shuffle_questions': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'shuffle_options': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


QuizSectionFormSet = inlineformset_factory(
    Quiz, QuizSection, 
    fields=('title', 'description', 'time_limit', 'order'),
    extra=1, 
    can_delete=True,
    widgets={
        'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Section Title (e.g. Aptitude)'}),
        'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional description'}),
        'time_limit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Mins (Optional)'}),
        'order': forms.NumberInput(attrs={'class': 'form-control'}),
    }
)


class QuestionForm(forms.Form):
    section = forms.ModelChoiceField(
        queryset=QuizSection.objects.none(),
        required=False,
        empty_label="General (No Section)",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Assign to Section (Optional)"
    )
    text = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter the question text here...'}),
        label="Question Text"
    )
    question_type = forms.ChoiceField(
        choices=Question.QUESTION_TYPES,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_question_type'}),
        initial='MCQ',
        label="Question Type"
    )
    correct_answer_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'For Fill-in-Blank, Program Code, or Paragraph answers...'}),
        label="Correct Answer Text (Non-MCQ)"
    )
    difficulty = forms.ChoiceField(
        choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='Medium',
        label="Difficulty"
    )
    image_url = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Image path or URL if applicable'}),
        label="Image URL/Path"
    )
    points = forms.IntegerField(
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        label="Points"
    )
    negative_marks = forms.FloatField(
        initial=0.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.0'}),
        label="Negative Marks"
    )
    explanation = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Explanation for correct choice...'}),
        label="Explanation"
    )
    
    # Choice options for MCQ / MultipleAnswers
    choice1_text = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 1'}), label="Option 1")
    choice1_correct = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}))
    
    choice2_text = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 2'}), label="Option 2")
    choice2_correct = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}))
    
    choice3_text = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 3 (Optional)'}), label="Option 3")
    choice3_correct = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}))
    
    choice4_text = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 4 (Optional)'}), label="Option 4")
    choice4_correct = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}))

    def __init__(self, *args, **kwargs):
        quiz = kwargs.pop('quiz', None)
        super().__init__(*args, **kwargs)
        if quiz:
            self.fields['section'].queryset = QuizSection.objects.filter(quiz=quiz)

    def clean(self):
        cleaned_data = super().clean()
        q_type = cleaned_data.get('question_type')
        c1_correct = cleaned_data.get('choice1_correct')
        c2_correct = cleaned_data.get('choice2_correct')
        c3_correct = cleaned_data.get('choice3_correct')
        c4_correct = cleaned_data.get('choice4_correct')

        # Validate that MCQ/MultipleAnswers has at least one correct choice
        if q_type in ['MCQ', 'MultipleAnswers', 'TrueFalse', 'Image']:
            if not (c1_correct or c2_correct or c3_correct or c4_correct):
                raise forms.ValidationError("You must mark at least one option as the correct answer for option-based questions.")
        elif q_type in ['FillBlank', 'Programming', 'Paragraph']:
            if not cleaned_data.get('correct_answer_text'):
                raise forms.ValidationError("You must specify the correct answer text for this question type.")
        
        return cleaned_data


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Computer Science'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Category details...'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., fa-laptop-code'}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserRegister
        fields = ['photo_url', 'department', 'semester', 'achievements']
        widgets = {
            'photo_url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '/static/quiz/images/avatar.png'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Information Technology'}),
            'semester': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Semester 4'}),
            'achievements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List certifications or badges...'}),
        }

class QuizConditionForm(forms.ModelForm):
    class Meta:
        model = QuizCondition
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. No calculators allowed', 'style': 'flex-grow: 1;'}),
        }

QuizConditionFormSet = forms.inlineformset_factory(
    Quiz, 
    QuizCondition, 
    form=QuizConditionForm,
    extra=0,
    can_delete=True
)
