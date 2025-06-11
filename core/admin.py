from django.contrib import admin
from .models import (
    User, Course, Enrollment, Lesson, Assignment, Submission,
    Grade, Quiz, Question, Discussion
)
from django import forms


# Show only instructors in the Course form
class CourseAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "instructor":
            kwargs["queryset"] = User.objects.filter(role='instructor')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Instructors see only their own courses
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(instructor=request.user)

    # Auto-assign logged-in instructor when creating
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.instructor = request.user
        obj.save()


# Instructors can only pick from their own courses when adding lessons
class LessonAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "course" and not request.user.is_superuser:
            kwargs["queryset"] = Course.objects.filter(instructor=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(course__instructor=request.user)


# Same logic for assignments
class AssignmentAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "course" and not request.user.is_superuser:
            kwargs["queryset"] = Course.objects.filter(instructor=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(course__instructor=request.user)


# Only show submissions related to the instructor's assignments
class SubmissionAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(assignment__course__instructor=request.user)


# Instructors can only grade submissions for their own assignments
class GradeAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(submission__assignment__course__instructor=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "submission" and not request.user.is_superuser:
            kwargs["queryset"] = Submission.objects.filter(
                assignment__course__instructor=request.user
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            if obj.submission.assignment.course.instructor != request.user:
                raise PermissionError("You do not have permission to grade this submission.")
        super().save_model(request, obj, form, change)

admin.site.register(User)
admin.site.register(Course, CourseAdmin)
admin.site.register(Enrollment)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Grade, GradeAdmin)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Discussion)
