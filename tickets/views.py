# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from tickets import printer
from tickets.models import Student, Ticket


# !view
def search_students(query, status):
    students = Student.objects.all()
    if status == '0':
        students = students.filter(ticket__isnull=True)
    elif status == '1':
        students = students.filter(ticket__isnull=False)
    for (i, q) in enumerate(query.split(' ')):
        if not q: continue
        students = students.filter(Q(first_name__istartswith=q) | Q(last_name__istartswith=q) | Q(username__istartswith=q) | Q(email__istartswith=q) | Q(ticket__number__istartswith=q))
    return students

@login_required
def student_list(request):
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    students = search_students(query, status)
    return render(request, 'tickets/student/list.html', {
        'students': students,
        'query': query,
        'status': status,
    })

@login_required
def student_export(request):
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    students = search_students(query, status)
    response = HttpResponse(printer.students_pdf(students), content_type='application/pdf')
    response['Content-Disposition'] = 'filename=%s' % 'Brucosi_Karte.pdf'
    return response

@login_required
def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    return render(request, 'tickets/student/detail.html', {
        'student': student,
    })

# !view
def send_confirmation_mail(student):
    subject = u'[Brucosijada FER-a 2013] Potvrda o kupljenoj karti'
    message = render_to_string('tickets/student/mail.html', {'student': student})
    recipients = [student.email]
    try:
        send_mail(subject, message, None, recipients)
        return True
    except Exception:
        return False

@login_required
def student_buy_ticket(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if student.ticket_or_none:
        raise PermissionDenied
    ticket = Ticket.objects.create(student=student)
    messages.add_message(request, messages.SUCCESS, u'Karta %s za brucoša %s je uspješno kupljena' % (ticket.number, student.full_name))
    return redirect('tickets:student_send_mail', student_id=student.id)

@login_required
def student_send_mail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if not student.ticket_or_none:
        raise PermissionDenied
    if send_confirmation_mail(student):
        messages.add_message(request, messages.INFO, u'Poslan je e-mail s potvrdom o kupljenoj karti na adresu %s' % student.email)
    else:
        messages.add_message(request, messages.ERROR, u'Trenutačno se ne može poslati e-mail s potvrdom o kupljenoj karti na adresu %s' % student.email)
    return redirect('tickets:student_list')
