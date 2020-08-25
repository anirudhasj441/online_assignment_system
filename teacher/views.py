from django.shortcuts import render,redirect
from assignment.models import Assignment,MCQ,FileUpload
from .models import AssignmentsLog,NotifiacationsForTeacher
from home.models import Class,Subject
from student.models import MCQResult,File,NotificationForStudent
from home.models import Student,Teacher
from django.contrib import messages
from home.templatetags import extras
from .templatetags import app_tags
from datetime import date,timedelta,datetime
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import sys
# Create your views here.
def teacherIndex(request):
  if request.user.is_authenticated:
    if extras.has_group(request.user,'Teacher'):
      assignment = []
      ass = Assignment.objects.filter(teacher = request.user).order_by("-date")
      for i in ass:
        # if i.last_date<date.today()+timedelta(days=5):
          assignment.append(i)
      params = {
        'assignments': assignment
      }
    else:
      return redirect('/')
  return render(request,'teacher/index.html',params)
  
def addAssignment(request):
  if request.user.is_authenticated:
    if extras.has_group(request.user,'Teacher'):
      if request.method=="POST":
        ass_class = request.POST['class']
        sub = request.POST['subject']
        due_date = request.POST['last_date']
        ass_type = request.POST['type']
        slug = ass_class+"-"+sub+"-"+ass_type+str(datetime.now())
        assignment_class = Class.objects.get(class_name=ass_class)
        subject = Subject.objects.get(subject_name=sub,class_name=assignment_class)
        assignment = Assignment.objects.create(
          teacher = request.user,
          ass_class = assignment_class,
          subject = subject,
          last_date = due_date,
          ass_type = ass_type,
          slug = slug
        )
        return redirect('/teacher/assignment/'+str(assignment.slug))
      classes = Class.objects.all()
      subjects = Subject.objects.all()
      params = {
        "classes" : classes,
        "subjects" : subjects, 
      }
    else:
      return redirect('/')
  return render(request,'teacher/add_assignment.html',params)
  
def assignment(request,slug):
  if request.user.is_authenticated:
    if extras.has_group(request.user,'Teacher'):
      assignment = Assignment.objects.get(slug=slug)
      mcqs = MCQ.objects.filter(assignment=assignment)
      file_ass = FileUpload.objects.filter(assignment=assignment)
      if assignment.ass_type == "MCQ":
        if request.method == "POST":
          que = request.POST['que']
          opt_a = request.POST['opt_a']
          opt_b = request.POST['opt_b']
          opt_c = request.POST['opt_c']
          opt_d = request.POST['opt_d']
          ans = request.POST['ans']
          mcq = MCQ.objects.create(
            assignment = assignment,
            que = que,
            opt1 = opt_a,
            opt2 = opt_b,
            opt3 = opt_c,
            opt4 = opt_d,
            ans = ans
          )
          return redirect('/teacher/assignment/'+str(assignment.slug))
      else:
        if request.method == "POST":
          que = request.POST['que']
          f_ass = FileUpload.objects.create(
            assignment = assignment,
            desc = que,
          )
      params = {
        'assignment':assignment,
        'mcqs':mcqs,
        'file_ass':file_ass,
      }
    else:
      return redirect('/')
  
  return render(request,'teacher/assignment.html',params)

def assignmentStatus(request,slug):
  if request.user.is_authenticated:
    if extras.has_group(request.user,'Teacher'):
      solved = []
      assignment = Assignment.objects.get(slug=slug)
      student = Student.objects.filter(s_class=assignment.ass_class)
      log = AssignmentsLog.objects.filter(assignment=assignment).order_by("-submit_on")
      solved_log = AssignmentsLog.objects.filter(assignment=assignment).values_list('student')
      unsolved = Student.objects.filter(s_class=assignment.ass_class).exclude(user__in=solved_log)
      file = File.objects.filter(assignment=assignment)
      count_student = len(student)
      solved_student = len(log)
      params = {
        'assignment':assignment,
        'log':log,
        'file':file,
        'range':len(file),
        'media':settings.MEDIA_URL,
        'count_student':count_student,
        'solved_student':solved_student,
        'unsolved':unsolved,
        'students':student,
      }
      return render(request,'teacher/assignment_status.html',params)
    else:
      return redirect('/')
  else:
    return redirect('/')
# API FOR TEACHER

def deleteAssignment(request,slug):
  if request.user.is_authenticated:
    if extras.has_group(request.user,'Teacher'):
        ass = Assignment.objects.get(slug=slug)
        ass.delete()
        return redirect('/teacher')
    else:
      return redirect('/')
  else:
    return redirect('/')

def deleteQuetion(request,id):
  if request.user.is_authenticated:
    if extras.has_group(request.user,'Teacher'):
        que = MCQ.objects.get(pk=id)
        ass = Assignment.objects.get(pk=que.assignment.pk)
        que.delete()
        return redirect('/teacher/assignment/'+ass.slug)
    else:
      return redirect('/')
  else:
    return redirect('/')

def deleteFileQuestion(request,id):
  if request.user.is_authenticated:
    if extras.has_group(request.user,'Teacher'):
      que = FileUpload.objects.get(pk=id)
      ass = Assignment.objects.get(pk=que.assignment.pk)
      que.delete()
      return redirect("/teacher/assignment/"+ass.slug)
    else:
      return redirect('/')
  else:
    return redirect('/')
# signals (Triggers)
@receiver(post_save,sender=Assignment)
def addNotification(sender,instance,created,**kwargs):
  if created:
    NotificationForStudent.objects.create(
      assignment = instance,
      notify_class = instance.ass_class,
    )

@receiver(post_save,sender=AssignmentsLog)
def addNotificationForTeacher(sender,instance,created,**kwargs):
  teacher = Teacher.objects.get(user=instance.assignment.teacher)
  if created:
    notification = NotifiacationsForTeacher.objects.create(
      assignment = instance.assignment,
      student = instance.student,
      teacher = teacher,
    )
  else:
    try:
      notification = NotifiacationsForTeacher.objects.get(assignment=instance.assignment,student=instance.student)
      notification.date_filled = timezone.now()
      notification.assignment = instance.assignment
      notification.student = instance.student
      notification.teacher = teacher
      notification.save()
    except NotifiacationsForTeacher.DoesNotExist:
      notification = NotifiacationsForTeacher.objects.create(
      assignment = instance.assignment,
      student = instance.student,
      teacher = teacher
    )