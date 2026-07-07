from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    # Auth & Student Views
    path('', views.welcome, name='welcome'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('quiz/<int:quiz_id>/overview/', views.quiz_overview, name='overview'),
    path('quiz/<int:quiz_id>/play/', views.play_quiz, name='play'),
    path('quiz/<int:quiz_id>/submit/', views.submit_quiz, name='submit'),
    path('attempt/<int:attempt_id>/results/', views.quiz_results, name='results'),
    path('profile/', views.student_profile, name='profile'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('subscriptions/', views.subscription_plans, name='subscriptions'),
    path('checkout/<int:plan_id>/', views.checkout, name='checkout'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    path('certificate/<int:certificate_id>/', views.view_certificate, name='view_certificate'),
    
    # Demo Exam URLs
    path('quiz/<int:quiz_id>/demo/overview/', views.demo_overview, name='demo_overview'),
    path('quiz/<int:quiz_id>/demo/', views.play_demo, name='play_demo'),
    path('quiz/<int:quiz_id>/demo/submit/', views.submit_demo, name='submit_demo'),
    path('exam/demo/results/', views.demo_results, name='demo_results'),
    
    # State Save & Notification APIs
    path('api/save-answer/', views.api_save_answer, name='api_save_answer'),
    path('api/notifications/read/<int:notif_id>/', views.api_mark_notification_read, name='api_mark_notification_read'),
    
    # Admin Panel Workspace
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Admin Subscriptions Management CRUD
    path('admin-dashboard/subscriptions/', views.admin_subscriptions_list, name='admin_subscriptions_list'),
    path('admin-dashboard/subscription/add/', views.admin_add_subscription, name='admin_add_subscription'),
    path('admin-dashboard/subscription/<int:plan_id>/edit/', views.admin_edit_subscription, name='admin_edit_subscription'),
    path('admin-dashboard/subscription/<int:plan_id>/delete/', views.admin_delete_subscription, name='admin_delete_subscription'),

    
    # Admin Categories Management CRUD
    path('admin-dashboard/categories/', views.admin_categories_list, name='admin_categories_list'),
    path('admin-dashboard/category/add/', views.admin_add_category, name='admin_add_category'),
    path('admin-dashboard/category/<int:category_id>/edit/', views.admin_edit_category, name='admin_edit_category'),
    path('admin-dashboard/category/<int:category_id>/delete/', views.admin_delete_category, name='admin_delete_category'),
    
    # Admin Quizzes Management CRUD
    path('admin-dashboard/quiz/add/', views.admin_add_quiz, name='admin_add_quiz'),
    path('admin-dashboard/quiz/<int:quiz_id>/edit/', views.admin_edit_quiz, name='admin_edit_quiz'),
    path('admin-dashboard/quiz/<int:quiz_id>/delete/', views.admin_delete_quiz, name='admin_delete_quiz'),
    path('admin-dashboard/quiz/<int:quiz_id>/duplicate/', views.admin_duplicate_quiz, name='admin_duplicate_quiz'),
    
    # Admin Questions Management CRUD
    path('admin-dashboard/quiz/<int:quiz_id>/question/add/', views.admin_add_question, name='admin_add_question'),
    path('admin-dashboard/question/<int:question_id>/edit/', views.admin_edit_question, name='admin_edit_question'),
    path('admin-dashboard/question/<int:question_id>/delete/', views.admin_delete_question, name='admin_delete_question'),
    
    # Question Imports/Exports
    path('admin-dashboard/quiz/<int:quiz_id>/questions/', views.admin_quiz_questions_list, name='admin_quiz_questions_list'),
    path('admin-dashboard/quiz/<int:quiz_id>/bulk-upload/', views.admin_bulk_upload_questions, name='admin_bulk_upload_questions'),
    path('admin-dashboard/quiz/<int:quiz_id>/export/', views.admin_export_questions, name='admin_export_questions'),
    
    # Admin Users Management CRUD
    path('admin-dashboard/users/', views.admin_users_list, name='admin_users_list'),
    path('admin-dashboard/user/<int:user_id>/toggle/', views.admin_toggle_user_status, name='admin_toggle_user_status'),
    path('admin-dashboard/user/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('admin-dashboard/user/<int:user_id>/reset-password/', views.admin_reset_user_password, name='admin_reset_user_password'),
    path('admin-dashboard/user/<int:user_id>/history/', views.admin_user_history, name='admin_user_history'),
    
    # Admin Reports
    path('admin-dashboard/reports/', views.admin_reports, name='admin_reports'),
]
