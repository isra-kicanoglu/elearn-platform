from django.urls import path
from . import views

urlpatterns = [
    # 🌐 Public & Auth
path('', views.course_list, name='course_list'),
path('register/', views.register_view, name='register'),
path('login/', views.login_view, name='login'),
path('logout/', views.logout_view, name='logout'),

# 📚 Course & Lesson
path('course/<int:id>/', views.course_detail, name='course_detail'),
path('lesson/<int:id>/', views.lesson_detail, name='lesson_detail'),
path('complete-lesson/<int:id>/', views.complete_lesson, name='complete_lesson'),

# 🎓 Student
path('grades/', views.view_grades, name='view_grades'),
path('assignment/<int:id>/upload/', views.upload_assignment, name='upload_assignment'),
path('my-submissions/', views.my_submissions, name='my_submissions'),
path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
path('enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),
path('certificate/<int:course_id>/', views.generate_certificate, name='generate_certificate'),

# 🧑‍🏫 Instructor
path('instructor-dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
path('create-course/', views.create_course, name='create_course'),
path('edit-course/<int:id>/', views.edit_course, name='edit_course'),
path('delete-course/<int:id>/', views.delete_course, name='delete_course'),
path('add-lesson/', views.add_lesson, name='add_lesson'),
path('edit-lesson/<int:id>/', views.edit_lesson, name='edit_lesson'),
path('delete-lesson/<int:id>/', views.delete_lesson, name='delete_lesson'),
path('add-assignment/', views.add_assignment, name='add_assignment'),
path('edit-assignment/<int:id>/', views.edit_assignment, name='edit_assignment'),
path('delete-assignment/<int:id>/', views.delete_assignment, name='delete_assignment'),
path('grade-submissions/', views.instructor_submissions, name='instructor_submissions'),
path('grade-submissions/<int:id>/', views.grade_submission, name='grade_submission'),
path('course/<int:course_id>/assignment/<int:assignment_id>/submissions/', views.assignment_submissions, name='assignment_submissions'),
path('course/<int:course_id>/students/', views.course_students, name='course_students'),


]
