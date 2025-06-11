from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User,Grade,Discussion,CourseRating,Course,Lesson,Assignment


class RegisterForm(UserCreationForm):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('instructor', 'Instructor'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name','email', 'password1', 'password2', 'role']


class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['marks', 'feedback']


class DiscussionForm(forms.ModelForm):
    class Meta:
        model = Discussion
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Write your comment...'}),
        }


class RatingForm(forms.ModelForm):
    class Meta:
        model = CourseRating
        fields = ['rating', 'feedback']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'feedback': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional feedback...'}),
        }



class CourseCreateForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'image']


class LessonCreateForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['course', 'title', 'content', 'video_url']


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['course', 'title', 'description', 'due_date']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }


