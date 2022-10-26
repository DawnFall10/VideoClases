# -*- coding: UTF-8 -*-

import json
import os
from json.decoder import JSONDecodeError

from django.shortcuts import render, redirect
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes


from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.urls import reverse, reverse_lazy
from django.core.validators import URLValidator
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormView, UpdateView, CreateView
from pyexcel_ods import get_data as ods_get_data
from pyexcel_xls import get_data as xls_get_data
from pyexcel_xlsx import get_data as xlsx_get_data

from quality_control.models.quality_control import QualityControl
from videoclases.forms.authentication_form import CustomAutheticationForm
from videoclases.forms.forms import *
from videoclases.models.boolean_parameters import BooleanParameters
from videoclases.models.evaluation.criterion import Criterion
from videoclases.models.evaluation.criteria_by_teacher import CriteriaByTeacher
from videoclases.models.evaluation.scale import Scale
from videoclases.models.final_scores import FinalScores
from videoclases.models.groupofstudents import GroupOfStudents
from videoclases.models.pedagogical_questions.pedagogical_questions_answers import PedagogicalQuestionsAnswers
from videoclases.models.student import Student
from videoclases.models.student_evaluations import StudentEvaluations
from videoclases.models.student_responses import StudentResponses
from videoclases.models.video_clase import VideoClase

SHOW_CORRECT_ANSWER = 'Mostrar alternativa correcta'


def in_students_group(user):
    if user:
        return user.groups.filter(name='Alumnos').exists()
    return False


def in_teachers_group(user):
    if user:
        return user.groups.filter(name='Profesores').exists()
    return False

def in_organizer_group(user):
    if user:
        return user.groups.filter(name='Organizadores').exists()
    return False


def password_reset_request(request):
	if request.method == "POST":
		password_reset_form = PasswordResetForm(request.POST)
		if password_reset_form.is_valid():
			data = password_reset_form.cleaned_data['email']
			associated_users = User.objects.filter(Q(email=data))
			if associated_users.exists():
				for user in associated_users:
					subject = "Password Reset Requested"
					email_template_name = "password_reset_email.txt"
					c = {
					"email":user.email,
					'domain':'127.0.0.1:8000',
					'site_name': 'Website',
					"uid": urlsafe_base64_encode(force_bytes(user.pk)),
					"user": user,
					'token': default_token_generator.make_token(user),
					'protocol': 'http',
					}
					email = render_to_string(email_template_name, c)
					try:
						send_mail(subject, email, settings.EMAIL_HOST_USER , [user.email], fail_silently=False)
					except BadHeaderError:
						return HttpResponse('Invalid header found.')
					return redirect ("password_reset/done/")
	password_reset_form = PasswordResetForm()
	return render(request=request, template_name="password_reset.html", context={"password_reset_form":password_reset_form})

class StudentView(TemplateView):
    template_name = 'student.html'

    def get_context_data(self, **kwargs):
        context = super(StudentView, self).get_context_data(**kwargs)
        student = self.request.user.student
        groups = GroupOfStudents.objects.filter(students=student)
        for group in groups:
            group.nota_final = FinalScores.objects.get(student=student, group=group).ponderar_notas()
            homework_base =group.homework
            homework =homework_base
            if homework.homework_to_evaluate is not None:
                homework = homework.homework_to_evaluate
            group.videoclases_evaluadas = StudentResponses.objects.filter(
                Q(videoclase__homework=homework) | Q(videoclase__homework=homework_base),
                student=student).count()
            control = QualityControl.objects.filter(homework=homework)
            control = control[0] if control.exists() else None
            if control:
                group.videoclases_evaluadas += control.list_items.filter(
                    videoclase__answers__student=student).count()

            try:
                group.pq_answer = PedagogicalQuestionsAnswers.objects.get(
                    student=student,test=group.homework.pedagogicalquestions,
                    state=group.homework.pedagogicalquestions.get_state())
            except:
                group.pq_answer = None

        context['groups'] = groups
        return context

    @method_decorator(user_passes_test(in_students_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(StudentView, self).dispatch(*args, **kwargs)


class AssignGroupFormView(FormView):
    template_name = 'blank.html'
    form_class = AssignGroupForm

    @method_decorator(user_passes_test(in_teachers_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(AssignGroupFormView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        groups = json.loads(form.cleaned_data['groups'])
        homework = Homework.objects.get(id=form.cleaned_data['homework'])
        for number in groups:
            group, created = GroupOfStudents.objects.get_or_create(homework=homework, number=int(number))
            for student_id in groups[number]:
                group.students.add(Student.objects.get(id=student_id))
            if created:
                for a in group.students.all():
                    FinalScores.objects.get_or_create(group=group, student=a)
                VideoClase.objects.get_or_create(group=group)
        result_dict = {}
        result_dict['success'] = True
        return JsonResponse(result_dict)

    def form_invalid(self, form):
        return super(AssignGroupFormView, self).form_invalid(form)

    def get(self, request, *args, **kwargs):
        return super(AssignGroupFormView, self).get(request, *args, **kwargs)


class DeleteStudentView(TemplateView):
    template_name = 'blank.html'

    @method_decorator(user_passes_test(in_teachers_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(DeleteStudentView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        student = Student.objects.get(id=self.kwargs['student_id'])
        course = Course.objects.get(id=self.kwargs['course_id'])
        if student not in course.students.all():
            messages.info(self.request, 'El alumno no corresponde a este curso.')
            return HttpResponseRedirect(reverse('teacher'))
        if course not in self.request.user.teacher.courses.all():
            messages.info(self.request, 'No tienes permisos para esta acción')
            return HttpResponseRedirect(reverse('teacher'))
        course.students.remove(student)
        messages.info(self.request, 'El alumno fue borrado del course exitosamente.')
        return HttpResponseRedirect(reverse('edit_course', kwargs={'course_id': course.id}))

    def get_success_url(self, *args, **kwargs):
        return reverse('edit_course', kwargs={'course_id': self.kwargs['course_id']})


class DeleteCourseFormView(FormView):
    template_name = 'blank.html'
    form_class = DeleteCourseForm
    success_url = reverse_lazy('teacher')

    @method_decorator(user_passes_test(in_teachers_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(DeleteCourseFormView, self).dispatch(*args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
        course = get_object_or_404(Course, pk=self.kwargs['course_id'])
        if course not in self.request.user.teacher.courses.all():
            messages.info(self.request, 'No tienes permisos para esta acción')
            return HttpResponseRedirect(reverse('teacher'))
        course.delete()
        messages.info(self.request, 'El curso se ha eliminado exitosamente')
        return super(DeleteCourseFormView, self).form_valid(form, *args, **kwargs)


class DeleteHomeworkFormView(FormView):
    template_name = 'blank.html'
    form_class = DeleteHomeworkForm
    success_url = reverse_lazy('teacher')

    @method_decorator(user_passes_test(in_teachers_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(DeleteHomeworkFormView, self).dispatch(*args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
        homework = Homework.objects.get(id=form.cleaned_data['homework'])
        homework.delete()
        messages.info(self.request, 'La tarea se ha eliminado exitosamente')
        return super(DeleteHomeworkFormView, self).form_valid(form, *args, **kwargs)


class ChangePasswordView(FormView):
    template_name = 'change-password.html'
    form_class = ChangePasswordForm

    def form_valid(self, form, *args, **kwargs):
        user = self.request.user
        if user.check_password(form.cleaned_data['old_password']):
            form.save()
            user = authenticate(username=self.request.user.username,
                                password=form.cleaned_data['new_password1'])
            login(self.request, user)
            messages.info(self.request, 'Tu contraseña fue cambiada exitosamente')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return HttpResponseRedirect(reverse('change_password'))

    def form_invalid(self, form, *args, **kwargs):
        return super(ChangePasswordView, self).form_invalid(form, *args, **kwargs)

    def get_success_url(self):
        user = self.request.user
        if user.groups.filter(name='Profesores').exists():
            user.teacher.changed_password = True
            user.teacher.save()
            return reverse('teacher')
        elif user.groups.filter(name='Alumnos').exists():
            user.student.changed_password = True
            user.student.save()
            return reverse('student')

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.request.user, **self.get_form_kwargs())

    def get_initial(self):
        if in_students_group(self.request.user):
            return {'email': self.request.user.email}

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return super(ChangePasswordView, self).get(self, request, *args, **kwargs)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        return super(ChangePasswordView, self).post(self, request, *args, **kwargs)


class ChangeStudentPasswordView(FormView):
    template_name = 'change-password-student.html'
    form_class = ChangeStudentPasswordForm

    @method_decorator(user_passes_test(in_teachers_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(ChangeStudentPasswordView, self).dispatch(*args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
        form.save()
        messages.info(self.request, 'Clave cambiada exitosamente.')
        return super(ChangeStudentPasswordView, self).form_valid(form, *args, **kwargs)

    def form_invalid(self, form, *args, **kwargs):
        return super(ChangeStudentPasswordView, self).form_invalid(form, *args, **kwargs)

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        form = form_class(**self.get_form_kwargs())
        course = Course.objects.get(id=self.kwargs['course_id'])
        form.fields['student'].queryset = course.students.all()
        form.fields['student'].label = 'Alumno'
        return form

    def get_success_url(self):
        return reverse('teacher')


class ChangeStudentPasswordSelectCourseView(FormView):
    template_name = 'change-password-student-select-course.html'
    form_class = ChangeStudentPasswordSelectCursoForm

    @method_decorator(user_passes_test(in_teachers_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(ChangeStudentPasswordSelectCourseView, self).dispatch(*args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
        self.kwargs['form'] = form
        return super(ChangeStudentPasswordSelectCourseView, self).form_valid(form, *args, **kwargs)

    def form_invalid(self, form, *args, **kwargs):
        return super(ChangeStudentPasswordSelectCourseView, self).form_invalid(form, *args, **kwargs)

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        form = form_class(**self.get_form_kwargs())
        form.fields['course'].queryset = self.request.user.teacher.courses.all()
        form.fields['course'].label = 'Curso'
        return form

    def get_success_url(self):
        course = self.kwargs['form'].cleaned_data['course']
        return reverse('change_student_password', kwargs={'course_id': course.id})


class NewCourseFormView(FormView):
    template_name = 'new-course.html'
    form_class = NewCourseUploadFileForm
    success_url = reverse_lazy('teacher')

    @method_decorator(user_passes_test(in_teachers_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(NewCourseFormView, self).dispatch(*args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
        # (self, file, field_name, name, content_type, size, charset, content_type_extra=None)
        f = form.cleaned_data['file']
        f.name = f.name.encode('ascii', 'ignore').decode('ascii')
        path = settings.STATIC_ROOT + '/test/' + f.name

        def save_file(f, path):
            with open(path, 'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)

        # Check file extension
        if f.name.endswith('.xlsx'):
            save_file(f, path)
            data = xlsx_get_data(path)
        elif f.name.endswith('.xls'):
            save_file(f, path)
            data = xls_get_data(path)
        elif f.name.endswith('.ods'):
            save_file(f, path)
            data = ods_get_data(path)
        else:
            messages.info(self.request, 'El archivo debe ser formato XLS, XLSX u ODS.')
            return HttpResponseRedirect(reverse('new_course'))
        # assumes first sheet has info
        key, sheet = data.popitem()
        for i in range(1, len(sheet)):
            student_array = sheet[i]
            if len(student_array) == 0:
                continue
            complete = False
            if len(student_array) > 3:
                complete = True
                complete &= student_array[0] not in [None, '']
                complete &= student_array[1] not in [None, '']
                complete &= student_array[2] not in [None, '']
                complete &= student_array[3] not in [None, '']
            if not complete:
                try:
                    os.remove(path)
                except Exception:
                    print("Not possible delete path")
                messages.info(self.request, 'El archivo no tiene toda la información de un alumno.')
                return HttpResponseRedirect(reverse('new_course'))
        # Create Course
        course, created = Course.objects.get_or_create(school=self.request.user.teacher.school,
                                                       name=form.cleaned_data['name'], year=form.cleaned_data['year'])
        self.request.user.teacher.courses.add(course)
        self.request.user.teacher.save()
        if created:
            # Create users and students
            for i in range(1, len(sheet)):
                student_array = sheet[i]
                if len(student_array) == 0:
                    continue
                apellidos = str(student_array[0])
                name = str(student_array[1])
                username = str(student_array[2])
                password = str(student_array[3])
                if apellidos and name and username and password:
                    try:
                        user = User.objects.get(username=username)
                        user.student.courses.add(course)
                        user.student.save()
                    except:
                        user = User.objects.create_user(username=username, password=password,
                                                        first_name=name, last_name=apellidos)
                        user.groups.add(Group.objects.get(name='Alumnos'))
                        a = Student.objects.create(user=user)
                        a.courses.add(course)
                        a.save()
        else:
            os.remove(path)
            messages.info(self.request, 'Ya existe un curso con ese nombre en este año.')
            return HttpResponseRedirect(reverse('new_course'))
        os.remove(path)
        messages.info(self.request, 'El curso se ha creado exitosamente')
        return HttpResponseRedirect(reverse('teacher'))


class NewHomeworkView(TemplateView):
    template_name = 'new-homework.html'

    def get_context_data(self, **kwargs):
        context = super(NewHomeworkView, self).get_context_data(**kwargs)
        form = NewHomeworkForm()
        context['new_homework_form'] = form
        teacher = self.request.user.teacher
        context['courses'] = teacher.courses.filter(year=timezone.now().year)
        context['type_scales'] = Scale.objects.all()
        context['homeworks'] = Homework.objects.filter(course__in=context['courses'])
        return context

    @method_decorator(user_passes_test(in_teachers_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(NewHomeworkView, self).dispatch(*args, **kwargs)


class NewHomeworkFormView(FormView):
    template_name = 'blank.html'
    form_class = NewHomeworkForm
    success_url = reverse_lazy('teacher')

    @method_decorator(user_passes_test(in_teachers_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(NewHomeworkFormView, self).dispatch(*args, **kwargs)

    def form_invalid(self, form):
        result_dict = {}
        result_dict['success'] = False
        result_dict['id'] = -1
        form_errors = []
        for field, errors in form.errors.items():
            print(errors)
            for error in errors:
                form_errors.append(error)
        result_dict['errors'] = form_errors
        return JsonResponse(result_dict)

    def form_valid(self, form):
        result_dict = {}
        scala = self.request.POST.get("scala", None)
        teacher = self.request.user.teacher
        homework = form.save(commit=False)
        homework.teacher = teacher
        homework.save()
        if scala:
            try:
                scala = json.loads(scala)
                model = CriteriaByTeacher.objects.create(teacher=teacher, name=homework.full_name())
                model.save()
                for c in scala.get('criteria'):
                    print(c)
                    model.criteria.create(value=c.get("name"), description=c.get('description', ""))
                homework.scala = Scale.objects.get(id=scala.get("scala"))
                homework.criteria.add(model)
                homework.save()
            except JSONDecodeError as e:
                pass

        result_dict['success'] = True
        result_dict['id'] = homework.id
        result_dict['errors'] = []
        return JsonResponse(result_dict)


class CourseView(TemplateView):
    template_name = 'course.html'

    def get_context_data(self, **kwargs):
        context = super(CourseView, self).get_context_data(**kwargs)
        course = Course.objects.get(id=kwargs['course_id'])
        students = course.students.all()
        students_array = []
        for student in students:
            student_dict = {}
            student_dict['id'] = student.id
            student_dict['last_name'] = student.user.last_name
            student_dict['first_name'] = student.user.first_name
            student_dict['username'] = student.user.username
            student_dict['homeworks_entregadas'] = student.groupofstudents_set.exclude(videoclase__video__isnull=True) \
                .exclude(videoclase__video__exact='').count()
            student_dict['pending_homeworks'] = student.groupofstudents_set \
                .filter(Q(videoclase__video='') | Q(videoclase__video__isnull=True)).count()
            student_dict['videoclases_answered'] = StudentEvaluations.objects \
                .filter(author=student) \
                .filter(videoclase__group__homework__course=course).count()
            students_array.append(student_dict)
        context['students'] = students_array
        context['course'] = course
        return context

    @method_decorator(user_passes_test(in_teachers_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(CourseView, self).dispatch(*args, **kwargs)


@user_passes_test(in_teachers_group, login_url='/')
def download_course(request, course_id):
    result_dict = {}
    course = Course.objects.get(id=course_id)
    students = course.students.all()
    course_dict = {}
    course_dict['id'] = course.id
    course_dict['name'] = course.name
    students_array = []
    for a in students:
        student_dict = {}
        student_dict['id'] = a.id
        student_dict['last_name'] = a.user.last_name
        student_dict['first_name'] = a.user.first_name
        students_array.append(student_dict)
    result_dict['students'] = students_array
    result_dict['course'] = course_dict
    return JsonResponse(result_dict)


@user_passes_test(in_teachers_group, login_url='/')
def download_homework_groups(request, homework_id):
    result_dict = {}
    homework = get_object_or_404(Homework, pk=homework_id)
    course_dict = {}
    course_dict['id'] = homework.course.id
    course_dict['name'] = homework.course.name
    students_array = []
    for g in homework.groups.all():
        for a in g.students.all():
            student_dict = {}
            student_dict['id'] = a.id
            student_dict['last_name'] = a.user.last_name
            student_dict['first_name'] = a.user.first_name
            student_dict['group'] = g.number
            student_dict['videoclase'] = g.videoclase.video not in [None, '']
            students_array.append(student_dict)
    result_dict['students'] = students_array
    result_dict['course'] = course_dict
    return JsonResponse(result_dict)


class EditStudentFormView(FormView):
    template_name = 'edit-student.html'
    form_class = EditStudentForm

    @method_decorator(user_passes_test(in_teachers_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(EditStudentFormView, self).dispatch(*args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
        student = Student.objects.get(id=self.kwargs['student_id'])
        student.user.first_name = form.cleaned_data['first_name']
        student.user.last_name = form.cleaned_data['last_name']
        student.user.save()
        messages.info(self.request, 'El alumno ha sido editado exitosamente.')
        return super(EditStudentFormView, self).form_valid(form, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        student = Student.objects.get(id=self.kwargs['student_id'])
        course = Course.objects.get(id=self.kwargs['course_id'])
        if student not in course.students.all():
            raise Http404
        return super(EditStudentFormView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EditStudentFormView, self).get_context_data(**kwargs)
        student = Student.objects.get(id=self.kwargs['student_id'])
        context['student'] = student
        context['course_id'] = self.kwargs['course_id']
        return context

    def get_initial(self):
        student = Student.objects.get(id=self.kwargs['student_id'])
        return {'first_name': student.user.first_name if student.user.first_name is not None else '',
                'last_name': student.user.last_name if student.user.last_name is not None else ''}

    def get_success_url(self, *args, **kwargs):
        return reverse('edit_course', kwargs={'course_id': self.kwargs['course_id']})


class EditCourseView(TemplateView):
    template_name = 'edit-course.html'

    @method_decorator(user_passes_test(in_teachers_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(EditCourseView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EditCourseView, self).get_context_data(**kwargs)
        course = Course.objects.get(id=kwargs['course_id'])
        context['course'] = course
        return context


class EditGroupFormView(FormView):
    template_name = 'blank.html'
    form_class = AssignGroupForm

    @method_decorator(user_passes_test(in_teachers_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(EditGroupFormView, self).dispatch(*args, **kwargs)

    def all_students_have_group(self, groups, original_groups):
        original_groups_students_count = 0
        groups_students_count = 0
        for g in original_groups:
            original_groups_students_count += g.students.all().count()
        for number in groups:
            for student_id in groups[number]:
                groups_students_count += 1
        return original_groups_students_count == groups_students_count

    def can_delete_group(self, group, homework):
        can_delete = True
        for a in group.students.all():
            nf = FinalScores.objects.get(group__homework=homework, student=a)
            if nf.group == group:
                return False, 'raise'
        return True, None

    def can_edit_group(self, group, list_submitted_students, list_contains_at_least_one_original):
        # if database group is the same than submitted group nothing happens
        if list(group.students.all()) == list_submitted_students:
            return False, None
        elif group.videoclase.video:
            # if database group has videoclase uploaded the group has to maintain
            # at least one original member
            if not list_contains_at_least_one_original:
                return False, 'raise'
            # if there is at least one original member, edit group
            else:
                return True, None
        # if there is no uploaded videoclase, all members can be changed
        else:
            return True, None

    def groups_numbers_correct(self, groups_json):
        numbers = list(range(1, len(groups_json) + 1))
        for number in groups_json:
            number_int = int(number)
            try:
                numbers.remove(number_int)
            except:
                pass
        return numbers == []

    @method_decorator(transaction.atomic)
    def form_valid(self, form):
        message = ''
        try:
            groups = json.loads(form.cleaned_data['groups'])
            if not self.groups_numbers_correct(groups):
                message = u'Los números de los groups no son consecutivos. Revisa si hay algún error.'
                raise ValueError
            homework = Homework.objects.get(id=form.cleaned_data['homework'])
            original_groups = GroupOfStudents.objects.filter(homework=homework)
            # check if all students from the original groups have a group in submitted data
            if not self.all_students_have_group(groups, original_groups):
                message = 'Datos incompletos, todos los alumnos deben tener grupo.'
                raise ValueError
            # check groups from submitted info
            for number in groups:
                group_qs = GroupOfStudents.objects.filter(homework=homework, number=int(number))
                # check if group exists in database
                if group_qs.exists():
                    group = group_qs[0]
                    list_contains_at_least_one_original = False
                    # create list of students from submitted info
                    list_submitted_students = []
                    for student_id in groups[number]:
                        list_submitted_students.append(Student.objects.get(id=student_id))
                        if group.students.filter(id=student_id).exists():
                            list_contains_at_least_one_original = True
                    # check if can edit group
                    can_edit, exception = self.can_edit_group(group, list_submitted_students,
                                                              list_contains_at_least_one_original)
                    if exception == 'raise':
                        message = 'No se pueden cambiar todos los alumnos de un group ' + \
                                  'que ya ha enviado videoclase: group número ' + str(group.number)
                        raise ValueError
                    elif can_edit:
                        group.students.clear()
                        for a in list_submitted_students:
                            group.students.add(a)
                            try:
                                nf = FinalScores.objects.get(group__homework=homework, student=a)
                            except Exception:
                                nf = FinalScores(student=a)
                            nf.group = group
                            nf.save()
                # if group does not exist, create group and add students
                else:
                    group = GroupOfStudents.objects.create(homework=homework, number=int(number))
                    # create list of students from submitted info
                    list_submitted_students = []
                    for student_id in groups[number]:
                        list_submitted_students.append(Student.objects.get(id=student_id))
                    for a in list_submitted_students:
                        group.students.add(a)
                    group.save()
                    for a in group.students.all():
                        nf = FinalScores.objects.get(group__homework=homework, student=a)
                        nf.group = group
                        nf.save()
                    VideoClase.objects.get_or_create(group=group)
            # check if there are groups that were not in the uploaded info
            # first, create a list of groups ids submitted
            list_submitted_group_ids = []
            for number in groups:
                list_submitted_group_ids.append(int(number))
            # get group queryset for other groups
            groups_not_submitted = GroupOfStudents.objects.filter(homework=homework) \
                .exclude(number__in=list_submitted_group_ids)
            for g in groups_not_submitted:
                can_delete, exception = self.can_delete_group(g, homework)
                if exception == 'raise':
                    message = 'No se puede eliminar el group ' + str(g.number) + '.'
                    raise ValueError
                else:
                    g.delete()
            result_dict = {}
            result_dict['success'] = True
            return JsonResponse(result_dict)
        except ValueError:
            result_dict = {}
            result_dict['success'] = False
            result_dict['message'] = str(message)
            return JsonResponse(result_dict)

    def form_invalid(self, form):
        print(form.errors)
        return super(EditGroupFormView, self).form_invalid(form)


class EditHomeworkView(UpdateView):
    template_name = 'edit-homework.html'
    form_class = EditHomeworkForm
    success_url = reverse_lazy('teacher')
    model = Homework

    @method_decorator(user_passes_test(in_teachers_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(EditHomeworkView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EditHomeworkView, self).get_context_data(**kwargs)
        homework = Homework.objects.get(id=self.kwargs['homework_id'])
        context['courses'] = self.request.user.teacher.courses.filter(year=timezone.now().year)
        context['homework'] = homework
        context['types_scales'] = Scale.objects.all()
        context['homeworks'] = Homework.objects.filter(course__in=context['courses']).exclude(id=homework.id)
        context['videoclases_recibidas'] = GroupOfStudents.objects.filter(homework=homework) \
            .exclude(videoclase__video__isnull=True) \
            .exclude(videoclase__video__exact='').count()
        return context

    def form_valid(self, form):
        self.object = self.get_object()
        self.object = form.save()

        criteria = self.request.POST.get('criteria', None)
        teacher = self.request.user.teacher
        if criteria:
            try:
                criteria = json.loads(criteria)
                groups_criteria = self.object.criteria.filter(teacher=teacher)
                if len(criteria) >0:
                    if groups_criteria.count() == 0:
                        model = CriteriaByTeacher.objects.create(teacher=teacher, name=self.object.full_name())
                        model.save()
                        filtered_criteria = [item for item in criteria if item.get('editable',None) and not item.get('id', None)]
                        for c in filtered_criteria:
                            model.criteria.create(value=c.get("name"), description=c.get('description', ""))
                        self.object.criteria.add(model)
                    else:
                        group = groups_criteria[0]
                        for c in criteria:
                            id = c.get('id', None)
                            editable = c.get('editable', False)
                            if id and editable:
                                original = group.criteria.filter(id=id)[0]
                                if c.get('deleted', False):
                                    original.delete()
                                else:
                                    original.value = c.get('name')
                                    original.description = c.get('description',"")
                                    original.save()
                            elif not id and editable:
                                group.criteria.create(value=c.get("name"), description=c.get('description', ""))

            except JSONDecodeError:
                pass
        result_dict = dict()
        result_dict['id'] = self.object.id
        return JsonResponse(result_dict)

    def get_object(self):
        obj = get_object_or_404(self.model, pk=self.kwargs['homework_id'])
        return obj


class SendVideoclaseView(UpdateView):
    template_name = 'send-videoclase.html'
    form_class = SendVideoclaseForm
    model = VideoClase
    success_url = reverse_lazy('student')

    @method_decorator(user_passes_test(in_students_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        obj = self.get_object(self, *args, **kwargs)
        if obj.group.homework.get_estado() == 3:
            messages.info(self.request, 'El plazo para enviar la homework ya ha terminado.')
            return HttpResponseRedirect(reverse('student'))
        return super(SendVideoclaseView, self).dispatch(*args, **kwargs)

    def form_invalid(self, form):
        return super(SendVideoclaseView, self).form_invalid(form)

    def form_valid(self, form):
        # check if video is a link
        validate = URLValidator()
        try:
            validate(form.cleaned_data['video'])
        except:
            messages.info(self.request, 'La VideoClase no corresponde a un link.')
            return HttpResponseRedirect(reverse('send_videoclase',
                                                kwargs={'homework_id': self.kwargs['homework_id']}))
        self.object.video = form.cleaned_data['video']
        self.object.question = form.cleaned_data['question']
        self.object.correct_alternative = form.cleaned_data['correct_alternative']
        self.object.alternative_2 = form.cleaned_data['alternative_2']
        self.object.alternative_3 = form.cleaned_data['alternative_3']
        self.object.upload_students = timezone.now()
        self.object.save()
        messages.info(self.request, 'La VideoClase se ha enviado correctamente.')
        return super(SendVideoclaseView, self).form_valid(form)

    def get_object(self, *args, **kwargs):
        homework = get_object_or_404(Homework, pk=self.kwargs['homework_id'])
        group = get_object_or_404(GroupOfStudents, students=self.request.user.student, homework=homework)
        return group.videoclase

    def get_context_data(self, *args, **kwargs):
        context = super(SendVideoclaseView, self).get_context_data(**kwargs)
        context['videoclase'] = self.object
        return context

    def get_initial(self):
        return {'video': self.object.video if self.object.video is not None else '',
                'question': self.object.question if self.object.question is not None else '',
                'correct_alternative': self.object.correct_alternative if self.object.correct_alternative is not None else '',
                'alternative_2': self.object.alternative_2 if self.object.alternative_2 is not None else '',
                'alternative_3': self.object.alternative_3 if self.object.alternative_3 is not None else ''}


class StudentEvaluationsFormView(CreateView):
    template_name = 'blank.html'
    form_class = StudentEvaluationsForm
    success_url = reverse_lazy('teacher')
    model = StudentEvaluations

    @method_decorator(user_passes_test(in_students_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(StudentEvaluationsFormView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        student = self.request.user.student

        evaluation, created = StudentEvaluations.objects.get_or_create(
            author=student, videoclase=form.cleaned_data['videoclase']
        )
        self.object = StudentEvaluationsForm(self.request.POST, instance=evaluation)
        # self.object.author = self.request.user.student
        self.object.save()

        criteria = self.request.POST.get('criteria', None)
        if criteria:
            try:
                criteria = json.loads(criteria)
                for c in criteria:
                    evaluation.criteria.create(value=c['value'], criterion=Criterion.objects.get(id=c['criterion']))

            except JSONDecodeError:
                pass
        result_dict = dict()
        result_dict['value'] = form.cleaned_data['value']
        return JsonResponse(result_dict)


class StudentResponsesView(FormView):
    template_name = 'review.html'
    form_class = StudentResponsesForm

    @method_decorator(user_passes_test(in_students_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        homework_base = get_object_or_404(Homework, pk=self.kwargs['homework_id'])
        homework = homework_base
        if homework_base.homework_to_evaluate is not None:
            homework = homework_base.homework_to_evaluate

        get_object_or_404(GroupOfStudents, students=self.request.user.student, homework=homework)
        if homework.get_estado() != 2:
            messages.info(self.request, u'Esta tarea no está en período de evaluación.')
            return HttpResponseRedirect(reverse('student'))
        return super(StudentResponsesView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(StudentResponsesView, self).get_context_data(**kwargs)
        context['homework_id'] = self.kwargs['homework_id']
        context['homework'] = get_object_or_404(Homework, pk=self.kwargs['homework_id'])
        homework_base = context['homework']
        homework = homework_base
        if homework_base.homework_to_evaluate is not None:
            homework = homework_base.homework_to_evaluate
        number_evaluations = \
            StudentEvaluations.objects.filter(
                Q(author=self.request.user.student),
                Q(videoclase__homework=homework) | Q(videoclase__homework=homework_base)).count()
        control = QualityControl.objects.filter(homework=homework)
        control = control[0] if control.exists() else None

        if control:
            number_evaluations += control.list_items.filter(videoclase__answers__student=self.request.user.student).count()

        context['number_evaluations'] = number_evaluations
        context['score'] = StudentEvaluations.scores
        return context

    def get(self, request, *args, **kwargs):
        homework = get_object_or_404(Homework, pk=self.kwargs['homework_id'])
        group = get_object_or_404(GroupOfStudents, students=self.request.user.student, homework=homework)
        return super(StudentResponsesView, self).get(self, request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return reverse('review_videoclase', kwargs={'homework_id': self.kwargs['homework_id']})


class StudentResponsesFormView(FormView):
    template_name = 'blank.html'
    form_class = StudentResponsesForm

    @method_decorator(user_passes_test(in_students_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(StudentResponsesFormView, self).dispatch(*args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
        student = self.request.user.student
        videoclase = form.cleaned_data['videoclase']
        answer = form.cleaned_data['answer']
        result_dict = {}
        result_dict['success'] = True
        show_correct_answer = BooleanParameters.objects.get(description=SHOW_CORRECT_ANSWER).value
        result_dict['show_correct_answer'] = show_correct_answer
        try:
            instancia = StudentResponses.objects.get(student=student,
                                                     videoclase=videoclase)
            instancia.answer = answer
            instancia.save()
            if show_correct_answer:
                result_dict['correct_answer'] = videoclase.correct_alternative
                result_dict['is_correct'] = instancia.is_correct()
        except:
            StudentResponses.objects.create(student=student,
                                            videoclase=videoclase, answer=answer).save()
            instancia = StudentResponses.objects.get(student=student,
                                                     videoclase=videoclase, answer=answer)
            if show_correct_answer:
                result_dict['correct_answer'] = videoclase.correct_alternative
                result_dict['is_correct'] = instancia.is_correct()
        return JsonResponse(result_dict)

    def form_invalid(self, form):
        print(form.errors)
        result_dict = {}
        return JsonResponse(result_dict)


class IndexView(FormView):
    template_name = 'index.html'
    form_class = CustomAutheticationForm

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=form.get_user(), password=password)
        if user is not None:
            if user.is_active:
                login(self.request, form.get_user())
                return HttpResponseRedirect(self.get_success_url(user))
        return super(IndexView, self).form_valid(form)

    def get_success_url(self, user):
        if user.groups.filter(name='Profesores').exists():
            if user.teacher.changed_password:
                return reverse('teacher')
            else:
                return reverse('change_password')
        elif user.groups.filter(name='Alumnos').exists():
            if user.student.changed_password:
                return reverse('student')
            else:
                return reverse('change_password')
        elif user.groups.filter(name='Organizadores').exists():
            if user.organizer.changed_password:
                return reverse('organizer')
            else:
                return reverse('change_password')

    def get(self, request, *args, **kwargs):
        return super(IndexView, self).get(request, *args, **kwargs)


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))


class PerfilView(TemplateView):
    template_name = 'perfil.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return super(PerfilView, self).get(request, *args, **kwargs)


class TeacherView(TemplateView):
    template_name = 'teacher.html'

    def get_context_data(self, **kwargs):
        context = super(TeacherView, self).get_context_data(**kwargs)
        current_year = timezone.now().year
        teacher = self.request.user.teacher
        context['homeworks'] = Homework.objects.filter(course__teacher=teacher)
        context['courses_without_homework'] = teacher.courses.filter(course_homework=None)
        return context

    @method_decorator(user_passes_test(in_teachers_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(TeacherView, self).dispatch(*args, **kwargs)

class OrganizerView(TemplateView):
    template_name = 'header.html'

    def get_context_data(self, **kwargs):
        context = super(OrganizerView, self).get_context_data(**kwargs)
        current_year = timezone.now().year
        organizer = self.request.user.organizer
        context['homeworks'] = Homework.objects.filter(organizer=organizer)
        context['courses_without_homework'] = organizer.courses.filter(course_homework=None)
        return context

    @method_decorator(user_passes_test(in_organizer_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(OrganizerView, self).dispatch(*args, **kwargs)


class UploadScoreFormView(FormView):
    template_name = 'blank.html'
    form_class = UploadScoreForm
    success_url = '/teacher/'

    @method_decorator(user_passes_test(in_teachers_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(UploadScoreFormView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        group = GroupOfStudents.objects.get(id=form.cleaned_data['group'])
        student = Student.objects.get(id=form.cleaned_data['student'])
        notas = FinalScores.objects.get(group=group, student=student)
        notas.teacher_score = form.cleaned_data['nota']
        notas.save()
        result_dict = {}
        return JsonResponse(result_dict)

    def form_invalid(self, form):
        result_dict = {}
        return JsonResponse(result_dict)


class VideoclaseDetailView(TemplateView):
    template_name = 'student-watch-videoclase.html'

    def get_context_data(self, **kwargs):
        context = super(VideoclaseDetailView, self).get_context_data(**kwargs)
        homework = Homework.objects.get(id=self.kwargs['homework_id'])
        group = GroupOfStudents.objects.get(homework=homework, students=self.request.user.student)
        comments = StudentEvaluations.objects.filter(videoclase=group.videoclase,comments__isnull=False).exclude(
            comments__exact='').values('comments')
        context['comments'] = comments
        context['group'] = group
        return context

    @method_decorator(user_passes_test(in_students_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        homework = Homework.objects.get(id=self.kwargs['homework_id'])
        if homework.get_estado() != 3:
            return HttpResponseRedirect(reverse('student'))
        return super(VideoclaseDetailView, self).dispatch(*args, **kwargs)


def videoclases(request):
    return render(request, 'videoclases.html')


class VideoclasesStudentView(TemplateView):
    template_name = 'videoclases-student.html'

    def get_context_data(self, **kwargs):
        context = super(VideoclasesStudentView, self).get_context_data(**kwargs)
        student = Student.objects.get(id=kwargs['student_id'])
        groups = student.groupofstudents_set.exclude(videoclase__video=None).exclude(videoclase__video__exact='')
        pending_groups = student.groupofstudents_set.filter(
            Q(videoclase__video='') | Q(videoclase__video__isnull=True))
        vmerge = groups | pending_groups
        vmerge.order_by('-id')
        context['student'] = student
        context['groups'] = vmerge
        return context

    @method_decorator(user_passes_test(in_teachers_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(VideoclasesStudentView, self).dispatch(*args, **kwargs)


class VideoclasesHomeworkView(TemplateView):
    template_name = 'videoclases-homework.html'

    def get_context_data(self, **kwargs):
        context = super(VideoclasesHomeworkView, self).get_context_data(**kwargs)
        homework = get_object_or_404(Homework, id=self.kwargs['homework_id'])
        context['groups'] = homework.groups.all()
        context['homework'] = homework
        return context

    @method_decorator(user_passes_test(in_teachers_group, login_url='/'))
    def dispatch(self, *args, **kwargs):
        return super(VideoclasesHomeworkView, self).dispatch(*args, **kwargs)


def ui(request):
    return render(request, 'zontal/ui.html')


def forms(request):
    return render(request, 'forms.html')


class LoginError(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(status=401)


