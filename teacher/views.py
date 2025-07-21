# teacher/views.py - Updated views to handle teacher approval workflow

from django.shortcuts import render, redirect, reverse
from . import forms, models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from datetime import date, timedelta
from exam import models as QMODEL
from student import models as SMODEL
from exam import forms as QFORM
from django.contrib.auth import authenticate, login
from django.contrib import messages


def teacherclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'teacher/teacherclick.html')


def teacher_signup_view(request):
    userForm = forms.TeacherUserForm()
    teacherForm = forms.TeacherForm()
    mydict = {'userForm': userForm, 'teacherForm': teacherForm}
    
    if request.method == 'POST':
        userForm = forms.TeacherUserForm(request.POST)
        teacherForm = forms.TeacherForm(request.POST, request.FILES)
        
        if userForm.is_valid() and teacherForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            
            teacher = teacherForm.save(commit=False)
            teacher.user = user
            teacher.status = False  # Waiting for approval
            teacher.save()
            
            # Add to teacher group
            my_teacher_group = Group.objects.get_or_create(name='TEACHER')
            my_teacher_group[0].user_set.add(user)
            
            # Add success message
            messages.success(request, 
                'Registration successful! Your account is pending approval from an administrator. '
                'You will receive an email notification once your account is approved.')
            
            return HttpResponseRedirect('teacher-wait-for-approval')
    
    return render(request, 'teacher/teachersignup.html', context=mydict)


def teacher_wait_for_approval_view(request):
    """View shown to teachers waiting for approval"""
    return render(request, 'teacher/teacher_wait_for_approval.html')


def is_teacher(user):
    return user.groups.filter(name='TEACHER').exists()


def is_approved_teacher(user):
    """Check if user is an approved teacher"""
    if user.groups.filter(name='TEACHER').exists():
        try:
            teacher = models.Teacher.objects.get(user=user)
            return teacher.status  # True if approved, False if pending
        except models.Teacher.DoesNotExist:
            return False
    return False


@login_required(login_url='teacherlogin')
@user_passes_test(is_approved_teacher, login_url='teacher-wait-for-approval')
def teacher_dashboard_view(request):
    """Teacher dashboard - only accessible to approved teachers"""
    dict_context = {
        'total_course': QMODEL.Course.objects.all().count(),
        'total_question': QMODEL.Question.objects.all().count(),
        'total_student': SMODEL.Student.objects.all().count()
    }
    return render(request, 'teacher/teacher_dashboard.html', context=dict_context)


@login_required(login_url='teacherlogin')
@user_passes_test(is_approved_teacher, login_url='teacher-wait-for-approval')
def teacher_exam_view(request):
    return render(request, 'teacher/teacher_exam.html')


@login_required(login_url='teacherlogin')
@user_passes_test(is_approved_teacher, login_url='teacher-wait-for-approval')
def teacher_add_exam_view(request):
    courseForm = QFORM.CourseForm()
    if request.method == 'POST':
        courseForm = QFORM.CourseForm(request.POST)
        if courseForm.is_valid():        
            courseForm.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/teacher/teacher-view-exam')
    return render(request, 'teacher/teacher_add_exam.html', {'courseForm': courseForm})


@login_required(login_url='teacherlogin')
@user_passes_test(is_approved_teacher, login_url='teacher-wait-for-approval')
def teacher_view_exam_view(request):
    courses = QMODEL.Course.objects.all()
    return render(request, 'teacher/teacher_view_exam.html', {'courses': courses})


@login_required(login_url='teacherlogin')
@user_passes_test(is_approved_teacher, login_url='teacher-wait-for-approval')
def delete_exam_view(request, pk):
    course = QMODEL.Course.objects.get(id=pk)
    course.delete()
    return HttpResponseRedirect('/teacher/teacher-view-exam')


@login_required(login_url='teacherlogin')
@user_passes_test(is_approved_teacher, login_url='teacher-wait-for-approval')
def teacher_question_view(request):
    return render(request, 'teacher/teacher_question.html')


@login_required(login_url='teacherlogin')
@user_passes_test(is_approved_teacher, login_url='teacher-wait-for-approval')
def teacher_add_question_view(request):
    questionForm = QFORM.QuestionForm()
    if request.method == 'POST':
        questionForm = QFORM.QuestionForm(request.POST)
        if questionForm.is_valid():
            question = questionForm.save(commit=False)
            course = QMODEL.Course.objects.get(id=request.POST.get('courseID'))
            question.course = course
            question.save()       
        else:
            print("form is invalid")
        return HttpResponseRedirect('/teacher/teacher-view-question')
    return render(request, 'teacher/teacher_add_question.html', {'questionForm': questionForm})


@login_required(login_url='teacherlogin')
@user_passes_test(is_approved_teacher, login_url='teacher-wait-for-approval')
def teacher_view_question_view(request):
    courses = QMODEL.Course.objects.all()
    return render(request, 'teacher/teacher_view_question.html', {'courses': courses})


@login_required(login_url='teacherlogin')
@user_passes_test(is_approved_teacher, login_url='teacher-wait-for-approval')
def see_question_view(request, pk):
    questions = QMODEL.Question.objects.all().filter(course_id=pk)
    return render(request, 'teacher/see_question.html', {'questions': questions})


@login_required(login_url='teacherlogin')
@user_passes_test(is_approved_teacher, login_url='teacher-wait-for-approval')
def remove_question_view(request, pk):
    question = QMODEL.Question.objects.get(id=pk)
    question.delete()
    return HttpResponseRedirect('/teacher/teacher-view-question')