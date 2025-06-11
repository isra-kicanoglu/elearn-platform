from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect,HttpResponse
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import RegisterForm, GradeForm, RatingForm, DiscussionForm
from .models import Course, Lesson, Assignment, Submission, Grade, Discussion, CourseRating,Enrollment
from django.db.models import Avg
from django.contrib import messages
from django.db import models
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.utils.timezone import now
from django.core.paginator import Paginator






def course_list(request):
    course_queryset = Course.objects.all()
    paginator = Paginator(course_queryset, 6)  # 4 courses per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'course_list.html', {
        'courses': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'paginator': paginator,
    })  


@login_required
def course_detail(request, id):
    course = get_object_or_404(Course, id=id)
    lessons = Lesson.objects.filter(course=course)
    assignments = Assignment.objects.filter(course=course)
    submissions_count = Submission.objects.filter(student=request.user, assignment__in=assignments).count()


    from .forms import DiscussionForm, RatingForm
    from .models import Discussion, CourseRating, LessonProgress, Enrollment

    # Discussions
    discussions = Discussion.objects.filter(course=course).order_by('-posted_at')
    discussion_form = DiscussionForm()

    # Ratings
    existing_rating = CourseRating.objects.filter(user=request.user, course=course).first()
    rating_form = RatingForm(instance=existing_rating)
    all_ratings = CourseRating.objects.filter(course=course)
    avg_rating = all_ratings.aggregate(models.Avg('rating'))['rating__avg']

    # Lesson progress
    total_lessons = lessons.count()
    completed_lessons_qs = LessonProgress.objects.filter(student=request.user, lesson__in=lessons)
    completed_lessons = completed_lessons_qs.values_list('lesson_id', flat=True)
    completed_count = completed_lessons_qs.count()

    progress_percent = 0
    if total_lessons > 0:
        progress_percent = int((completed_count / total_lessons) * 100)

    # Enrollment status (for student)
    is_enrolled = False
    if request.user.role == 'student':
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()

    # Handle POST: Discussions or Ratings
    if request.method == 'POST':
        if 'message' in request.POST:
            discussion_form = DiscussionForm(request.POST)
            if discussion_form.is_valid():
                discussion = discussion_form.save(commit=False)
                discussion.user = request.user
                discussion.course = course
                discussion.save()
                messages.success(request, 'Comment posted!')
                return redirect(f'/course/{id}/')

        elif 'rating' in request.POST:
            rating_form = RatingForm(request.POST, instance=existing_rating)
            if rating_form.is_valid():
                rating = rating_form.save(commit=False)
                rating.user = request.user
                rating.course = course
                rating.save()
                messages.success(request, 'Rating submitted!')
                return redirect(f'/course/{id}/')

    return render(request, 'course_detail.html', {
        'course': course,
        'lessons': lessons,
        'assignments': assignments,
        'form': discussion_form,
        'discussions': discussions,
        'rating_form': rating_form,
        'existing_rating': existing_rating,
        'all_ratings': all_ratings,
        'avg_rating': avg_rating,
        'completed_lessons': completed_lessons,
        'completed_count': completed_count,
        'total_lessons': total_lessons,
        'progress_percent': progress_percent,
        'is_enrolled': is_enrolled,
        'submissions_count': submissions_count,

    })


@login_required
def lesson_detail(request, id):
    lesson = get_object_or_404(Lesson, id=id)
    return render(request, 'lesson_detail.html', {'lesson': lesson})


@login_required
def upload_assignment(request, id):
    assignment = get_object_or_404(Assignment, id=id)

    if request.method == 'POST':
        file = request.FILES.get('file')
        if file:
            Submission.objects.create(
                assignment=assignment,
                student=request.user,
                file_url=file,
                submitted_at=timezone.now()
            )
            return HttpResponseRedirect(f'/course/{assignment.course.id}/')

    return render(request, 'assignment_upload.html', {'assignment': assignment})


@login_required
def view_grades(request):
    submissions = Submission.objects.filter(student=request.user)
    grades = Grade.objects.filter(submission__in=submissions)

    return render(request, 'grades.html', {
        'grades': grades
    })


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome.")
            return redirect('/')
        else:
            # Optional: show custom error message if needed
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})



def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('/')


def is_instructor(user):
    return user.is_authenticated and user.role == 'instructor'


@user_passes_test(is_instructor)
def instructor_submissions(request):
    submissions = Submission.objects.filter(assignment__course__instructor=request.user)
    return render(request, 'instructor_submissions.html', {'submissions': submissions})


@user_passes_test(is_instructor)
def grade_submission(request, id):
    submission = get_object_or_404(Submission, id=id)

    if request.method == 'POST':
        form = GradeForm(request.POST)
        if form.is_valid():
            grade = form.save(commit=False)
            grade.submission = submission
            grade.save()
            return redirect('/grade-submissions/')
    else:
        form = GradeForm()

    return render(request, 'grade_submission.html', {
        'submission': submission,
        'form': form
    })


@user_passes_test(lambda u: u.is_authenticated and u.role == 'instructor')
def assignment_submissions(request, course_id, assignment_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    assignment = get_object_or_404(Assignment, id=assignment_id, course=course)
    submissions = Submission.objects.filter(assignment=assignment)

    return render(request, 'assignment_submissions.html', {
        'assignment': assignment,
        'submissions': submissions
    })


@login_required
def my_submissions(request):
    submissions = Submission.objects.filter(student=request.user)
    return render(request, 'my_submissions.html', {
        'submissions': submissions
    })
@user_passes_test(lambda u: u.is_authenticated and u.role == 'instructor' and u.is_approved)
def create_course(request):
    from .forms import CourseCreateForm

    if request.method == 'POST':
        form = CourseCreateForm(request.POST, request.FILES)  # ✅ add request.FILES to handle image upload
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            messages.success(request, 'Course created successfully!')
            return redirect('/')
    else:
        form = CourseCreateForm()

    return render(request, 'create_course.html', {'form': form})
@user_passes_test(lambda u: u.is_authenticated and u.role == 'instructor' and u.is_approved)
def add_lesson(request):
    from .forms import LessonCreateForm

    if request.method == 'POST':
        form = LessonCreateForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            if lesson.course.instructor != request.user:
                messages.success(request, 'Lesson created!')
                return redirect('/')  # ✅ prevent hacking other courses
            lesson.save()
            return redirect(f'/course/{lesson.course.id}/')
    else:
        form = LessonCreateForm()

        # Filter the course dropdown to only show instructor's own
        form.fields['course'].queryset = Course.objects.filter(instructor=request.user)

    return render(request, 'add_lesson.html', {'form': form})
@user_passes_test(lambda u: u.is_authenticated and u.role == 'instructor' and u.is_approved)
def edit_course(request, id):
    course = get_object_or_404(Course, id=id, instructor=request.user)
    from .forms import CourseCreateForm

    if request.method == 'POST':
        form = CourseCreateForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated!')
            return redirect('/')
    else:
        form = CourseCreateForm(instance=course)

    return render(request, 'edit_course.html', {'form': form, 'course': course})
@user_passes_test(lambda u: u.is_authenticated and u.role == 'instructor' and u.is_approved)
def edit_lesson(request, id):
    lesson = get_object_or_404(Lesson, id=id)
    
    # Ensure the logged-in instructor owns this course
    if lesson.course.instructor != request.user:
        messages.success(request, 'Lesson updated!')
        return redirect('/')

    from .forms import LessonCreateForm

    if request.method == 'POST':
        form = LessonCreateForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            return redirect(f'/course/{lesson.course.id}/')
    else:
        form = LessonCreateForm(instance=lesson)

    # Lock the course dropdown to just the current course
    form.fields['course'].queryset = Course.objects.filter(id=lesson.course.id)

    return render(request, 'edit_lesson.html', {'form': form, 'lesson': lesson})
@user_passes_test(lambda u: u.is_authenticated and u.role == 'instructor' and u.is_approved)
def delete_course(request, id):
    course = get_object_or_404(Course, id=id, instructor=request.user)
    course.delete()
    messages.success(request, 'Course deleted.')
    return redirect('/')

@user_passes_test(lambda u: u.is_authenticated and u.role == 'instructor' and u.is_approved)
def delete_lesson(request, id):
    lesson = get_object_or_404(Lesson, id=id)
    if lesson.course.instructor != request.user:
        messages.success(request, 'Lesson deleted!')

        return redirect('/')
    course_id = lesson.course.id
    lesson.delete()
    return redirect(f'/course/{course_id}/')
@user_passes_test(lambda u: u.is_authenticated and u.role == 'instructor' and u.is_approved)
def add_assignment(request):
    from .forms import AssignmentForm

    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            if assignment.course.instructor != request.user:
                return redirect('/')
            assignment.save()
            messages.success(request, 'Assignment created!')
            return redirect(f'/course/{assignment.course.id}/')
    else:
        form = AssignmentForm()
        form.fields['course'].queryset = Course.objects.filter(instructor=request.user)

    return render(request, 'add_assignment.html', {'form': form})
@user_passes_test(lambda u: u.is_authenticated and u.role == 'instructor' and u.is_approved)
def edit_assignment(request, id):
    assignment = get_object_or_404(Assignment, id=id)
    if assignment.course.instructor != request.user:
        return redirect('/')

    from .forms import AssignmentForm
    if request.method == 'POST':
        form = AssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assignment updated!')
            return redirect(f'/course/{assignment.course.id}/')
    else:
        form = AssignmentForm(instance=assignment)
        form.fields['course'].queryset = Course.objects.filter(id=assignment.course.id)

    return render(request, 'edit_assignment.html', {'form': form, 'assignment': assignment})
@user_passes_test(lambda u: u.is_authenticated and u.role == 'instructor' and u.is_approved)
def delete_assignment(request, id):
    assignment = get_object_or_404(Assignment, id=id)
    if assignment.course.instructor != request.user:
        return redirect('/')
    course_id = assignment.course.id
    assignment.delete()
    messages.success(request, 'Assignment deleted!')
    return redirect(f'/course/{course_id}/')
from .models import LessonProgress

@login_required
def complete_lesson(request, id):
    lesson = get_object_or_404(Lesson, id=id)

    # Prevent instructors from marking lessons
    if request.user.role != 'student':
        return redirect(f'/lesson/{id}/')

    # Only mark once
    LessonProgress.objects.get_or_create(
        student=request.user,
        lesson=lesson,
        defaults={'completed': True}
    )

    messages.success(request, 'Lesson marked as completed!')
    return redirect(f'/lesson/{id}/')
@user_passes_test(lambda u: u.is_authenticated and u.role == 'instructor' and u.is_approved)
def instructor_dashboard(request):
    from .models import Course, Lesson, Assignment, CourseRating

    courses = Course.objects.filter(instructor=request.user).distinct()
    course_data = []

    for course in courses:
        avg_rating = CourseRating.objects.filter(course=course).aggregate(Avg('rating'))['rating__avg']
        avg_rating = round(avg_rating, 1) if avg_rating else "No ratings"

        enrollments = Enrollment.objects.filter(course=course).select_related('student')
        student_count = enrollments.count()

        course_data.append({
            'course': course,
            'avg_rating': avg_rating,
            'student_count': student_count,
        })



    return render(request, 'instructor_dashboard.html', {'course_data': course_data})
@user_passes_test(lambda u: u.is_authenticated and u.role == 'student')
def student_dashboard(request):
    from .models import LessonProgress, CourseRating, Enrollment
    student = request.user
    courses = Course.objects.filter(enrollment__student=student)
    data = []

    for course in courses:
        lessons = Lesson.objects.filter(course=course)
        total = lessons.count()
        completed = LessonProgress.objects.filter(student=student, lesson__in=lessons).count()
        percent = int((completed / total) * 100) if total > 0 else 0
        data.append({
            'course': course,
            'progress': percent
        })

    return render(request, 'student_dashboard.html', {'data': data})
 

@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user.role != 'student':
        return redirect(f'/course/{course_id}/')

    Enrollment.objects.get_or_create(
        student=request.user,
        course=course
    )

    messages.success(request, 'Enrolled successfully!')
    return redirect(f'/course/{course_id}/')
@user_passes_test(lambda u: u.is_authenticated and u.role == 'instructor' and u.is_approved)
def course_students(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    enrollments = Enrollment.objects.filter(course=course).select_related('student')

    return render(request, 'course_students.html', {
        'course': course,
        'enrollments': enrollments
    })


@user_passes_test(lambda u: u.is_authenticated and u.role == 'student')
def generate_certificate(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if the student is enrolled
    enrolled = Enrollment.objects.filter(course=course, student=request.user).exists()
    if not enrolled:
        return HttpResponse("You're not enrolled in this course.", status=403)

    # Check if all lessons are completed
    lessons = Lesson.objects.filter(course=course)
    total_lessons = lessons.count()
    completed_lessons = LessonProgress.objects.filter(
        student=request.user, lesson__in=lessons).count()
    if completed_lessons < total_lessons:
        return HttpResponse("You must complete all lessons.", status=403)

    # Check if all assignments are submitted
    assignments = Assignment.objects.filter(course=course)
    submitted_count = Submission.objects.filter(
        student=request.user, assignment__in=assignments).count()
    if submitted_count < assignments.count():
        return HttpResponse("You must submit all assignments.", status=403)

    # Generate PDF
    # Generate PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate_{course.title}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Border
    p.setStrokeColorRGB(0, 0, 0)
    p.setLineWidth(4)
    p.rect(30, 30, width - 60, height - 60)

    # Header
    p.setFont("Helvetica-Bold", 30)
    p.drawCentredString(width / 2, height - 100, "CERTIFICATE OF COMPLETION")

    # Subheading
    p.setFont("Helvetica", 16)
    p.drawCentredString(width / 2, height - 140, "This is proudly presented to")

    # Student Name
    p.setFont("Helvetica-Bold", 22)
    p.drawCentredString(width / 2, height - 180, f"{request.user.first_name} {request.user.last_name}")

    # Completion line
    p.setFont("Helvetica", 16)
    p.drawCentredString(width / 2, height - 220, "for successfully completing the course")

    # Course Title
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width / 2, height - 250, f"“{course.title}”")

    # Date and Signature
    p.setFont("Helvetica", 12)
    p.drawString(70, 100, f"Date: {now().strftime('%B %d, %Y')}")
    p.drawRightString(width - 70, 100, "Platform Signature: _______________")

    # Footer
    p.setFont("Helvetica-Oblique", 10)
    p.drawCentredString(width / 2, 60, "This certificate is generated electronically by the platform.")

    p.showPage()
    p.save()


    return response

