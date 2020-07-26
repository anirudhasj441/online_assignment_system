from django.shortcuts import render,redirect
from home.models import Student
from assignment.models import Assignment,MCQ,FileUpload
from teacher.models import AssignmentsLog
from .models import MCQResult,AttempQuestion,File
from home.templatetags import extras
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date
from django.utils import timezone
# Create your views here.



def studIndex(request):
  if request.user.is_authenticated:
    if extras.has_group(request.user,'Student'):
      assignment = []
      student = Student.objects.get(user=request.user)
      ass = Assignment.objects.filter(ass_class=student.s_class).order_by("-date")
      for i in ass:
        if i.last_date>date.today():
          assignment.append(i)
        
      params = {
        'student':student,
        'assignments':assignment
      }
    else:
      return redirect('/')  
  else:
    return redirect('/')
  return render(request,'student/index.html',params)
  
def assignment(request,slug):
  if request.user.is_authenticated:
    if extras.has_group(request.user,'Student'):
      assignment = Assignment.objects.get(slug = slug)
      mcqs = MCQ.objects.filter(assignment=assignment)
      file_ass = FileUpload.objects.filter(assignment=assignment)
      params = {
        'assignment':assignment,
        'mcqs':mcqs,
        'file_ass':file_ass,
      }
    else:
      return redirect('/')
  else:
    return redirect('/')
  return render(request,'student/assignment.html',params)
  
def mcqResult(request,slug):
  if request.user.is_authenticated:
    if extras.has_group(request.user,'Student'):
      correct = 0
      attemp = 0
      assignment = Assignment.objects.get(slug=slug)
      mcq = MCQ.objects.filter(assignment=assignment)
      total_quetions = len(mcq)
      AttempQuestion.objects.all().delete()
      if request.method == 'POST':
        for i in mcq:
          ans = request.POST.get("ans"+str(i.pk))
          if ans != None:
            attemp += 1
            if str(ans).replace(" ","") == str(i.ans).replace(" ",""):
              correct += 1
            attemp_que = AttempQuestion.objects.create(
              student = request.user,
              mcq = i,
              s_ans = ans,
            )
          else:
            continue
        try:
          res = MCQResult.objects.get(student=request.user,assignment=assignment)
          res.attemp = attemp
          res.total_que = total_quetions
          res.correct = correct
          res.marks = correct
          res.save()
        except MCQResult.DoesNotExist:
          res = MCQResult.objects.create(
            assignment = assignment,
            student = request.user,
            total_que = total_quetions,
            attemp = attemp,
            correct = correct,
            marks = correct,
          )
      attemp_questions = AttempQuestion.objects.filter(student=request.user)
      
      
      params = {
        "assignment" : assignment,
        "attemp_questions" : attemp_questions,
        "res" : res,
      }  
      
      
      return render(request,"student/mcq_result.html",params)
    else:
      return redirect("/")
  else:
    return redirect("/")
  


def fileSubmit(request,slug):
  if request.user.is_authenticated:
    if extras.has_group(request.user,'Student'):
      assignment = Assignment.objects.get(slug=slug)
      questions = FileUpload.objects.filter(assignment = assignment)
      try:
        log = AssignmentsLog.objects.get(student=request.user,assignment=assignment)
        log.submit_on = timezone.now()
      except AssignmentsLog.DoesNotExist:
        log = AssignmentsLog.objects.create(
          student=request.user,
          assignment=assignment,
        )
      if request.method == "POST":
          for i in questions:
            try:
              file = request.FILES.get("file"+str(i.pk))
              if file is not None:
                file_upload = File.objects.get(
                  student=request.user,
                  assignment=assignment,
                  question=i.desc,
                )
                file_upload.file.delete(save=True)
                file_upload.file = file
                file_upload.save()
              else:
                continue
            except File.DoesNotExist:
              if file is not None:
                file_upload = File.objects.create(
                  student = request.user,
                  assignment=assignment,
                  question = i.desc,
                  file = file,
                )
              else:
                continue
      return redirect("/student/assignment/"+str(assignment.slug))
    else:
      return redirect("/")
  else:
    return redirect("/")
      
  

# signals (Triggers)
@receiver(post_save,sender=MCQResult)
def addLog(sender,instance,created,**kwargs):
  if created:
    log = AssignmentsLog.objects.create(
      assignment = instance.assignment,
      student = instance.student,
      result = instance,
    )
  else:
    try:
      log = AssignmentsLog.objects.get(assignment=instance.assignment,student=instance.student)
      log.submit_on = timezone.now()
      log.result = instance
      log.save()
    except AssignmentsLog.DoesNotExist:
      log = AssignmentsLog.objects.create(
      assignment = instance.assignment,
      student = instance.student,
      result = instance,
    )

      
    