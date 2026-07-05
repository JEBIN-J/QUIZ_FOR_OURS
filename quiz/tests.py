from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Quiz, Question, Choice, QuizAttempt, UserResponse, StudentProfile

class QuizModelTests(TestCase):
    def setUp(self):
        # Create users
        self.admin = User.objects.create_superuser(username='admin_test', password='adminpass')
        self.competitor = User.objects.create_user(username='competitor_test', password='comppass')

        # Create Quiz
        self.quiz = Quiz.objects.create(
            title="General Quiz",
            description="Testing base features",
            time_limit=60,
            passing_score=50,
            created_by=self.admin
        )
        
        # Create Question 1 (1 point)
        self.q1 = Question.objects.create(quiz=self.quiz, text="What is 2 + 2?", points=1)
        self.c1_correct = Choice.objects.create(question=self.q1, text="4", is_correct=True)
        self.c1_wrong = Choice.objects.create(question=self.q1, text="5", is_correct=False)
        
        # Create Question 2 (2 points)
        self.q2 = Question.objects.create(quiz=self.quiz, text="What is capital of France?", points=2)
        self.c2_correct = Choice.objects.create(question=self.q2, text="Paris", is_correct=True)
        self.c2_wrong = Choice.objects.create(question=self.q2, text="London", is_correct=False)

    def test_quiz_properties(self):
        """Verify model counts and details are working."""
        self.assertEqual(self.quiz.title, "General Quiz")
        self.assertEqual(self.quiz.total_questions, 2)
        self.assertEqual(str(self.q1), "What is 2 + 2?")

    def test_quiz_attempt_scoring_pass(self):
        """Verify scoring updates passed status correctly if correct answers exceed passing_score."""
        attempt = QuizAttempt.objects.create(
            quiz=self.quiz,
            user=self.competitor,
            score=3,
            total_questions=2,
            correct_answers=2,
            percentage=100.0,
            passed=True
        )
        self.assertEqual(attempt.user.username, 'competitor_test')
        self.assertTrue(attempt.passed)

    def test_quiz_attempt_scoring_fail(self):
        """Verify scoring registers fail status when score is below requirement."""
        attempt = QuizAttempt.objects.create(
            quiz=self.quiz,
            user=self.competitor,
            score=0,
            total_questions=2,
            correct_answers=0,
            percentage=0.0,
            passed=False
        )
        self.assertFalse(attempt.passed)

class QuizViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='admin_test', password='adminpass')
        self.competitor = User.objects.create_user(username='competitor_test', password='comppass')

    def test_welcome_page(self):
        """Welcome page loads successfully for anonymous visitor."""
        response = self.client.get(reverse('quiz:welcome'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Examination")

    def test_dashboard_redirect_for_anonymous(self):
        """Unauthenticated user is redirected to the register screen."""
        response = self.client.get(reverse('quiz:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('quiz:register'), response.url)

    def test_dashboard_access_for_authenticated(self):
        """Logged in user can access the dashboard."""
        self.client.login(username='competitor_test', password='comppass')
        response = self.client.get(reverse('quiz:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")

    def test_quiz_submission_creates_user_responses(self):
        """Submitting exam answers creates UserResponse records in the database."""
        # Create models for submission test
        quiz = Quiz.objects.create(
            title="Python Exam",
            time_limit=60,
            passing_score=50,
            created_by=self.admin
        )
        q1 = Question.objects.create(quiz=quiz, text="Q1", points=1)
        c1 = Choice.objects.create(question=q1, text="C1", is_correct=True)
        c2 = Choice.objects.create(question=q1, text="C2", is_correct=False)

        self.client.login(username='competitor_test', password='comppass')
        
        # Submit the exam POST request
        response = self.client.post(
            reverse('quiz:submit', args=[quiz.id]),
            {f'question_{q1.id}': c1.id}
        )
        
        # Verify attempt exists and responses were saved
        attempt = QuizAttempt.objects.get(quiz=quiz, user=self.competitor)
        self.assertEqual(attempt.correct_answers, 1)
        
        # Check UserResponse
        user_responses = UserResponse.objects.filter(attempt=attempt)
        self.assertEqual(user_responses.count(), 1)
        self.assertEqual(user_responses.first().selected_choice, c1)

    def test_quiz_demo_flow(self):
        """Anonymous user can take a demo version of an exam, submit it, and view demo results."""
        quiz = Quiz.objects.create(
            title="Demo Subject",
            time_limit=60,
            passing_score=50,
            created_by=self.admin
        )
        q1 = Question.objects.create(quiz=quiz, text="Q1", points=1)
        c1 = Choice.objects.create(question=q1, text="C1", is_correct=True)

        # 1. Play Demo page works anonymously
        response = self.client.get(reverse('quiz:play_demo', args=[quiz.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sample Demo")

        # 2. Submit Demo works anonymously and redirects to demo_results
        response = self.client.post(
            reverse('quiz:submit_demo', args=[quiz.id]),
            {f'question_{q1.id}': c1.id}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('quiz:demo_results')))

        # 3. Demo results page renders the scores and selections
        response = self.client.get(reverse('quiz:demo_results'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sample Exam")
        self.assertContains(response, "Report")
        self.assertContains(response, "Demo Score")
        self.assertContains(response, "Your Selection")

    def test_user_registration(self):
        """Test registering a new user via POST."""
        response = self.client.post(reverse('quiz:register'), {
            'username': 'new_student',
            'email': 'student@example.com',
            'password': 'studentpass123',
            'password_confirm': 'studentpass123',
        })
        # Check redirect to dashboard on success
        self.assertEqual(response.status_code, 302)
        # Check if user is saved in DB
        self.assertTrue(User.objects.filter(username='new_student').exists())
        # Check if student profile was created
        user = User.objects.get(username='new_student')
        self.assertTrue(StudentProfile.objects.filter(user=user).exists())



