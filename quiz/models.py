from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, default='fa-graduation-cap', help_text="FontAwesome icon class name")

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subjects')

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class Quiz(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text="Short description of the quiz")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='quizzes')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name='quizzes')
    academic_year = models.CharField(max_length=50, default="2025-2026", blank=True, null=True)
    unit = models.CharField(max_length=50, default="Unit 1", blank=True, null=True)
    difficulty = models.CharField(max_length=50, choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')], default='Medium')
    duration = models.PositiveIntegerField(default=60, help_text="Time limit in minutes")
    passing_score = models.PositiveIntegerField(default=60, help_text="Passing score percentage (0-100)")
    negative_marking = models.BooleanField(default=False, help_text="Enable negative marking for this quiz")
    negative_marks_per_question = models.FloatField(default=0.0, help_text="Marks deducted for each incorrect answer")
    shuffle_questions = models.BooleanField(default=False, help_text="Shuffle questions order for each attempt")
    shuffle_options = models.BooleanField(default=False, help_text="Shuffle choices/options for each question")
    max_attempts = models.PositiveIntegerField(default=1, help_text="Maximum allowed attempts per student")
    start_date = models.DateTimeField(null=True, blank=True, help_text="Quiz availability start date")
    end_date = models.DateTimeField(null=True, blank=True, help_text="Quiz availability end date/deadline")
    deadline = models.DateTimeField(null=True, blank=True, help_text="Backwards compatible deadline datetime")
    status = models.CharField(max_length=50, choices=[('Draft', 'Draft'), ('Published', 'Published'), ('Archived', 'Archived')], default='Draft')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quizzes_created', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Quizzes"
        ordering = ['-created_at']



    def __str__(self):
        return self.title

    @property
    def total_questions(self):
        return self.questions.count()

    @property
    def time_limit(self):
        # returns time limit in seconds (backwards compatibility for playroom script)
        return self.duration * 60

    @time_limit.setter
    def time_limit(self, value):
        self.duration = value // 60 if value else 60


class QuizSection(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    time_limit = models.PositiveIntegerField(blank=True, null=True, help_text="Time limit in minutes for this specific section")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.title} (Quiz: {self.quiz.title})"


class QuizCondition(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='conditions')
    text = models.CharField(max_length=500, help_text="A specific rule or condition for this quiz")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Condition for {self.quiz.title}"


class Question(models.Model):
    QUESTION_TYPES = [
        ('MCQ', 'Multiple Choice Single Answer'),
        ('MultipleAnswers', 'Multiple Choice Multiple Answers'),
        ('TrueFalse', 'True/False'),
        ('FillBlank', 'Fill in the Blank'),
        ('Image', 'Image Question'),
        ('Programming', 'Code/Programming Question'),
        ('Paragraph', 'Paragraph/Short Answer Question')
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    section = models.ForeignKey(QuizSection, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions')
    text = models.TextField(help_text="The question text")
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES, default='MCQ')
    correct_answer_text = models.TextField(blank=True, null=True, help_text="For Fill-in-Blank, Code, and Paragraph questions")
    difficulty = models.CharField(max_length=50, choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')], default='Medium')
    image_url = models.CharField(max_length=255, blank=True, null=True, help_text="URL or path to question image")
    points = models.PositiveIntegerField(default=1, help_text="Points awarded for a correct answer")
    negative_marks = models.FloatField(default=0.0, help_text="Points deducted for a wrong answer")
    explanation = models.TextField(blank=True, null=True, help_text="Explanation justifying the correct answer")

    def __str__(self):
        return self.text


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=255, help_text="The choice text")
    is_correct = models.BooleanField(default=False, help_text="Check if this is the correct answer")

    def __str__(self):
        return f"{self.text} (Correct: {self.is_correct})"


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey('UserRegister', on_delete=models.CASCADE, related_name='quiz_attempts')
    score = models.IntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    passed = models.BooleanField(default=False)
    time_taken = models.PositiveIntegerField(default=0, help_text="Time taken in seconds")
    grade = models.CharField(max_length=5, default='F')
    status = models.CharField(max_length=50, choices=[('InProgress', 'InProgress'), ('Completed', 'Completed')], default='Completed')
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.percentage}%"


class UserResponse(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)
    selected_choices = models.ManyToManyField(Choice, blank=True, related_name='multiple_responses')
    submitted_text = models.TextField(blank=True, null=True, help_text="For FillBlank, Code, and Paragraph questions")
    is_marked_for_review = models.BooleanField(default=False)

    class Meta:
        ordering = ['question__id']

    def __str__(self):
        if self.question.question_type in ['MCQ', 'TrueFalse', 'Image']:
            return f"{self.attempt.user.username} - Q: {self.question.id} - Choice: {self.selected_choice.text if self.selected_choice else 'None'}"
        return f"{self.attempt.user.username} - Q: {self.question.id} - Text: {self.submitted_text[:30] if self.submitted_text else 'None'}"





class Leaderboard(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='rankings')
    user = models.ForeignKey('UserRegister', on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    time_taken = models.PositiveIntegerField(default=0, help_text="Time taken in seconds")
    accuracy = models.FloatField(default=0.0)
    rank = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['rank', 'time_taken']

    def __str__(self):
        return f"Rank {self.rank}: {self.user.username} on {self.quiz.title}"


class Certificate(models.Model):
    user = models.ForeignKey('UserRegister', on_delete=models.CASCADE, related_name='certificates')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE)
    certificate_code = models.CharField(max_length=100, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Certificate {self.certificate_code} - {self.user.username}"


class Notification(models.Model):
    user = models.ForeignKey('UserRegister', on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, default='Info') # Info, Published, Alert
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title} (Read: {self.is_read})"


class UserRegister(models.Model):
    username = models.CharField(max_length=150)
    email = models.EmailField()
    mobile = models.CharField(max_length=15, unique=True, null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], null=True, blank=True)
    place = models.CharField(max_length=255, null=True, blank=True)
    password = models.CharField(max_length=255, help_text="Stored password hash at time of registration")
    
    # Merged from StudentProfile
    photo_url = models.CharField(max_length=255, blank=True, null=True, default='/static/quiz/images/default-avatar.png')
    target_exam = models.CharField(max_length=255, blank=True, null=True, default='UPSC', help_text="e.g. UPSC, SSC, Banking")
    education_qualification = models.CharField(max_length=50, blank=True, null=True, default='Graduate', help_text="e.g. Graduate, Post Graduate")
    preparation_stage = models.TextField(blank=True, help_text="e.g. Beginner, 1 Year, etc.")
    registered_at = models.DateTimeField(auto_now_add=True)
    
    # Session tracking
    last_active = models.DateTimeField(null=True, blank=True, help_text="Timestamp of the user's last request")
    current_session_start = models.DateTimeField(null=True, blank=True, help_text="Timestamp when the current session started")

    def __str__(self):
        return self.username

class OTPVerification(models.Model):
    mobile_or_email = models.CharField(max_length=255)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.mobile_or_email} - {self.otp}"

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon_class = models.CharField(max_length=100, default='bi-star-fill', help_text="Bootstrap icon class")
    is_popular = models.BooleanField(default=False, help_text="Highlight this plan as most popular")
    
    price = models.PositiveIntegerField(default=0, help_text="Price in INR")
    duration_days = models.PositiveIntegerField(default=30, help_text="Duration in days (0 for lifetime)")
    
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.name

class SubscriptionFeature(models.Model):
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='features')
    text = models.CharField(max_length=500)
    is_included = models.BooleanField(default=True, help_text="If unchecked, shows as a disabled feature with an X")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.text} ({'Included' if self.is_included else 'Excluded'})"

class UserSubscription(models.Model):
    user = models.ForeignKey('UserRegister', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='subscribers')
    
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True, help_text="Null means lifetime access")
    
    is_active = models.BooleanField(default=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True, help_text="Mock transaction ID")
    amount_paid = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-start_date']

    @property
    def status(self):
        if not self.is_active:
            return 'Cancelled'
        now = timezone.now()
        if self.start_date > now:
            return 'Pending'
        if self.end_date and self.end_date < now:
            return 'Expired'
        return 'Active'

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"
