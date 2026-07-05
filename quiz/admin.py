from django.contrib import admin
from .models import Quiz, Question, Choice, QuizAttempt, UserResponse

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4

class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_display = ('text', 'quiz', 'points')
    list_filter = ('quiz',)
    search_fields = ('text',)

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

class QuizAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ('title', 'duration', 'passing_score', 'created_by', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('created_at',)

class UserResponseInline(admin.TabularInline):
    model = UserResponse
    extra = 0
    readonly_fields = ('question', 'selected_choice')

class QuizAttemptAdmin(admin.ModelAdmin):
    inlines = [UserResponseInline]
    list_display = ('user', 'quiz', 'score', 'percentage', 'passed', 'completed_at')
    list_filter = ('passed', 'completed_at', 'quiz')
    search_fields = ('user__username', 'quiz__title')
    readonly_fields = ('completed_at',)

admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
admin.site.register(QuizAttempt, QuizAttemptAdmin)
admin.site.register(UserResponse)


