import csv
import json
import io
import uuid
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.db import models
from django.db.models import Count, Avg, Max, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator

from django.contrib.auth.hashers import check_password
from .models import Category, Subject, Quiz, Question, Choice, QuizAttempt, UserResponse, Leaderboard, Certificate, Notification, UserRegister, SubscriptionPlan, SubscriptionFeature, UserSubscription
from .forms import RegistrationForm, QuizForm, QuestionForm, CategoryForm, UserProfileForm, SubscriptionPlanForm, SubscriptionFeatureFormSet
from .decorators import student_required

# Helpers
def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# Icon choices for the category form icon picker
ICON_CHOICES = [
    ('fa-graduation-cap', 'Study'),
    ('fa-flask', 'Science'),
    ('fa-calculator', 'Math'),
    ('fa-book', 'Books'),
    ('fa-globe', 'Geography'),
    ('fa-atom', 'Physics'),
    ('fa-code', 'Coding'),
    ('fa-brain', 'IQ'),
    ('fa-landmark', 'History'),
    ('fa-music', 'Music'),
    ('fa-palette', 'Art'),
    ('fa-person-running', 'Sports'),
    ('fa-heart-pulse', 'Health'),
    ('fa-laptop', 'Tech'),
    ('fa-star', 'General'),
    ('fa-trophy', 'Contest'),
    ('fa-lightbulb', 'Ideas'),
    ('fa-puzzle-piece', 'Logic'),
    ('fa-shield-halved', 'Security'),
    ('fa-rocket', 'Space'),
]


# --- Public / User Authentication Views ---

def welcome(request):
    quizzes = Quiz.objects.filter(status='Published').annotate(num_questions=Count('questions'))
    stats = {
        'total_quizzes': quizzes.count(),
        'total_users': UserRegister.objects.count(),
        'total_attempts': QuizAttempt.objects.count(),
    }
    return render(request, 'quiz/welcome.html', {'stats': stats, 'quizzes': quizzes})


import random
from .models import OTPVerification

def register_view(request):
    if request.session.get('student_id'):
        return redirect('quiz:dashboard')
        
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Generate OTP
            otp = str(random.randint(100000, 999999))
            mobile = form.cleaned_data.get('mobile')
            email = form.cleaned_data.get('email')
            
            # Print to console for dev testing
            print(f"========== OTP FOR {mobile}: {otp} ==========")
            
            # Send Email
            from django.core.mail import send_mail
            if email:
                send_mail(
                    'Your OTP for FJ Edu Online Exam',
                    f'Your OTP for registration is: {otp}',
                    'jebin6884@gmail.com',
                    [email],
                    fail_silently=True,
                )
            
            # Store in DB
            OTPVerification.objects.create(mobile_or_email=mobile, otp=otp)
            
            # Save form data in session
            registration_data = form.cleaned_data.copy()
            if registration_data.get('target_exam'):
                # Convert Category object to its name string for JSON serialization
                registration_data['target_exam'] = getattr(registration_data['target_exam'], 'name', str(registration_data['target_exam']))
            request.session['registration_data'] = registration_data
            
            messages.info(request, f"An OTP has been sent to {mobile}. Please enter it below.")
            return redirect('quiz:verify_otp')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")
    else:
        form = RegistrationForm()
    next_url = request.GET.get('next', '')
    return render(request, 'quiz/register.html', {'form': form, 'next_url': next_url})

def verify_otp_view(request):
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        registration_data = request.session.get('registration_data')
        
        if not registration_data:
            messages.error(request, "Session expired. Please register again.")
            return redirect('quiz:register')
            
        mobile = registration_data.get('mobile')
        
        # Verify OTP
        otp_record = OTPVerification.objects.filter(mobile_or_email=mobile, otp=otp_entered, is_verified=False).last()
        if otp_record:
            otp_record.is_verified = True
            otp_record.save()
            
            # Create user
            from django.contrib.auth.hashers import make_password
            user_reg = UserRegister.objects.create(
                username=registration_data['username'],
                email=registration_data['email'],
                mobile=registration_data['mobile'],
                target_exam=registration_data.get('target_exam', ''),
                age=registration_data.get('age'),
                gender=registration_data.get('gender'),
                place=registration_data.get('place'),
                password=make_password(registration_data['password'])
            )
            user_reg.current_session_start = timezone.now()
            user_reg.save()
            request.session['student_id'] = user_reg.id
            
            # Clear session data
            del request.session['registration_data']
            
            messages.success(request, f"Welcome, {user_reg.username}! Registration successful.")
            return redirect('quiz:dashboard')
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            
    return render(request, 'quiz/otp_verification.html')

def forgot_password_view(request):
    if request.method == 'POST':
        mobile_or_email = request.POST.get('mobile_or_email')
        
        user = UserRegister.objects.filter(models.Q(mobile=mobile_or_email) | models.Q(email=mobile_or_email)).first()
        if user:
            otp = str(random.randint(100000, 999999))
            print(f"========== OTP FOR FORGOT PASSWORD {mobile_or_email}: {otp} ==========")
            
            # Send Email
            from django.core.mail import send_mail
            recipient = mobile_or_email if '@' in mobile_or_email else user.email
            if recipient:
                send_mail(
                    'Password Reset OTP for FJ Edu Online Exam',
                    f'Your OTP for password reset is: {otp}',
                    'jebin6884@gmail.com',
                    [recipient],
                    fail_silently=True,
                )
            
            OTPVerification.objects.create(mobile_or_email=mobile_or_email, otp=otp)
            request.session['reset_identity'] = mobile_or_email
            messages.info(request, "OTP sent successfully to your registered mobile/email.")
            return redirect('quiz:reset_password')
        else:
            messages.error(request, "No account found with that mobile number or email.")
            
    return render(request, 'quiz/forgot_password.html')

def reset_password_view(request):
    identity = request.session.get('reset_identity')
    if not identity:
        messages.error(request, "Session expired. Please try again.")
        return redirect('quiz:forgot_password')
        
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
        else:
            otp_record = OTPVerification.objects.filter(mobile_or_email=identity, otp=otp_entered, is_verified=False).last()
            if otp_record:
                otp_record.is_verified = True
                otp_record.save()
                
                from django.contrib.auth.hashers import make_password
                user = UserRegister.objects.filter(models.Q(mobile=identity) | models.Q(email=identity)).first()
                user.password = make_password(new_password)
                user.save()
                
                del request.session['reset_identity']
                messages.success(request, "Password reset successfully. You can now login.")
                return redirect('quiz:login')
            else:
                messages.error(request, "Invalid OTP.")
                
    return render(request, 'quiz/reset_password.html')


def login_view(request):
    # If admin is logged in via Django auth
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('quiz:admin_dashboard')
    # If student is logged in via custom session
    if request.session.get('student_id'):
        return redirect('quiz:dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # 1. Check if it's an admin (using standard Django auth)
        user = authenticate(username=username, password=password)
        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
            messages.success(request, f"Welcome back Admin, {user.username}!")
            next_url = request.POST.get('next') or request.GET.get('next')
            return redirect(next_url if next_url else 'quiz:admin_dashboard')
            
        # 2. Check if it's a student (using custom UserRegister table)
        try:
            student = UserRegister.objects.get(username=username)
            if check_password(password, student.password):
                student.current_session_start = timezone.now()
                student.save()
                request.session['student_id'] = student.id
                messages.success(request, f"Welcome back, {student.username}!")
                next_url = request.POST.get('next') or request.GET.get('next')
                return redirect(next_url if next_url else 'quiz:dashboard')
        except UserRegister.DoesNotExist:
            pass
            
        messages.error(request, "Invalid username or password.")
        # Re-initialize form with data so it renders errors if needed
        form = AuthenticationForm(request, data=request.POST)
    else:
        form = AuthenticationForm()
    return render(request, 'quiz/login.html', {'form': form})


def logout_view(request):
    logout(request)
    if 'student_id' in request.session:
        del request.session['student_id']
    messages.info(request, "Logged out successfully.")
    return redirect('quiz:welcome')


# --- Student Dashboard & Exam Views ---

@student_required
def dashboard(request):
    user = request.student
    
    # Calculate Student Stats
    attempts = QuizAttempt.objects.filter(user=user, status='Completed')
    total_taken = attempts.count()
    
    passed_attempts = attempts.filter(passed=True)
    total_passed = passed_attempts.count()
    
    avg_score = attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0.0
    best_score = attempts.aggregate(Max('percentage'))['percentage__max'] or 0.0
    total_time = attempts.aggregate(Sum('time_taken'))['time_taken__sum'] or 0
    total_time_min = round(total_time / 60, 1)

    # Quiz Queryset
    quizzes_qs = Quiz.objects.filter(status='Published').annotate(num_questions=Count('questions'))
    
    # Search & Filtering
    search_query = request.GET.get('search', '')
    if search_query:
        quizzes_qs = quizzes_qs.filter(title__icontains=search_query)
        
    cat_filter = request.GET.get('category', 'all')
    if cat_filter != 'all':
        quizzes_qs = quizzes_qs.filter(category__name=cat_filter)
        
    diff_filter = request.GET.get('difficulty', 'all')
    if diff_filter != 'all':
        quizzes_qs = quizzes_qs.filter(difficulty=diff_filter)
        
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by in ['title', '-title', 'duration', '-duration', 'passing_score', '-passing_score', '-created_at']:
        quizzes_qs = quizzes_qs.order_by(sort_by)

    # Categories list for filters with attempt counts per category
    categories = Category.objects.all().annotate(
        published_count=Count('quizzes', filter=Q(quizzes__status='Published'))
    )

    if user.target_exam:
        categories = categories.filter(name=user.target_exam)
        # Default quiz list to their target exam as well
        if cat_filter == 'all':
            quizzes_qs = quizzes_qs.filter(category__name=user.target_exam)

    # Build per-category user attempt stats
    category_stats = []
    for cat in categories:
        cat_attempts = attempts.filter(quiz__category=cat)
        cat_taken = cat_attempts.count()
        cat_passed = cat_attempts.filter(passed=True).count()
        cat_avg = cat_attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0.0
        category_stats.append({
            'category': cat,
            'taken': cat_taken,
            'passed': cat_passed,
            'avg': round(cat_avg, 1),
        })

    # Pagination
    paginator = Paginator(quizzes_qs, 12)  # 12 quizzes per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Attach attempts to each quiz on the current page for template access
    for quiz in page_obj.object_list:
        quiz.user_attempts = QuizAttempt.objects.filter(quiz=quiz, user=user, status='Completed').order_by('-completed_at')
        quiz.has_attempted = quiz.user_attempts.exists()

    # Calculate pending quizzes (Published quizzes not yet completed by this user)
    completed_quiz_ids = attempts.values_list('quiz_id', flat=True)
    pending_count = Quiz.objects.filter(status='Published').exclude(id__in=completed_quiz_ids).count()

    # Fetch User Notifications
    notifications = user.notifications.filter(is_read=False)[:5]

    # Recent attempts and improvement trend (last 8 for chart)
    recent_attempts = list(attempts.order_by('-completed_at')[:8])
    recent_attempts_chronological = list(reversed(recent_attempts))
    chart_data = [
        {
            'date': attempt.completed_at.strftime('%d %b'),
            'percentage': round(attempt.percentage or 0),
            'label': attempt.quiz.title[:22],
            'passed': attempt.passed,
            'grade': attempt.grade,
        }
        for attempt in recent_attempts_chronological
    ]
    improvement_delta = None
    improvement_text = ''
    if len(chart_data) >= 2:
        start_score = chart_data[0]['percentage']
        latest_score = chart_data[-1]['percentage']
        improvement_delta = latest_score - start_score
        improvement_text = f"{abs(improvement_delta)}% {'improvement' if improvement_delta >= 0 else 'drop'} since your earliest recent test"

    # Calculate expiring subscription (within 5 days)
    expiry_threshold = timezone.now() + timedelta(days=5)
    expiring_subscription = UserSubscription.objects.filter(
        user=user, 
        is_active=True, 
        end_date__isnull=False,
        end_date__gt=timezone.now(),
        end_date__lte=expiry_threshold
    ).order_by('end_date').first()
    
    days_to_expiry = None
    if expiring_subscription:
        days_to_expiry = (expiring_subscription.end_date - timezone.now()).days

    # Pass rate
    pass_rate = round((total_passed / total_taken * 100), 1) if total_taken > 0 else 0.0

    # Serialize chart_data to valid JSON (Python True/False → JSON true/false)
    import json as _json
    chart_data_json = _json.dumps(chart_data)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'category_stats': category_stats,
        'notifications': notifications,
        'stats': {
            'total_quizzes': Quiz.objects.filter(status='Published').count(),
            'total_taken': total_taken,
            'pending_count': pending_count,
            'avg_score': round(avg_score, 1),
            'best_score': round(best_score, 1),
            'total_time': total_time_min,
            'total_passed': total_passed,
            'total_failed': total_taken - total_passed,
            'pass_rate': pass_rate,
        },
        'search_query': search_query,
        'cat_filter': cat_filter,
        'diff_filter': diff_filter,
        'sort_by': sort_by,
        'chart_data': chart_data,
        'chart_data_json': chart_data_json,
        'improvement_delta': improvement_delta,
        'improvement_text': improvement_text,
        'recent_attempts': recent_attempts,
        'expiring_subscription': expiring_subscription,
        'days_to_expiry': days_to_expiry,
    }
    return render(request, 'quiz/dashboard.html', context)

@student_required
def quiz_overview(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    now = timezone.now()
    if quiz.start_date and now < quiz.start_date:
        messages.warning(request, f"This quiz is not available yet. It opens on {quiz.start_date.strftime('%Y-%m-%d %H:%M')}.")
        return redirect('quiz:dashboard')
    if quiz.end_date and now > quiz.end_date:
        messages.warning(request, "This quiz is no longer available as the deadline has passed.")
        return redirect('quiz:dashboard')

    sections = quiz.sections.all()
    general_questions = quiz.questions.filter(section__isnull=True).count()
    total_questions = quiz.questions.count()
    
    context = {
        'quiz': quiz,
        'sections': sections,
        'general_questions_count': general_questions,
        'total_questions': total_questions,
        'is_demo': False,
    }
    return render(request, 'quiz/overview.html', context)


@student_required
def play_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check accessibility dates
    now = timezone.now()
    if quiz.start_date and now < quiz.start_date:
        messages.warning(request, f"This quiz is not available yet. It opens on {quiz.start_date.strftime('%Y-%m-%d %H:%M')}.")
        return redirect('quiz:dashboard')
    if quiz.end_date and now > quiz.end_date:
        messages.warning(request, "This quiz is no longer available as the deadline has passed.")
        return redirect('quiz:dashboard')

    # Check max attempts limit
    completed_attempts = QuizAttempt.objects.filter(user=request.student, quiz=quiz, status='Completed').count()
    if completed_attempts >= quiz.max_attempts:
        messages.warning(request, f"You have already reached the maximum attempts ({quiz.max_attempts}) allowed for this quiz.")
        return redirect('quiz:dashboard')

    questions_qs = quiz.questions.all().prefetch_related('choices')
    if not questions_qs.exists():
        messages.warning(request, "This quiz has no questions yet.")
        return redirect('quiz:dashboard')

    # Force query to list so we can use .index() later
    questions = list(questions_qs)

    # Retrieve or create InProgress QuizAttempt
    attempt, created = QuizAttempt.objects.get_or_create(
        user=request.student,
        quiz=quiz,
        status='InProgress',
        defaults={'total_questions': len(questions)}
    )

    # Shuffle questions if enabled
    if quiz.shuffle_questions:
        import random
        random.seed(attempt.id) # deterministic shuffle per attempt
        random.shuffle(questions)

    # Initialize empty responses for this attempt if not already present
    for question in questions:
        UserResponse.objects.get_or_create(
            attempt=attempt,
            question=question
        )

    # Group questions by section if sections exist
    sections_data = []
    has_general_questions = False
    if quiz.sections.exists():
        sections = list(quiz.sections.all().order_by('order'))
        
        grouped_questions = []
        for sec in sections:
            sec_questions = [q for q in questions if q.section_id == sec.id]
            if sec_questions:
                start_idx = len(grouped_questions)
                grouped_questions.extend(sec_questions)
                end_idx = len(grouped_questions)
                sections_data.append({
                    'id': sec.id,
                    'title': sec.title,
                    'time_limit': sec.time_limit * 60 if sec.time_limit else 0,
                    'q_indices': list(range(start_idx, end_idx))
                })
                
        no_sec_questions = [q for q in questions if q.section_id is None]
        if no_sec_questions:
            has_general_questions = True
            start_idx = len(grouped_questions)
            grouped_questions.extend(no_sec_questions)
            end_idx = len(grouped_questions)
            sections_data.append({
                'id': 'general',
                'title': 'General',
                'time_limit': 0,
                'q_indices': list(range(start_idx, end_idx))
            })
            
        questions = grouped_questions

    import json
    context = {
        'quiz': quiz,
        'questions': questions,
        'attempt': attempt,
        'time_limit': quiz.time_limit, # time limit in seconds
        'has_sections': quiz.sections.exists(),
        'has_general_questions': has_general_questions,
        'sections_data_json': json.dumps(sections_data) if sections_data else 'null',
    }
    return render(request, 'quiz/play.html', context)


@student_required
def submit_quiz(request, quiz_id):
    if request.method != 'POST':
        return redirect('quiz:dashboard')
        
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()
    total_questions = questions.count()
    
    attempt, created = QuizAttempt.objects.get_or_create(
        user=request.student,
        quiz=quiz,
        status='InProgress',
        defaults={'total_questions': total_questions}
    )
    
    correct_answers = 0
    total_score = 0
    
    review_q_str = request.POST.get('review_questions', '')
    review_q_ids = [int(q_id) for q_id in review_q_str.split(',') if q_id.strip().isdigit()]
    
    # Process each question and evaluate
    for question in questions:
        response, created = UserResponse.objects.get_or_create(attempt=attempt, question=question)
        response.is_marked_for_review = (question.id in review_q_ids)
        
        # Evaluate based on question type
        is_correct = False
        question_score = 0
        
        if question.question_type in ['MCQ', 'TrueFalse', 'Image']:
            selected_choice_id = request.POST.get(f'question_{question.id}')
            if selected_choice_id:
                try:
                    choice = Choice.objects.get(id=selected_choice_id, question=question)
                    response.selected_choice = choice
                    response.selected_choices.set([choice])
                    if choice.is_correct:
                        is_correct = True
                except Choice.DoesNotExist:
                    pass
                    
        elif question.question_type == 'MultipleAnswers':
            selected_choice_ids = request.POST.getlist(f'question_{question.id}')
            choices = list(Choice.objects.filter(id__in=selected_choice_ids, question=question))
            response.selected_choices.set(choices)
            
            # Check if correct choices matches exactly
            correct_choices = list(question.choices.filter(is_correct=True))
            if set(choices) == set(correct_choices) and len(choices) > 0:
                is_correct = True
                
        elif question.question_type in ['FillBlank', 'Programming', 'Paragraph']:
            submitted_text = request.POST.get(f'question_{question.id}', '').strip()
            response.submitted_text = submitted_text
            
            # Simple case-insensitive match for short fill blank questions
            correct_text = question.correct_answer_text.strip() if question.correct_answer_text else ""
            if question.question_type == 'FillBlank':
                if submitted_text.lower() == correct_text.lower() and correct_text:
                    is_correct = True
            else:
                # For Paragraph / Code programming, check text is provided and non-empty
                if submitted_text:
                    is_correct = True # mark as correct for simple grading, or admin can review
        
        # Apply marks and negative markings
        if is_correct:
            correct_answers += 1
            question_score = question.points
            total_score += question_score
        else:
            if quiz.negative_marking:
                question_score = -abs(question.negative_marks or quiz.negative_marks_per_question)
                total_score += question_score
                
        response.save()

    # Calculate final attempt values
    time_taken = int(request.POST.get('time_taken', 0))
    percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    passed = percentage >= quiz.passing_score

    # Calculate Grade
    if percentage >= 90:
        grade = 'A'
    elif percentage >= 80:
        grade = 'B'
    elif percentage >= 70:
        grade = 'C'
    elif percentage >= 60:
        grade = 'D'
    else:
        grade = 'F'

    # Save Attempt
    attempt.score = max(total_score, 0) # Score cannot be negative
    attempt.correct_answers = correct_answers
    attempt.percentage = round(percentage, 1)
    attempt.passed = passed
    attempt.time_taken = time_taken
    attempt.grade = grade
    attempt.status = 'Completed'
    attempt.save()

    # Leaderboard Update / Calculation
    accuracy = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    # Calculate Rank
    better_attempts = QuizAttempt.objects.filter(
        quiz=quiz, 
        status='Completed'
    ).filter(
        models.Q(percentage__gt=percentage) | 
        models.Q(percentage=percentage, time_taken__lt=time_taken)
    ).count()
    user_rank = better_attempts + 1

    Leaderboard.objects.create(
        quiz=quiz,
        user=request.student,
        score=attempt.score,
        percentage=attempt.percentage,
        time_taken=time_taken,
        accuracy=round(accuracy, 1),
        rank=user_rank
    )

    # Recalculate other rankings for this quiz to keep it consistent
    all_rankings = QuizAttempt.objects.filter(quiz=quiz, status='Completed').order_by('-percentage', 'time_taken')
    for idx, att in enumerate(all_rankings):
        # Update matching leaderboard entries if any
        Leaderboard.objects.filter(quiz=quiz, user=att.user, score=att.score).update(rank=idx + 1)

    # Generate Certificate if passed
    if passed:
        cert_code = f"CERT-{attempt.id}-{uuid.uuid4().hex[:6].upper()}"
        Certificate.objects.get_or_create(
            user=request.student,
            quiz=quiz,
            attempt=attempt,
            defaults={'certificate_code': cert_code}
        )
        # Notify user
        Notification.objects.create(
            user=request.student,
            title="Certificate Issued!",
            message=f"Congratulations! You passed the '{quiz.title}' quiz and earned a certificate.",
            notification_type="Success"
        )

    return redirect('quiz:results', attempt_id=attempt.id)


@student_required
def quiz_results(request, attempt_id):
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related('quiz').prefetch_related(
            'responses__question', 'responses__selected_choices', 'responses__question__choices'
        ),
        id=attempt_id
    )
    
    if attempt.user != request.student:
        return HttpResponseForbidden("Access Denied.")

    # Calculate skipped vs wrong count and section stats
    skipped_count = 0
    wrong_count = 0
    
    section_stats = {}
    has_sections = attempt.quiz.sections.exists()
    
    for resp in attempt.responses.all():
        sec_name = resp.question.section.title if resp.question.section else "General"
        if sec_name not in section_stats:
            section_stats[sec_name] = {
                'name': sec_name,
                'total': 0,
                'correct': 0,
                'wrong': 0,
                'skipped': 0,
                'review': 0,
                'points_earned': 0,
                'total_points': 0
            }
        
        s_stat = section_stats[sec_name]
        s_stat['total'] += 1
        s_stat['total_points'] += resp.question.points
        
        is_skipped = False
        is_correct = False
        
        if resp.question.question_type in ['MCQ', 'TrueFalse', 'Image', 'MultipleAnswers']:
            if resp.selected_choices.count() == 0:
                is_skipped = True
            else:
                if resp.question.question_type == 'MultipleAnswers':
                    correct_choices = set(resp.question.choices.filter(is_correct=True))
                    selected_choices = set(resp.selected_choices.all())
                    if correct_choices == selected_choices:
                        is_correct = True
                else:
                    if resp.selected_choice and resp.selected_choice.is_correct:
                        is_correct = True
        else:
            if not resp.submitted_text:
                is_skipped = True
            else:
                correct_text = resp.question.correct_answer_text.strip() if resp.question.correct_answer_text else ""
                if resp.question.question_type == 'FillBlank':
                    if resp.submitted_text.lower() == correct_text.lower():
                        is_correct = True
                else:
                    # Programming / Paragraph default correct
                    is_correct = True
        
        if is_skipped:
            skipped_count += 1
            s_stat['skipped'] += 1
        elif is_correct:
            s_stat['correct'] += 1
            s_stat['points_earned'] += resp.question.points
        else:
            wrong_count += 1
            s_stat['wrong'] += 1
            
        if resp.is_marked_for_review:
            s_stat['review'] += 1
            
    for stat in section_stats.values():
        stat['score_pct'] = round((stat['points_earned'] / stat['total_points'] * 100), 1) if stat['total_points'] > 0 else 0

    # Check for Certificate link
    certificate = Certificate.objects.filter(attempt=attempt).first()

    # Fetch User Leaderboard entry
    rank_entry = Leaderboard.objects.filter(quiz=attempt.quiz, user=attempt.user).order_by('-score').first()
    rank = rank_entry.rank if rank_entry else '-'

    # Format time taken
    mins = attempt.time_taken // 60
    secs = attempt.time_taken % 60
    time_taken_str = f"{mins}m {secs}s"

    context = {
        'attempt': attempt,
        'skipped_count': skipped_count,
        'wrong_count': wrong_count,
        'time_taken_str': time_taken_str,
        'certificate': certificate,
        'rank': rank,
        'has_sections': has_sections,
        'section_stats': section_stats.values(),
    }
    return render(request, 'quiz/results.html', context)


# --- Certificate & Profiles & Leaderboards ---

@student_required
def view_certificate(request, certificate_id):
    cert = get_object_or_404(Certificate.objects.select_related('user', 'quiz', 'attempt'), id=certificate_id)
    if cert.user != request.student:
        return HttpResponseForbidden("Access Denied.")
    return render(request, 'quiz/certificate.html', {'cert': cert})


@student_required
def student_profile(request):
    profile = request.student
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('quiz:profile')
    else:
        form = UserProfileForm(instance=profile)

    completed_attempts = QuizAttempt.objects.filter(user=request.student, status='Completed')
    certificates = Certificate.objects.filter(user=request.student).select_related('quiz')
    subscriptions = UserSubscription.objects.filter(user=request.student).select_related('plan').order_by('-start_date')

    context = {
        'profile': profile,
        'form': form,
        'attempts': completed_attempts,
        'certificates': certificates,
        'subscriptions': subscriptions,
    }
    return render(request, 'quiz/student_profile.html', context)


@student_required
def subscription_plans(request):
    plans = SubscriptionPlan.objects.all().prefetch_related('features').order_by('order')
    return render(request, 'quiz/subscriptions.html', {'plans': plans})

@student_required
def checkout(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    
    # In a mock payment flow, we simulate sending a transaction payload
    # to the gateway. Here we just present the confirmation page.
    context = {
        'plan': plan,
    }
    return render(request, 'quiz/checkout.html', context)

@student_required
def payment_success(request):
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)
        
        user_reg = request.student
        
        # Find the latest active subscription end date to support stacking
        latest_sub = UserSubscription.objects.filter(
            user=user_reg, 
            is_active=True
        ).order_by('-end_date').first()
        
        now = timezone.now()
        if latest_sub and latest_sub.end_date and latest_sub.end_date > now:
            start_date = latest_sub.end_date
        else:
            start_date = now
            
        # Calculate expiration
        if plan.duration_days > 0:
            end_date = start_date + timedelta(days=plan.duration_days)
        else:
            end_date = None # Lifetime
            
        sub = UserSubscription.objects.create(
            user=user_reg,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            payment_reference=f"MOCK_{uuid.uuid4().hex[:8].upper()}",
            amount_paid=plan.price
        )
        
        messages.success(request, f"Successfully subscribed to {plan.name}!")
        return render(request, 'quiz/payment_success.html', {'sub': sub})
        
    return redirect('quiz:subscriptions')

@student_required
def payment_failed(request):
    messages.error(request, "Payment failed or was cancelled. Please try again.")
    return render(request, 'quiz/payment_failed.html')

@student_required
def leaderboard(request):
    quizzes = Quiz.objects.filter(status='Published')
    selected_quiz_id = request.GET.get('quiz_id')
    
    rankings = []
    selected_quiz = None
    
    if selected_quiz_id:
        selected_quiz = get_object_or_404(Quiz, id=selected_quiz_id)
        rankings = Leaderboard.objects.filter(quiz=selected_quiz).select_related('user').order_by('rank', 'time_taken')[:20]
    else:
        # Default overall leaderboard based on sum of percentages across all attempts
        rankings = Leaderboard.objects.select_related('user', 'quiz').order_by('-score', 'time_taken')[:20]

    # Calculate leaderboards stats metrics
    top_accuracy = Leaderboard.objects.select_related('user', 'quiz').order_by('-accuracy', 'time_taken')[:5]
    fastest = Leaderboard.objects.select_related('user', 'quiz').filter(percentage__gte=60).order_by('time_taken')[:5]

    context = {
        'quizzes': quizzes,
        'rankings': rankings,
        'selected_quiz': selected_quiz,
        'top_accuracy': top_accuracy,
        'fastest': fastest,
    }
    return render(request, 'quiz/leaderboard.html', context)


# --- APIs for Interactive State Save & Notifications ---

@student_required
def api_save_answer(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
        
    try:
        data = json.loads(request.body)
        attempt_id = data.get('attempt_id')
        question_id = data.get('question_id')
        
        attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.student, status='InProgress')
        question = get_object_or_404(Question, id=question_id)
        response, created = UserResponse.objects.get_or_create(attempt=attempt, question=question)

        q_type = question.question_type
        if q_type in ['MCQ', 'TrueFalse', 'Image']:
            choice_id = data.get('choice_id')
            if choice_id:
                choice = Choice.objects.get(id=choice_id, question=question)
                response.selected_choice = choice
                response.selected_choices.set([choice])
            else:
                response.selected_choice = None
                response.selected_choices.clear()
                
        elif q_type == 'MultipleAnswers':
            choice_ids = data.get('choice_ids', [])
            choices = Choice.objects.filter(id__in=choice_ids, question=question)
            response.selected_choices.set(choices)
            
        elif q_type in ['FillBlank', 'Programming', 'Paragraph']:
            submitted_text = data.get('submitted_text', '')
            response.submitted_text = submitted_text

        response.save()
        return JsonResponse({'status': 'success', 'message': 'Answer auto-saved.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@student_required
def api_mark_notification_read(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, user=request.student)
    notif.is_read = True
    notif.save()
    return JsonResponse({'status': 'success', 'message': 'Notification read.'})


# --- Admin Panel / Instructor Views ---

@user_passes_test(is_admin)
def admin_dashboard(request):
    users = UserRegister.objects.all()
    students_count = users.count()
    quizzes = Quiz.objects.all()
    active_quizzes_count = quizzes.filter(status='Published').count()
    questions_count = Question.objects.count()
    categories_count = Category.objects.count()

    recent_attempts = QuizAttempt.objects.all().select_related('quiz', 'user').order_by('-completed_at')[:10]
    recent_quizzes = Quiz.objects.all().select_related('category').order_by('-created_at')[:5]

    online_threshold = timezone.now() - timedelta(minutes=5)
    online_users = UserRegister.objects.filter(last_active__gte=online_threshold).order_by('-last_active')

    stats = {
        'total_users': users.count(),
        'total_students': students_count,
        'total_quizzes': quizzes.count(),
        'active_quizzes': active_quizzes_count,
        'total_questions': questions_count,
        'total_categories': categories_count,
        'online_users_count': online_users.count(),
    }

    context = {
        'stats': stats,
        'recent_attempts': recent_attempts,
        'recent_quizzes': recent_quizzes,
        'online_users': online_users,
    }
    return render(request, 'quiz/admin_dashboard.html', context)


# Subscription Management CRUD
@user_passes_test(is_admin)
def admin_subscriptions_list(request):
    plans = SubscriptionPlan.objects.all().order_by('order')
    return render(request, 'quiz/admin_subscriptions_list.html', {'plans': plans})

@user_passes_test(is_admin)
def admin_add_subscription(request):
    if request.method == 'POST':
        form = SubscriptionPlanForm(request.POST)
        formset = SubscriptionFeatureFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            plan = form.save()
            formset.instance = plan
            formset.save()
            messages.success(request, "Subscription plan created successfully!")
            return redirect('quiz:admin_subscriptions_list')
    else:
        form = SubscriptionPlanForm()
        formset = SubscriptionFeatureFormSet()
    return render(request, 'quiz/admin_subscription_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Subscription Plan'
    })

@user_passes_test(is_admin)
def admin_edit_subscription(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    if request.method == 'POST':
        form = SubscriptionPlanForm(request.POST, instance=plan)
        formset = SubscriptionFeatureFormSet(request.POST, instance=plan)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Subscription plan updated successfully!")
            return redirect('quiz:admin_subscriptions_list')
    else:
        form = SubscriptionPlanForm(instance=plan)
        formset = SubscriptionFeatureFormSet(instance=plan)
    return render(request, 'quiz/admin_subscription_form.html', {
        'form': form,
        'formset': formset,
        'plan': plan,
        'title': 'Edit Subscription Plan'
    })

@user_passes_test(is_admin)
def admin_delete_subscription(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    if request.method == 'POST':
        plan.delete()
        messages.success(request, "Subscription plan deleted successfully!")
    return redirect('quiz:admin_subscriptions_list')

# Category Management CRUD
@user_passes_test(is_admin)
def admin_categories_list(request):
    categories = Category.objects.annotate(num_quizzes=Count('quizzes'))
    search_query = request.GET.get('search', '')
    if search_query:
        categories = categories.filter(name__icontains=search_query)
    return render(request, 'quiz/admin_categories_list.html', {'categories': categories, 'search_query': search_query})


@user_passes_test(is_admin)
def admin_add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category created successfully!")
            return redirect('quiz:admin_categories_list')
    else:
        form = CategoryForm()
    return render(request, 'quiz/admin_category_form.html', {
        'form': form,
        'title': 'Create Category',
        'icon_choices': ICON_CHOICES,
    })


@user_passes_test(is_admin)
def admin_edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully!")
            return redirect('quiz:admin_categories_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'quiz/admin_category_form.html', {
        'form': form,
        'category': category,
        'title': 'Edit Category',
        'icon_choices': ICON_CHOICES,
    })


@user_passes_test(is_admin)
def admin_delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Category deleted successfully!")
    return redirect('quiz:admin_categories_list')


# Helper for bulk uploads
def process_questions_file(quiz, file_obj, filename, section_id=None):
    try:
        # Parse JSON
        if filename.endswith('.json'):
            data = json.loads(file_obj.read().decode('utf-8'))
            for item in data:
                q = Question.objects.create(
                    quiz=quiz,
                    section_id=section_id if section_id else None,
                    text=item.get('text', ''),
                    question_type=item.get('type', 'MCQ'),
                    correct_answer_text=item.get('correct_answer_text', ''),
                    difficulty=item.get('difficulty', 'Medium'),
                    points=int(item.get('points', 1)),
                    explanation=item.get('explanation', '')
                )
                options = item.get('options', [])
                for opt in options:
                    Choice.objects.create(question=q, text=opt.get('text'), is_correct=opt.get('is_correct', False))
            return True, f"Successfully uploaded JSON questions to '{quiz.title}'!"

        # Parse Excel / CSV using pandas for auto-fill based on specific columns
        elif filename.endswith(('.csv', '.xlsx', '.xls')):
            if filename.endswith('.csv'):
                df = pd.read_csv(file_obj)
            else:
                df = pd.read_excel(file_obj)
            
            if 'Question' in df.columns:
                count = 0
                
                # Pre-fetch existing sections for row-level assignment
                section_map = {s.title.lower().strip(): s.id for s in quiz.sections.all()}
                
                for index, row in df.iterrows():
                    q_text = str(row.get('Question', '')).strip()
                    if pd.isna(row.get('Question')) or not q_text or q_text == 'nan':
                        continue
                        
                    explanation_val = row.get('Explanation', '')
                    explanation = str(explanation_val) if not pd.isna(explanation_val) else ''
                    if explanation.lower() == 'nan':
                        explanation = ''

                    answer_val = row.get('Answer', '')
                    answer_text = str(answer_val).strip().lower() if not pd.isna(answer_val) else ''
                    if answer_text == 'nan':
                        answer_text = ''
                        
                    # Row-level section assignment
                    row_section_id = section_id
                    if 'Section' in df.columns:
                        sec_val = row.get('Section', '')
                        if not pd.isna(sec_val) and str(sec_val).strip() and str(sec_val).lower() != 'nan':
                            sec_title = str(sec_val).strip().lower()
                            if sec_title in section_map:
                                row_section_id = section_map[sec_title]
                    
                    q = Question.objects.create(
                        quiz=quiz,
                        section_id=row_section_id if row_section_id else None,
                        text=q_text,
                        question_type='MCQ',
                        correct_answer_text='',
                        difficulty='Medium',
                        points=1,
                        explanation=explanation
                    )
                    count += 1
                    
                    options_data = [
                        ('Option A', 'A', row.get('Option A', '')),
                        ('Option B', 'B', row.get('Option B', '')),
                        ('Option C', 'C', row.get('Option C', '')),
                        ('Option D', 'D', row.get('Option D', '')),
                    ]
                    
                    for opt_name, opt_letter, opt_val in options_data:
                        if not pd.isna(opt_val) and str(opt_val).strip() and str(opt_val).lower() != 'nan':
                            opt_text_val = str(opt_val).strip()
                            is_correct = False
                            if answer_text:
                                if answer_text == opt_letter.lower():
                                    is_correct = True
                                elif answer_text == opt_name.lower():
                                    is_correct = True
                                elif answer_text == opt_text_val.lower():
                                    is_correct = True
                            
                            Choice.objects.create(
                                question=q,
                                text=opt_text_val,
                                is_correct=is_correct
                            )
                return True, f"Successfully auto-filled and created {count} questions for '{quiz.title}' from {filename}!"
            else:
                if 'text' in df.columns:
                    for index, row in df.iterrows():
                        q = Question.objects.create(
                            quiz=quiz,
                            text=str(row.get('text', '')),
                            question_type=str(row.get('type', 'MCQ')),
                            correct_answer_text=str(row.get('correct_answer_text', '')),
                            difficulty=str(row.get('difficulty', 'Medium')),
                            points=int(row.get('points', 1)) if not pd.isna(row.get('points')) else 1,
                            explanation=str(row.get('explanation', '')) if not pd.isna(row.get('explanation')) else ''
                        )
                        correct_choices_str = str(row.get('correct_choices', ''))
                        correct_indexes = [int(i.strip()) for i in correct_choices_str.split(',') if i.strip() and i.strip().isdigit()]
                        
                        for idx, opt_col in enumerate(['choice1', 'choice2', 'choice3', 'choice4'], start=1):
                            opt_text = row.get(opt_col)
                            if not pd.isna(opt_text) and str(opt_text).strip():
                                Choice.objects.create(
                                    question=q,
                                    text=str(opt_text).strip(),
                                    is_correct=(idx in correct_indexes)
                                )
                    return True, f"Successfully uploaded legacy CSV questions to '{quiz.title}'!"
                else:
                    return False, "Invalid file format. Please ensure columns match the provided template (e.g. Question, Option A, Option B...)."
        else:
            return False, "Format unsupported! Please upload a valid Excel, CSV or JSON file."
    except Exception as e:
        return False, f"Error processing file: {str(e)}"

# Quiz Management CRUD overrides
@user_passes_test(is_admin)
def admin_add_quiz(request):
    from .forms import QuizForm, QuizSectionFormSet, QuizConditionFormSet
    if request.method == 'POST':
        form = QuizForm(request.POST)
        section_formset = QuizSectionFormSet(request.POST)
        condition_formset = QuizConditionFormSet(request.POST)
        if not (form.is_valid() and section_formset.is_valid() and condition_formset.is_valid()):
            print("FORM ERRORS:", form.errors)
            print("SECTION ERRORS:", section_formset.errors)
            print("CONDITION ERRORS:", condition_formset.errors)
            print("SECTION NON FORM ERRORS:", section_formset.non_form_errors())
            if form.errors:
                messages.error(request, f"Form Errors: {form.errors}")
            if section_formset.errors and any(section_formset.errors):
                messages.error(request, f"Section Errors: {section_formset.errors}")
            if section_formset.non_form_errors():
                messages.error(request, f"Section Formset Errors: {section_formset.non_form_errors()}")
            
        if form.is_valid() and section_formset.is_valid() and condition_formset.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()
            section_formset.instance = quiz
            section_formset.save()
            condition_formset.instance = quiz
            condition_formset.save()
            
            messages.success(request, f"Quiz '{quiz.title}' has been created successfully! Now add questions.")
            return redirect('quiz:admin_add_question', quiz_id=quiz.id)
    else:
        form = QuizForm()
        section_formset = QuizSectionFormSet()
        condition_formset = QuizConditionFormSet()
    return render(request, 'quiz/admin_quiz_form.html', {'form': form, 'section_formset': section_formset, 'condition_formset': condition_formset, 'title': 'Create Quiz'})


@user_passes_test(is_admin)
def admin_edit_quiz(request, quiz_id):
    from .forms import QuizForm, QuizSectionFormSet, QuizConditionFormSet
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        section_formset = QuizSectionFormSet(request.POST, instance=quiz)
        condition_formset = QuizConditionFormSet(request.POST, instance=quiz)
        if not (form.is_valid() and section_formset.is_valid() and condition_formset.is_valid()):
            print("FORM ERRORS:", form.errors)
            print("SECTION ERRORS:", section_formset.errors)
            print("CONDITION ERRORS:", condition_formset.errors)
            print("SECTION NON FORM ERRORS:", section_formset.non_form_errors())
            if form.errors:
                messages.error(request, f"Form Errors: {form.errors}")
            if section_formset.errors and any(section_formset.errors):
                messages.error(request, f"Section Errors: {section_formset.errors}")
            if section_formset.non_form_errors():
                messages.error(request, f"Section Formset Errors: {section_formset.non_form_errors()}")
            
        if form.is_valid() and section_formset.is_valid() and condition_formset.is_valid():
            form.save()
            section_formset.save()
            condition_formset.save()
            messages.success(request, "Quiz updated successfully!")
            return redirect('quiz:admin_dashboard')
    else:
        form = QuizForm(instance=quiz)
        section_formset = QuizSectionFormSet(instance=quiz)
        condition_formset = QuizConditionFormSet(instance=quiz)
    return render(request, 'quiz/admin_quiz_form.html', {'form': form, 'section_formset': section_formset, 'condition_formset': condition_formset, 'quiz': quiz, 'title': 'Edit Quiz'})


@user_passes_test(is_admin)
def admin_delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.method == 'POST':
        title = quiz.title
        quiz.delete()
        messages.success(request, f"Quiz '{title}' has been deleted.")
    return redirect('quiz:admin_dashboard')


@user_passes_test(is_admin)
def admin_duplicate_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all().prefetch_related('choices')
    
    # Clone Quiz
    quiz.pk = None
    quiz.title = f"Copy of {quiz.title}"
    quiz.status = 'Draft'
    quiz.save()
    
    # Clone Questions & Choices
    for q in questions:
        old_choices = list(q.choices.all())
        q.pk = None
        q.quiz = quiz
        q.save()
        for choice in old_choices:
            choice.pk = None
            choice.question = q
            choice.save()
            
    messages.success(request, "Quiz duplicated successfully!")
    return redirect('quiz:admin_dashboard')


# Question Management overrides
@user_passes_test(is_admin)
def admin_add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.method == 'POST':
        # Check if this is a bulk upload
        file_obj = request.FILES.get('questions_file')
        if file_obj:
            section_id = request.POST.get('upload_section')
            success, msg = process_questions_file(quiz, file_obj, file_obj.name.lower(), section_id)
            if success:
                messages.success(request, msg)
            else:
                messages.error(request, msg)
            from django.urls import reverse
            url = reverse('quiz:admin_add_question', args=[quiz.id])
            return redirect(f"{url}?tab=autofill")

        # Otherwise, process the standard question form
        form = QuestionForm(request.POST, quiz=quiz)
        if form.is_valid():
            question = Question.objects.create(
                quiz=quiz,
                section=form.cleaned_data.get('section'),
                text=form.cleaned_data['text'],
                question_type=form.cleaned_data['question_type'],
                correct_answer_text=form.cleaned_data['correct_answer_text'],
                difficulty=form.cleaned_data['difficulty'],
                image_url=form.cleaned_data['image_url'],
                points=form.cleaned_data['points'],
                negative_marks=form.cleaned_data['negative_marks'],
                explanation=form.cleaned_data['explanation']
            )
            
            # Save choices if MCQ, MultiAnswer, True/False, or Image
            if form.cleaned_data['question_type'] in ['MCQ', 'MultipleAnswers', 'TrueFalse', 'Image']:
                if form.cleaned_data['choice1_text']:
                    Choice.objects.create(question=question, text=form.cleaned_data['choice1_text'], is_correct=form.cleaned_data['choice1_correct'])
                if form.cleaned_data['choice2_text']:
                    Choice.objects.create(question=question, text=form.cleaned_data['choice2_text'], is_correct=form.cleaned_data['choice2_correct'])
                if form.cleaned_data['choice3_text']:
                    Choice.objects.create(question=question, text=form.cleaned_data['choice3_text'], is_correct=form.cleaned_data['choice3_correct'])
                if form.cleaned_data['choice4_text']:
                    Choice.objects.create(question=question, text=form.cleaned_data['choice4_text'], is_correct=form.cleaned_data['choice4_correct'])
                    
            messages.success(request, "Question added successfully!")
            return redirect('quiz:admin_add_question', quiz_id=quiz.id)
    else:
        section_id = request.GET.get('section_id')
        initial = {}
        if section_id:
            initial['section'] = section_id
        form = QuestionForm(quiz=quiz, initial=initial)
    return render(request, 'quiz/admin_question_form.html', {'form': form, 'quiz': quiz, 'title': 'Add Question'})


@user_passes_test(is_admin)
def admin_edit_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    choices = list(question.choices.all())
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, quiz=question.quiz)
        if form.is_valid():
            question.section = form.cleaned_data.get('section')
            question.text = form.cleaned_data['text']
            question.question_type = form.cleaned_data['question_type']
            question.correct_answer_text = form.cleaned_data['correct_answer_text']
            question.difficulty = form.cleaned_data['difficulty']
            question.image_url = form.cleaned_data['image_url']
            question.points = form.cleaned_data['points']
            question.negative_marks = form.cleaned_data['negative_marks']
            question.explanation = form.cleaned_data['explanation']
            question.save()
            
            # Recreate Choices
            question.choices.all().delete()
            if form.cleaned_data['question_type'] in ['MCQ', 'MultipleAnswers', 'TrueFalse', 'Image']:
                if form.cleaned_data['choice1_text']:
                    Choice.objects.create(question=question, text=form.cleaned_data['choice1_text'], is_correct=form.cleaned_data['choice1_correct'])
                if form.cleaned_data['choice2_text']:
                    Choice.objects.create(question=question, text=form.cleaned_data['choice2_text'], is_correct=form.cleaned_data['choice2_correct'])
                if form.cleaned_data['choice3_text']:
                    Choice.objects.create(question=question, text=form.cleaned_data['choice3_text'], is_correct=form.cleaned_data['choice3_correct'])
                if form.cleaned_data['choice4_text']:
                    Choice.objects.create(question=question, text=form.cleaned_data['choice4_text'], is_correct=form.cleaned_data['choice4_correct'])
                    
            messages.success(request, "Question updated successfully!")
            return redirect('quiz:admin_add_question', quiz_id=question.quiz.id)
    else:
        # Prepopulate initial data
        initial = {
            'section': question.section,
            'text': question.text,
            'question_type': question.question_type,
            'correct_answer_text': question.correct_answer_text,
            'difficulty': question.difficulty,
            'image_url': question.image_url,
            'points': question.points,
            'negative_marks': question.negative_marks,
            'explanation': question.explanation,
            'choice1_text': choices[0].text if len(choices) > 0 else '',
            'choice1_correct': choices[0].is_correct if len(choices) > 0 else False,
            'choice2_text': choices[1].text if len(choices) > 1 else '',
            'choice2_correct': choices[1].is_correct if len(choices) > 1 else False,
            'choice3_text': choices[2].text if len(choices) > 2 else '',
            'choice3_correct': choices[2].is_correct if len(choices) > 2 else False,
            'choice4_text': choices[3].text if len(choices) > 3 else '',
            'choice4_correct': choices[3].is_correct if len(choices) > 3 else False,
        }
        form = QuestionForm(initial=initial, quiz=question.quiz)
        
    return render(request, 'quiz/admin_question_form.html', {'form': form, 'quiz': question.quiz, 'question': question, 'title': 'Edit Question'})


@user_passes_test(is_admin)
def admin_delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    quiz_id = question.quiz.id
    if request.method == 'POST':
        question.delete()
        messages.success(request, "Question deleted successfully.")
    return redirect('quiz:admin_add_question', quiz_id=quiz_id)

@user_passes_test(is_admin)
def admin_quiz_questions_list(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = list(quiz.questions.all().order_by('id'))
    sections = list(quiz.sections.all().order_by('order'))
    
    grouped_questions = []
    for sec in sections:
        sec_qs = [q for q in questions if q.section_id == sec.id]
        grouped_questions.append({
            'section': sec,
            'questions': sec_qs
        })
    
    general_qs = [q for q in questions if q.section_id is None]
    
    return render(request, 'quiz/admin_questions_list.html', {
        'quiz': quiz,
        'grouped_questions': grouped_questions,
        'general_qs': general_qs,
        'title': f'Manage Questions for {quiz.title}'
    })

# Question Bulk Upload & Exports
@user_passes_test(is_admin)
def admin_bulk_upload_questions(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    if request.method == 'POST':
        file_obj = request.FILES.get('file')
        if not file_obj:
            messages.error(request, "Please select a file to upload.")
            return redirect('quiz:admin_bulk_upload_questions', quiz_id=quiz.id)

        filename = file_obj.name.lower()
        success, msg = process_questions_file(quiz, file_obj, filename)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)

        return redirect('quiz:admin_dashboard')

    return render(request, 'quiz/admin_bulk_upload.html', {'quiz': quiz})


@user_passes_test(is_admin)
def admin_export_questions(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all().prefetch_related('choices')
    
    export_format = request.GET.get('format', 'csv')
    
    if export_format == 'json':
        data = []
        for q in questions:
            opts = [{'text': c.text, 'is_correct': c.is_correct} for c in q.choices.all()]
            data.append({
                'text': q.text,
                'type': q.question_type,
                'correct_answer_text': q.correct_answer_text,
                'difficulty': q.difficulty,
                'points': q.points,
                'explanation': q.explanation,
                'options': opts
            })
        response = HttpResponse(json.dumps(data, indent=4), content_type="application/json")
        response['Content-Disposition'] = f'attachment; filename="quiz_{quiz.id}_questions.json"'
        return response
    else:
        # Export CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="quiz_{quiz.id}_questions.csv"'
        writer = csv.writer(response)
        writer.writerow(['text', 'type', 'correct_answer_text', 'difficulty', 'points', 'explanation', 'choice1', 'choice2', 'choice3', 'choice4', 'correct_choices'])
        
        for q in questions:
            choices = list(q.choices.all())
            c1 = choices[0].text if len(choices) > 0 else ''
            c2 = choices[1].text if len(choices) > 1 else ''
            c3 = choices[2].text if len(choices) > 2 else ''
            c4 = choices[3].text if len(choices) > 3 else ''
            
            correct_indexes = []
            for i, c in enumerate(choices, start=1):
                if c.is_correct:
                    correct_indexes.append(str(i))
                    
            writer.writerow([
                q.text, q.question_type, q.correct_answer_text, q.difficulty, q.points, q.explanation,
                c1, c2, c3, c4, ",".join(correct_indexes)
            ])
        return response


# User Management
@user_passes_test(is_admin)
def admin_users_list(request):
    users = UserRegister.objects.all().annotate(num_attempts=Count('quiz_attempts'))
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(username__icontains=search_query)
    return render(request, 'quiz/admin_users_list.html', {'users': users, 'search_query': search_query})


@user_passes_test(is_admin)
def admin_toggle_user_status(request, user_id):
    user_item = get_object_or_404(User, id=user_id)
    if user_item == request.user:
        messages.error(request, "You cannot deactivate yourself!")
    else:
        user_item.is_active = not user_item.is_active
        user_item.save()
        messages.success(request, f"User '{user_item.username}' active status toggled.")
    return redirect('quiz:admin_users_list')


@user_passes_test(is_admin)
def admin_delete_user(request, user_id):
    user_item = get_object_or_404(User, id=user_id)
    if user_item == request.user:
        messages.error(request, "You cannot delete yourself!")
    else:
        username = user_item.username
        user_item.delete()
        messages.success(request, f"User '{username}' has been deleted.")
    return redirect('quiz:admin_users_list')


@user_passes_test(is_admin)
def admin_reset_user_password(request, user_id):
    user_item = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = SetPasswordForm(user_item, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Password reset successfully for '{user_item.username}'!")
            return redirect('quiz:admin_users_list')
    else:
        form = SetPasswordForm(user_item)
    return render(request, 'quiz/admin_reset_password_form.html', {'form': form, 'user_item': user_item})


@user_passes_test(is_admin)
def admin_user_history(request, user_id):
    user_item = get_object_or_404(UserRegister, id=user_id)
    attempts = QuizAttempt.objects.filter(user=user_item, status='Completed').select_related('quiz')
    subscriptions = UserSubscription.objects.filter(user=user_item).select_related('plan').order_by('-start_date')
    return render(request, 'quiz/admin_user_history.html', {'user_item': user_item, 'attempts': attempts, 'subscriptions': subscriptions})


# Reports Panel
@user_passes_test(is_admin)
def admin_reports(request):
    # Fetch aggregates for Daily, Weekly, Monthly attempts counts
    today = timezone.now().date()
    start_of_week = timezone.now() - timezone.timedelta(days=timezone.now().weekday())
    start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0)

    attempts = QuizAttempt.objects.filter(status='Completed')
    daily_count = attempts.filter(completed_at__date=today).count()
    weekly_count = attempts.filter(completed_at__gte=start_of_week).count()
    monthly_count = attempts.filter(completed_at__gte=start_of_month).count()
    yearly_count = attempts.filter(completed_at__year=timezone.now().year).count()

    # Quizzes passing rates
    quiz_reports = list(Quiz.objects.annotate(
        total_attempts=Count('attempts'),
        passed_attempts=Count('attempts', filter=models.Q(attempts__passed=True)),
        avg_score=Avg('attempts__percentage')
    ))
    for q in quiz_reports:
        q.pass_rate = (q.passed_attempts / q.total_attempts * 100) if q.total_attempts > 0 else 0.0

    export_format = request.GET.get('export', '')
    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="quiz_reports.csv"'
        writer = csv.writer(response)
        writer.writerow(['Quiz Title', 'Total Attempts', 'Passed Attempts', 'Average Score (%)'])
        for q in quiz_reports:
            writer.writerow([q.title, q.total_attempts, q.passed_attempts, round(q.avg_score or 0, 1)])
        return response

    context = {
        'stats': {
            'daily': daily_count,
            'weekly': weekly_count,
            'monthly': monthly_count,
            'yearly': yearly_count,
        },
        'quiz_reports': quiz_reports,
    }
    return render(request, 'quiz/admin_reports.html', context)


# --- Demo Version Views ---

def demo_overview(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    sections = quiz.sections.all()
    general_questions = quiz.questions.filter(section__isnull=True).count()
    total_questions = quiz.questions.count()
    
    context = {
        'quiz': quiz,
        'sections': sections,
        'general_questions_count': general_questions,
        'total_questions': total_questions,
        'is_demo': True,
    }
    return render(request, 'quiz/overview.html', context)

def play_demo(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all().prefetch_related('choices')
    return render(request, 'quiz/play_demo.html', {'quiz': quiz, 'questions': questions})


def submit_demo(request, quiz_id):
    if request.method != 'POST':
        return redirect('quiz:welcome')
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()
    
    correct_answers = 0
    total_score = 0
    total_questions = questions.count()
    
    # Simple evaluation
    # Store user choices in a dict to show on results page
    user_selections = {}
    
    for question in questions:
        selected_choice_id = request.POST.get(f'question_{question.id}')
        user_selections[str(question.id)] = selected_choice_id
        if selected_choice_id:
            try:
                choice = Choice.objects.get(id=selected_choice_id, question=question)
                if choice.is_correct:
                    correct_answers += 1
                    total_score += question.points
            except Choice.DoesNotExist:
                pass
                
    percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    # Store in session
    request.session['demo_results'] = {
        'quiz_id': quiz.id,
        'quiz_title': quiz.title,
        'score': total_score,
        'correct_answers': correct_answers,
        'total_questions': total_questions,
        'percentage': round(percentage, 1),
        'passed': percentage >= quiz.passing_score,
        'user_selections': user_selections
    }
    return redirect('quiz:demo_results')


def demo_results(request):
    results = request.session.get('demo_results')
    if not results:
        return redirect('quiz:welcome')
        
    quiz = get_object_or_404(Quiz, id=results['quiz_id'])
    questions = quiz.questions.all().prefetch_related('choices')
    
    # Reconstruct the responses structure that results_demo.html expects
    responses_list = []
    user_selections = results.get('user_selections', {})
    
    for question in questions:
        selected_choice_id = user_selections.get(str(question.id))
        selected_choice = None
        if selected_choice_id:
            try:
                selected_choice = Choice.objects.get(id=selected_choice_id, question=question)
            except Choice.DoesNotExist:
                pass
                
        responses_list.append({
            'question': question,
            'selected_choice': selected_choice,
            'choices': question.choices.all()
        })
        
    results['responses'] = responses_list
    results['quiz_passing_score'] = quiz.passing_score
    
    context = {
        'results': results,
        'quiz': quiz,
        'questions': questions,
    }
    return render(request, 'quiz/results_demo.html', context)
