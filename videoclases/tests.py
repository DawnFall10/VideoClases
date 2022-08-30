# -*- coding: UTF-8 -*-

import datetime
import json
import os
from datetime import timedelta
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.urls import reverse
from django.db.models import Q
from django.templatetags.static import static
from django.test import TestCase

from videoclases.forms.forms import *
from videoclases.models.course import Course
from videoclases.models.final_scores import FinalScores
from videoclases.models.groupofstudents import GroupOfStudents
from videoclases.models.homework import Homework
from videoclases.models.student import Student
from videoclases.models.student_evaluations import StudentEvaluations
from videoclases.models.student_responses import StudentResponses
from videoclases.models.video_clase import VideoClase

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
all_fixturues = ['devgroups', 'devusers', 'devcourses', 'devstudents', 'devteachers',
                      'devschool', 'devhomeworks', 'devgroupsstudent', 'devvideoclasesevaluando', 'devfinalscores',
                      'devstudentsresponses', 'devstudentevaluations']
this_year = datetime.date.today().year


class StudentTestCase(TestCase):
    fixtures = all_fixturues

    def test_student_permissions(self):
        self.client.login(username='student1', password='alumno')
        response = self.client.get(reverse('student'))
        self.assertEqual(response.status_code, 200)

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('student'))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('student'))
        self.assertEqual(response.status_code, 302)

    def test_states_homework(self):
        # date_upload = today
        # date_evaluation = today + 10 days
        # estado = 'Terminada'
        homework = Homework.objects.get(id=3)
        states = dict(homework.states)
        self.assertEqual(homework.get_estado(), states.get('Terminada'))

        # date_upload = today - 1
        # date_evaluation = today + 1
        # estado = 'Evaluando'
        today = timezone.datetime.date(timezone.datetime.now())
        homework.date_evaluation = today + timedelta(days=1)
        homework.date_upload = today - timedelta(days=1)
        self.assertEqual(homework.get_estado(), states.get('Evaluando'))

        # date_upload = today + 1
        # date_evaluation = today + 2
        # estado = 'Pendiente'
        homework.date_evaluation = today + timedelta(days=2)
        homework.date_upload = today + timedelta(days=1)
        self.assertEqual(homework.get_estado(), states.get('Pendiente'))

    def test_list_homeworks_get_table(self):
        self.client.login(username='student1', password='alumno')
        response = self.client.get(reverse('student'))
        student = Student.objects.get(user__username='student1')
        groups = GroupOfStudents.objects.filter(students=student)
        self.assertEqual(list(response.context['groups']), list(groups))


class DeleteStudentTestCase(TestCase):
    fixtures = all_fixturues

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('borrar_student',
                                           kwargs={'student_id': 1, 'course_id': 1}), follow=True)
        self.assertRedirects(response, reverse('edit_course', kwargs={'course_id': 1}))

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        response = self.client.get(reverse('borrar_student', kwargs={'student_id': 1, 'course_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('borrar_student', kwargs={'student_id': 1, 'course_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_student_not_in_course(self):
        self.client.login(username='profe', password='profe')
        teacher = User.objects.get(username='profe').teacher
        course = teacher.courses.order_by('?')[0]
        student = Student.objects.exclude(courses=course).order_by('?')[0]
        response = self.client.get(reverse('borrar_student',
                                           kwargs={'student_id': student.id, 'course_id': course.id}), follow=True)
        self.assertRedirects(response, reverse('teacher'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'El alumno no corresponde a este curso.')

    def test_teacher_not_assigned_to_course(self):
        self.client.login(username='profe', password='profe')
        # course 4 is not assigned to teacher 'profe'
        course_id = 4
        student = Course.objects.get(id=course_id).students.all()[0]
        response = self.client.get(reverse('borrar_student',
                                           kwargs={'student_id': student.id, 'course_id': course_id}), follow=True)
        self.assertRedirects(response, reverse('teacher'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'No tienes permisos para esta acción')

    def test_correct_delete(self):
        self.client.login(username='profe', password='profe')
        teacher = User.objects.get(username='profe').teacher
        course = teacher.courses.order_by('?')[0]
        student = course.students.order_by('?')[0]
        response = self.client.get(reverse('borrar_student',
                                           kwargs={'student_id': student.id, 'course_id': course.id}), follow=True)
        self.assertRedirects(response, reverse('edit_course', kwargs={'course_id': course.id}))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'El alumno fue borrado del course exitosamente.')


class DeleteCourseTestCase(TestCase):
    fixtures = all_fixturues

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('delete_course', kwargs={'course_id': 1}))
        self.assertEqual(response.status_code, 200)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        response = self.client.get(reverse('delete_course', kwargs={'course_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('delete_course', kwargs={'course_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_delete_course_teacher_not_assigned(self):
        self.client.login(username='profe', password='profe')
        # course 4 is not assigned to teacher 'profe'
        course_id = 4
        form_data = {}
        form_data['course'] = course_id
        form = DeleteCourseForm(form_data)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response redirect and message
        response = self.client.post(reverse('delete_course', kwargs={'course_id': course_id}),
                                    form_data, follow=True)
        self.assertRedirects(response, reverse('teacher'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'No tienes permisos para esta acción')

    def test_delete_course_does_not_exist_error(self):
        self.client.login(username='profe', password='profe')
        # course 4 is not assigned to teacher 'profe'
        course_id = 123123123
        form_data = {}
        form_data['course'] = course_id
        form = DeleteCourseForm(form_data)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response redirect and message
        response = self.client.post(reverse('delete_course', kwargs={'course_id': course_id}),
                                    form_data)
        self.assertEqual(response.status_code, 404)

    def test_delete_course_correct_form(self):
        self.client.login(username='profe', password='profe')
        # course 4 is not assigned to teacher 'profe'
        course_id = 1
        form_data = {}
        form_data['course'] = course_id
        form = DeleteCourseForm(form_data)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response redirect and message
        response = self.client.post(reverse('delete_course', kwargs={'course_id': course_id}),
                                    form_data, follow=True)
        self.assertRedirects(response, reverse('teacher'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'El curso se ha eliminado exitosamente')

        # assert valid deletion of object
        course_qs = Course.objects.filter(id=course_id)
        self.assertFalse(course_qs.exists())

        # assert valid deletion of other related objects
        groups_qs = GroupOfStudents.objects.filter(homework__course__id=course_id)
        videoclases_qs = VideoClase.objects.filter(group__homework__course__id=course_id)
        notasfinales_qs = FinalScores.objects.filter(group__homework__course__id=course_id)
        students_evaluations_qs = StudentEvaluations.objects \
            .filter(videoclase__group__homework__course__id=course_id)
        answersdestudents_qs = StudentResponses.objects \
            .filter(videoclase__group__homework__course__id=course_id)
        self.assertFalse(groups_qs.exists())
        self.assertFalse(videoclases_qs.exists())
        self.assertFalse(notasfinales_qs.exists())
        self.assertFalse(students_evaluations_qs.exists())
        self.assertFalse(answersdestudents_qs.exists())


class DeleteHomeworkTestCase(TestCase):
    fixtures = all_fixturues

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('new_course'))
        self.assertEqual(response.status_code, 200)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        response = self.client.get(reverse('new_course'))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('new_course'))
        self.assertEqual(response.status_code, 302)

    def test_delete_homework_form(self):
        self.client.login(username='profe', password='profe')
        homework_id = 10
        form_data = {}
        form_data['homework'] = homework_id
        form = DeleteHomeworkForm(form_data)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response redirect and message
        response = self.client.post(reverse('delete_course'), form_data, follow=True)
        self.assertRedirects(response, reverse('teacher'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'La tarea se ha eliminado exitosamente')

        # assert valid deletion of object
        homework_qs = Homework.objects.filter(id=homework_id)
        self.assertFalse(homework_qs.exists())

        # assert valid deletion of other related objects
        groups_qs = GroupOfStudents.objects.filter(homework__id=homework_id)
        videoclases_qs = VideoClase.objects.filter(group__homework__id=homework_id)
        final_scores_qs = FinalScores.objects.filter(group__homework__id=homework_id)
        students_evaluations_qs = StudentEvaluations.objects \
            .filter(videoclase__group__homework__id=homework_id)
        answersdestudents_qs = StudentResponses.objects \
            .filter(videoclase__group__homework__id=homework_id)
        self.assertFalse(groups_qs.exists())
        self.assertFalse(videoclases_qs.exists())
        self.assertFalse(final_scores_qs.exists())
        self.assertFalse(students_evaluations_qs.exists())
        self.assertFalse(answersdestudents_qs.exists())


class ChangePasswordTestCase(TestCase):
    fixtures = all_fixturues

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('change_password'))
        self.assertEqual(response.status_code, 302)

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        user = User.objects.get(username='profe')
        response = self.client.get(reverse('change_password'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'], user)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        user = User.objects.get(username='student')
        response = self.client.get(reverse('change_password'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'], user)

    def test_change_password_teacher_form(self):
        self.client.login(username='profe', password='profe')
        user = User.objects.get(username='profe')
        new_password = 'profe2'
        form_data = {}
        form_data['old_password'] = 'profe'
        form_data['new_password1'] = new_password
        form_data['new_password2'] = new_password
        form = ChangePasswordForm(user, form_data)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response
        response = self.client.post(reverse('change_password'), form_data, follow=True)
        self.assertRedirects(response, reverse('teacher'))
        self.assertEqual(response.status_code, 200)

        # assert valid change of password
        new_user = User.objects.get(username='profe')
        self.assertTrue(new_user.check_password(new_password))

    def test_change_password_form_initial_data_student(self):
        self.client.login(username='student1', password='alumno')
        user = User.objects.get(username='student1')

        # Check that name is pre-filled
        response = self.client.get(reverse('change_password'))
        self.assertEqual(response.context['form'].initial['email'], user.email)

    def test_change_password_form_initial_data_teacher(self):
        self.client.login(username='profe', password='profe')
        user = User.objects.get(username='profe')

        # Check that name is pre-filled
        response = self.client.get(reverse('change_password'))
        with self.assertRaises(KeyError) as raises:
            response.context['form'].initial['email']

    def test_change_password_student_with_email_correct_form(self):
        self.client.login(username='student1', password='alumno')
        user = User.objects.get(username='student1')
        new_password = 'student1'
        form_data = {}
        form_data['old_password'] = 'alumno'
        form_data['new_password1'] = new_password
        form_data['new_password2'] = new_password
        form_data['email'] = user.email
        form = ChangePasswordForm(user, form_data)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response
        response = self.client.post(reverse('change_password'), form_data, follow=True)
        self.assertRedirects(response, reverse('student'))
        self.assertEqual(response.status_code, 200)

        # assert valid change of password
        new_user = User.objects.get(username='student1')
        self.assertTrue(new_user.check_password(new_password))

    def test_change_password_student_without_email_correct_form(self):
        self.client.login(username='student2', password='alumno')
        user = User.objects.get(username='student2')
        new_password = 'student2'
        email = 'student2@student.com'
        form_data = {}
        form_data['old_password'] = 'alumno'
        form_data['new_password1'] = new_password
        form_data['new_password2'] = new_password
        form_data['email'] = email
        form = ChangePasswordForm(user, form_data)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response
        response = self.client.post(reverse('change_password'), form_data, follow=True)
        self.assertRedirects(response, reverse('student'))
        self.assertEqual(response.status_code, 200)

        # assert valid change of password
        new_user = User.objects.get(username='student2')
        self.assertTrue(new_user.check_password(new_password))
        self.assertEqual(new_user.email, email)

    def test_change_password_email_not_valid_error_form(self):
        self.client.login(username='student2', password='alumno')
        user = User.objects.get(username='student2')
        new_password = 'student2'
        form_data = {}
        form_data['old_password'] = 'student'
        form_data['new_password1'] = new_password
        form_data['new_password2'] = new_password
        form_data['email'] = 'this is not an email'
        form = ChangePasswordForm(user, form_data)

        # assert valid form
        self.assertFalse(form.is_valid())

        # assert valid response redirect and form error
        response = self.client.post(reverse('change_password'), form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', u'Introduzca una dirección de correo electrónico válida.')

        # assert did not change password
        new_user = User.objects.get(username='student2')
        self.assertFalse(new_user.check_password(new_password))

    def test_change_password_email_required_error_form(self):
        self.client.login(username='student2', password='alumno')
        user = User.objects.get(username='student2')
        new_password = 'student2'
        form_data = {}
        form_data['old_password'] = 'student'
        form_data['new_password1'] = new_password
        form_data['new_password2'] = new_password
        form = ChangePasswordForm(user, form_data)

        # assert valid form
        self.assertFalse(form.is_valid())

        # assert valid response redirect and form error
        response = self.client.post(reverse('change_password'), form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', u'Debes ingresar un correo.')

        # assert did not change password
        new_user = User.objects.get(username='student2')
        self.assertFalse(new_user.check_password(new_password))

    def test_change_password_password_incorrect_error_form(self):
        self.client.login(username='student1', password='alumno')
        user = User.objects.get(username='student1')
        new_password = 'student1'
        form_data = {}
        form_data['old_password'] = 'wrong_password'
        form_data['new_password1'] = new_password
        form_data['new_password2'] = new_password
        form = ChangePasswordForm(user, form_data)

        # assert valid form
        self.assertFalse(form.is_valid())

        # assert valid response redirect and form error
        response = self.client.post(reverse('change_password'), form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'old_password', 'Clave incorrecta.')

        # assert did not change password
        new_user = User.objects.get(username='student1')
        self.assertFalse(new_user.check_password(new_password))

    def test_change_password_password_mismatch_error_form(self):
        self.client.login(username='student1', password='alumno')
        user = User.objects.get(username='student1')
        new_password = 'student1'
        form_data = {}
        form_data['old_password'] = 'student'
        form_data['new_password1'] = new_password
        form_data['new_password2'] = 'wrong_new_password'
        form = ChangePasswordForm(user, form_data)

        # assert valid form
        self.assertFalse(form.is_valid())

        # assert valid response redirect and form error
        response = self.client.post(reverse('change_password'), form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'new_password2', u'Las contraseñas no coinciden.')

        # assert did not change password
        new_user = User.objects.get(username='student1')
        self.assertFalse(new_user.check_password(new_password))


class ChangeStudentPasswordTestCase(TestCase):
    fixtures = all_fixturues

    def test_anonymous_user_permissions(self):
        course = Course.objects.get(id=1)
        response = self.client.get(reverse('change_student_password', kwargs={'course_id': course.id}))
        self.assertEqual(response.status_code, 302)

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        course = Course.objects.get(id=1)
        response = self.client.get(reverse('change_student_password', kwargs={'course_id': course.id}))
        self.assertEqual(response.status_code, 200)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        course = Course.objects.get(id=1)
        response = self.client.get(reverse('change_student_password', kwargs={'course_id': course.id}))
        self.assertEqual(response.status_code, 302)

    def test_change_student_password_correct_form(self):
        self.client.login(username='profe', password='profe')
        student_user = User.objects.get(username='student3')
        course = student_user.student.courses.all()[0]
        new_password = 'student3'
        form_data = {}
        form_data['student'] = student_user.student.pk
        form_data['new_password1'] = new_password
        form_data['new_password2'] = new_password
        form = ChangeStudentPasswordForm(form_data)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response
        response = self.client.post(reverse('change_student_password', kwargs={'course_id': course.id}),
                                    form_data, follow=True)
        self.assertRedirects(response, reverse('teacher'))
        self.assertEqual(response.status_code, 200)

        # assert valid change of password
        new_user = User.objects.get(username='student3')
        self.assertTrue(new_user.check_password(new_password))

    def test_get_form_students(self):
        self.client.login(username='profe', password='profe')
        course = Course.objects.all()[0]
        response = self.client.get(reverse('change_student_password', kwargs={'course_id': course.id}))

        # assert valid students variable in form in context
        self.assertEqual(list(response.context['form'].fields['student'].queryset),
                         list(course.students.all()))

    def test_change_password_student_invalid_choice_error_form(self):
        self.client.login(username='profe', password='profe')
        student_user = User.objects.get(username='student2')
        course = student_user.student.courses.all()[0]
        new_password = 'student2'
        form_data = {}
        form_data['student'] = ''
        form_data['new_password1'] = new_password
        form_data['new_password2'] = new_password
        form = ChangeStudentPasswordForm(form_data)

        # assert valid form
        self.assertFalse(form.is_valid())

        # assert valid response redirect and form error
        response = self.client.post(reverse('change_student_password', kwargs={'course_id': course.id}),
                                    form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'student', u'Este campo es obligatorio.')

        # assert did not change password
        new_user = User.objects.get(username='student2')
        self.assertFalse(new_user.check_password(new_password))


class ChangeStudentPasswordSelectCourseTestCase(TestCase):
    fixtures = all_fixturues

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('change_student_password_select_course'))
        self.assertEqual(response.status_code, 302)

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        user = User.objects.get(username='profe')
        response = self.client.get(reverse('change_student_password_select_course'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'], user)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        response = self.client.get(reverse('change_student_password_select_course'))
        self.assertEqual(response.status_code, 302)

    def test_change_student_password_select_course_form(self):
        self.client.login(username='profe', password='profe')
        course = Course.objects.get(id=1)
        new_password = 'student1'
        form_data = {}
        form_data['course'] = course.id
        form = ChangeStudentPasswordSelectCursoForm(form_data)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response
        response = self.client.post(reverse('change_student_password_select_course'), form_data, follow=True)
        self.assertRedirects(response, reverse('change_student_password', kwargs={'course_id': course.id}))
        self.assertEqual(response.status_code, 200)


class newCourseTestCase(TestCase):
    fixtures = all_fixturues

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('new_course'))
        self.assertEqual(response.status_code, 200)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        response = self.client.get(reverse('new_course'))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('new_course'))
        self.assertEqual(response.status_code, 302)

    def new_course_form_correct(self, filename, content_type):
        # sheet has 2 students
        # usernames dmunoz and anoram

        self.client.login(username='profe', password='profe')
        user = User.objects.get(username='profe')
        original_students = Student.objects.all().count()
        path = BASE_DIR + '/project' + static(filename)
        upload_file = open(path, 'rb')
        # (self, file, field_name, name, content_type, size, charset, content_type_extra=None)
        imf = InMemoryUploadedFile(BytesIO(upload_file.read()), 'file', upload_file.name,
                                   content_type, os.path.getsize(path), None, {})
        file_dict = {'file': imf}
        form_data = {}
        form_data['name'] = 'Nombre'
        form_data['year'] = this_year
        form_data['file'] = imf
        form = NewCourseUploadFileForm(form_data, file_dict)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response redirect and message
        response = self.client.post(reverse('new_course'), form_data, follow=True)
        self.assertRedirects(response, reverse('teacher'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'El curso se ha creado exitosamente')

        # assert valid creation of object
        course = Course.objects.filter(name='Nombre', year=this_year, school=user.teacher.school)
        self.assertTrue(course.exists())
        self.assertEqual(course.count(), 1)

        # assert valid creation of students
        self.assertEqual(original_students + 2, Student.objects.all().count())
        self.assertTrue(User.objects.filter(username='dmunoz').exists())
        self.assertTrue(User.objects.filter(username='anoram').exists())
        self.assertIsInstance(User.objects.get(username='dmunoz').student, Student)
        self.assertIsInstance(User.objects.get(username='anoram').student, Student)
        upload_file.close()
        imf.close()

    def test_new_course_form_correct_ods(self):
        self.new_course_form_correct(
            'test/correctSheet.ods',
            'application/vnd.oasis.opendocument.spreadsheet')

    def test_new_course_form_correct_xls(self):
        self.new_course_form_correct(
            'test/correctSheet.xls',
            'application/vnd.ms-excel')

    def test_new_course_form_correct_xlsx(self):
        self.new_course_form_correct(
            'test/correctSheet.xlsx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def new_course_form_incomplete(self, filename, content_type):
        # sheet has 2 students
        # usernames dmunoz and anoram

        self.client.login(username='profe', password='profe')
        user = User.objects.get(username='profe')
        path = BASE_DIR + '/project' + static(filename)
        upload_file = open(path, 'rb')
        imf = InMemoryUploadedFile(BytesIO(upload_file.read()), 'file', upload_file.name,
                                   content_type, os.path.getsize(path), None, {})
        file_dict = {'file': imf}
        form_data = {}
        form_data['name'] = 'Nombre'
        form_data['year'] = this_year
        form_data['file'] = imf
        form = NewCourseUploadFileForm(form_data, file_dict)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response redirect and message
        response = self.client.post(reverse('new_course'), form_data, follow=True)
        self.assertRedirects(response, reverse('new_course'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'El archivo no tiene toda la información de un alumno.')
        upload_file.close()

    def test_new_course_form_incomplete_ods(self):
        self.new_course_form_incomplete(
            'test/incompleteSheet.ods',
            'application/vnd.oasis.opendocument.spreadsheet')

    def test_new_course_form_incomplete_xls(self):
        self.new_course_form_incomplete(
            'test/incompleteSheet.xls',
            'application/vnd.ms-excel')

    def test_new_course_form_incomplete_xlsx(self):
        self.new_course_form_incomplete(
            'test/incompleteSheet.xlsx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def test_new_course_form_wrong_extension(self):
        self.client.login(username='profe', password='profe')
        user = User.objects.get(username='profe')
        path = BASE_DIR + '/project' + static('test/image.png')
        upload_file = open(path, 'rb')
        imf = InMemoryUploadedFile(BytesIO(upload_file.read()), 'file', upload_file.name,
                                   'image/png', os.path.getsize(path), None, {})
        file_dict = {'file': imf}
        form_data = {}
        form_data['name'] = 'Nombre'
        form_data['year'] = this_year
        form_data['file'] = imf
        form = NewCourseUploadFileForm(form_data, file_dict)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response redirect and message
        response = self.client.post(reverse('new_course'), form_data, follow=True)
        self.assertRedirects(response, reverse('new_course'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'El archivo debe ser formato XLS, XLSX u ODS.')


class CrearTareaTestCase(TestCase):
    fixtures = all_fixturues

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('new_homework'))
        self.assertEqual(response.status_code, 200)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        response = self.client.get(reverse('new_homework'))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('new_homework'))
        self.assertEqual(response.status_code, 302)

    def test_new_homework_get(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('new_homework'))
        user = User.objects.get(username='profe')
        courses = user.teacher.courses.filter(year=timezone.now().year)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['courses']), list(courses))

    def test_new_homework_form(self):
        self.client.login(username='profe', password='profe')
        form_data = {}
        form_data['title'] = 'title'
        form_data['description'] = 'description'
        form_data['course'] = 1
        form_data['revision'] = 1
        today = datetime.datetime.today()
        form_data['date_upload'] = today.strftime('%Y-%m-%d')
        form_data['date_evaluation'] = (today + datetime.timedelta(days=10)).strftime('%Y-%m-%d')
        form_data['video'] = 'https://www.youtube.com/watch?v=8a7sd82s'
        form = NewHomeworkForm(form_data)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response
        response = self.client.post(reverse('new_homework_form'), form_data)
        self.assertEqual(response.status_code, 200)

        # assert valid creation of object
        new_homework = Homework.objects.get(title='title', description='description')
        self.assertEqual(new_homework, Homework.objects.latest('id'))
        self.assertEqual(new_homework.video, u'https://www.youtube.com/embed/8a7sd82s')

    def test_assign_group_form(self):
        self.client.login(username='profe', password='profe')
        form_data = {}
        form_data['groups'] = '{"1":[34,37,38],"2":[31,39,40],"3":[33,35,36],"4":[32]}'
        form_data['homework'] = 2
        form = AssignGroupForm(form_data)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response
        response = self.client.post(reverse('assign_group_form'), form_data)
        self.assertEqual(response.status_code, 200)

        # assert valid creation of object
        students = [Student.objects.get(id=34), Student.objects.get(id=37), Student.objects.get(id=38)]
        homework = Homework.objects.get(id=2)
        new_group = GroupOfStudents.objects.get(number=1, homework=homework)
        self.assertEqual(list(new_group.students.all()), list(students))

        # assert valid creation of FinalScores
        nf = FinalScores.objects.filter(group=new_group)
        self.assertTrue(nf.exists())


class CourseTestCase(TestCase):
    fixtures = all_fixturues

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('course', kwargs={'course_id': 1}))
        self.assertEqual(response.status_code, 200)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        response = self.client.get(reverse('course', kwargs={'course_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('course', kwargs={'course_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_list_courses_get_table(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('course', kwargs={'course_id': 1}))
        course = Course.objects.get(id=1)
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
        self.assertEqual(response.context['students'], students_array)
        self.assertEqual(response.context['course'], course)


class DownloadCourseTestCase(TestCase):
    fixtures = all_fixturues

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('download_course', kwargs={'course_id': 1}))
        self.assertEqual(response.status_code, 200)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        response = self.client.get(reverse('download_course', kwargs={'course_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('download_course', kwargs={'course_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_json_download(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('download_course', kwargs={'course_id': 1}))
        result_dict = {}
        course = Course.objects.get(id=1)
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
        self.assertJSONEqual(response.content.decode("utf-8"), result_dict)


class DownloadGroupsHomeworkTestCase(TestCase):
    fixtures = all_fixturues

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('download_homework_groups', kwargs={'homework_id': 1}))
        self.assertEqual(response.status_code, 200)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        response = self.client.get(reverse('download_homework_groups', kwargs={'homework_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('download_homework_groups', kwargs={'homework_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_json_download(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('download_homework_groups', kwargs={'homework_id': 1}))
        result_dict = {}
        homework = Homework.objects.get(id=1)
        course_dict = {}
        course_dict['id'] = homework.course.id
        course_dict['name'] = homework.course.name
        students_array = []
        for g in homework.groups.all():
            for a in g.students.all():
                student_dict = {}
                student_dict['id'] = a.id
                student_dict['first_name'] = a.user.last_name
                student_dict['last_name'] = a.user.first_name
                student_dict['group'] = g.number
                student_dict['videoclase'] = g.videoclase.video not in [None, '']
                students_array.append(student_dict)
        result_dict['students'] = students_array
        result_dict['course'] = course_dict
        self.assertJSONEqual(response.content.decode("utf-8"), result_dict)


class EditHomeworkTestCase(TestCase):
    fixtures = all_fixturues

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        student_id = 1
        course_id = Student.objects.get(id=student_id).courses.all()[0].id
        response = self.client.get(reverse('edit_student',
                                           kwargs={'student_id': student_id, 'course_id': course_id}))
        self.assertEqual(response.status_code, 200)

        # test initial form values
        student = Student.objects.get(id=student_id)
        self.assertEqual(response.context['form'].initial['first_name'], student.user.first_name)
        self.assertEqual(response.context['form'].initial['last_name'], student.user.last_name)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        response = self.client.get(reverse('edit_student', kwargs={'student_id': 1, 'course_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('edit_student', kwargs={'student_id': 1, 'course_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_student_not_in_course(self):
        self.client.login(username='profe', password='profe')
        student_id = 1
        student = Student.objects.get(id=student_id)
        course = Course.objects.exclude(students=student)[0]
        response = self.client.get(reverse('edit_student',
                                           kwargs={'student_id': student_id, 'course_id': course.id}))
        self.assertEqual(response.status_code, 404)

    def test_change_student_first_name(self):
        self.client.login(username='profe', password='profe')
        student_id = 1
        student = Student.objects.get(id=student_id)
        student_original_first_name = student.user.first_name
        student_original_last_name = student.user.last_name
        course = student.courses.all()[0]
        new_first_name = 'new first name'
        form_data = {}
        form_data['first_name'] = new_first_name
        form_data['last_name'] = student_original_last_name
        form = EditStudentForm(form_data)

        # assert form is valid
        self.assertTrue(form.is_valid())

        # assert valid response, redirect and message
        response = self.client.post(reverse('edit_student',
                                            kwargs={'student_id': student_id, 'course_id': course.id}),
                                    form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('edit_course', kwargs={'course_id': course.id}))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'El alumno ha sido editado exitosamente.')

        # assert valid edition of object
        new_student = Student.objects.get(id=student_id)
        new_student_first_name = new_student.user.first_name
        new_student_last_name = new_student.user.last_name
        self.assertNotEqual(student_original_first_name, new_student_first_name)
        self.assertEqual(new_student_first_name, new_first_name)
        self.assertEqual(new_student_last_name, student_original_last_name)

    def test_change_student_last_name(self):
        self.client.login(username='profe', password='profe')
        student_id = 1
        student = Student.objects.get(id=student_id)
        student_original_first_name = student.user.first_name
        student_original_last_name = student.user.last_name
        course = student.courses.all()[0]
        new_last_name = 'new last name'
        form_data = {}
        form_data['first_name'] = student_original_first_name
        form_data['last_name'] = new_last_name
        form = EditStudentForm(form_data)

        # assert form is valid
        self.assertTrue(form.is_valid())

        # assert valid response, redirect and message
        response = self.client.post(reverse('edit_student',
                                            kwargs={'student_id': student_id, 'course_id': course.id}),
                                    form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('edit_course', kwargs={'course_id': course.id}))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'El alumno ha sido editado exitosamente.')

        # assert valid edition of object
        new_student = Student.objects.get(id=student_id)
        new_student_first_name = new_student.user.first_name
        new_student_last_name = new_student.user.last_name
        self.assertNotEqual(student_original_last_name, new_student_last_name)
        self.assertEqual(new_student_last_name, new_last_name)
        self.assertEqual(new_student_first_name, student_original_first_name)


class EditCourseTestCase(TestCase):
    fixtures = all_fixturues

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('edit_course', kwargs={'course_id': 1}))
        self.assertEqual(response.status_code, 200)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        response = self.client.get(reverse('edit_course', kwargs={'course_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('edit_course', kwargs={'course_id': 1}))
        self.assertEqual(response.status_code, 302)


class EditGroupTestCase(TestCase):
    fixtures = all_fixturues

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('edit_group_form'))
        self.assertEqual(response.status_code, 200)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        response = self.client.get(reverse('edit_group_form'))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('edit_group_form'))
        self.assertEqual(response.status_code, 302)

    def test_edit_group_form_simple_case_remove_group(self):
        self.client.login(username='profe', password='profe')

        # students to use in tests
        a1 = Student.objects.get(id=32)
        a2 = Student.objects.get(id=33)
        a3 = Student.objects.get(id=35)
        a4 = Student.objects.get(id=36)

        # assign groups for test
        original_groups_data = {}
        original_groups_data['groups'] = '{"1":[34,37,38],"2":[31,39,40],"3":[33,35,36],"4":[32]}'
        original_groups_data['homework'] = 2
        self.client.post(reverse('assign_group_form'), original_groups_data)

        # post edited groups data
        edited_groups_data = {}
        edited_groups_data['groups'] = '{"1":[34,37,38],"2":[31,39,40],"3":[32,33,35,36]}'
        edited_groups_data['homework'] = 2
        form = AssignGroupForm(edited_groups_data)

        # assert form is valid
        self.assertTrue(form.is_valid())

        # assert valid response
        response = self.client.post(reverse('edit_group_form'), edited_groups_data)
        self.assertEqual(response.status_code, 200)

        # assert valid creation of object
        students = [a1, a2, a3, a4]
        homework = Homework.objects.get(id=2)
        edited_group = GroupOfStudents.objects.get(number=3, homework=homework)
        self.assertEqual(list(edited_group.students.all()), list(students))
        self.assertTrue(edited_group.videoclase not in [None, ''])

        # assert valid creation of FinalScores
        nf1 = FinalScores.objects.filter(group=edited_group, student=a1)
        nf2 = FinalScores.objects.filter(group=edited_group, student=a2)
        nf3 = FinalScores.objects.filter(group=edited_group, student=a3)
        nf4 = FinalScores.objects.filter(group=edited_group, student=a4)
        self.assertTrue(nf1.exists())
        self.assertTrue(nf2.exists())
        self.assertTrue(nf3.exists())
        self.assertTrue(nf4.exists())

        # assert valid removal of objects
        deleted_group = GroupOfStudents.objects.filter(number=4, homework=homework)
        deleted_nf = FinalScores.objects.filter(group__number=4, group__homework=homework)
        self.assertFalse(deleted_group.exists())
        self.assertFalse(deleted_nf.exists())

    def test_edit_group_form_simple_case_add_group(self):
        self.client.login(username='profe', password='profe')

        # students to use in tests
        a1 = Student.objects.get(id=32)
        a2 = Student.objects.get(id=33)
        a3 = Student.objects.get(id=35)
        a4 = Student.objects.get(id=36)

        # assign groups for test
        original_groups_data = {}
        original_groups_data['groups'] = '{"1":[34,37,38],"2":[31,39,40],"3":[32,33,35,36]}'
        original_groups_data['homework'] = 2
        self.client.post(reverse('assign_group_form'), original_groups_data)

        # post edited groups data
        edited_groups_data = {}
        edited_groups_data['groups'] = '{"1":[34,37,38],"2":[31,39,40],"3":[33,35,36], "4":[32]}'
        edited_groups_data['homework'] = 2
        form = AssignGroupForm(edited_groups_data)

        # assert form is valid
        self.assertTrue(form.is_valid())

        # assert valid response
        response = self.client.post(reverse('edit_group_form'), edited_groups_data)
        self.assertEqual(response.status_code, 200)

        # assert valid creation of new group
        students = [a1]
        homework = Homework.objects.get(id=2)
        created_group = GroupOfStudents.objects.get(number=4, homework=homework)
        self.assertEqual(list(created_group.students.all()), list(students))
        self.assertTrue(created_group.videoclase not in [None, ''])

        # assert valid creation of FinalScores
        nf1 = FinalScores.objects.filter(group=created_group, student=a1)
        self.assertTrue(nf1.exists())

    def test_edit_group_incomplete_data(self):
        self.client.login(username='profe', password='profe')

        # students to use in tests
        a1 = Student.objects.get(id=31)
        a2 = Student.objects.get(id=39)
        a3 = Student.objects.get(id=40)

        # assign groups for test
        original_groups_data = {}
        original_groups_data['groups'] = '{"1":[34,37,38],"2":[31,39,40],"3":[33,35,36],"4":[32]}'
        original_groups_data['homework'] = 2
        self.client.post(reverse('assign_group_form'), original_groups_data)

        # post edited groups data
        edited_groups_data = {}
        edited_groups_data['groups'] = '{"1":[34,37,38],"2":[31,39],"3":[33,35,36],"4":[32]}'
        edited_groups_data['homework'] = 2
        form = AssignGroupForm(edited_groups_data)

        # assert form is valid
        self.assertTrue(form.is_valid())

        # assert valid response
        response = self.client.post(reverse('edit_group_form'), edited_groups_data)
        self.assertEqual(response.status_code, 200)

        # assert that groups were not changed
        students = [a1, a2, a3]
        homework = Homework.objects.get(id=2)
        not_edited_group = GroupOfStudents.objects.get(number=2, homework=homework)
        self.assertEqual(list(not_edited_group.students.all()), list(students))
        self.assertTrue(not_edited_group.videoclase not in [None, ''])

        # assert FinalScores were not changed
        nf1 = FinalScores.objects.filter(group=not_edited_group, student=a1)
        nf2 = FinalScores.objects.filter(group=not_edited_group, student=a2)
        nf3 = FinalScores.objects.filter(group=not_edited_group, student=a3)
        self.assertTrue(nf1.exists())
        self.assertTrue(nf2.exists())
        self.assertTrue(nf3.exists())

        # assert correct response
        resp_json = json.loads(response.content.decode("utf-8"))
        self.assertFalse(resp_json['success'])
        self.assertEqual(resp_json['message'], u'Datos incompletos, todos los alumnos deben tener grupo.')

    def test_edit_group_incomplete_data_with_rare_group_numbers(self):
        self.client.login(username='profe', password='profe')

        # students to use in tests
        a1 = Student.objects.get(id=31)
        a2 = Student.objects.get(id=39)
        a3 = Student.objects.get(id=40)

        # assign groups for test
        original_groups_data = {}
        original_groups_data['groups'] = '{"1":[34,37,38],"2":[31,39,40],"3":[33,35,36],"4":[32]}'
        original_groups_data['homework'] = 2
        self.client.post(reverse('assign_group_form'), original_groups_data)

        # post edited groups data
        edited_groups_data = {}
        edited_groups_data['groups'] = '{"45":[34,37,38],"67":[31,39],"88":[33,35,36],"110":[32]}'
        edited_groups_data['homework'] = 2
        form = AssignGroupForm(edited_groups_data)

        # assert form is valid
        self.assertTrue(form.is_valid())

        # assert valid response
        response = self.client.post(reverse('edit_group_form'), edited_groups_data)
        self.assertEqual(response.status_code, 200)

        # assert that groups were not changed
        students = [a1, a2, a3]
        homework = Homework.objects.get(id=2)
        not_edited_group = GroupOfStudents.objects.get(number=2, homework=homework)
        self.assertEqual(list(not_edited_group.students.all()), list(students))
        self.assertTrue(not_edited_group.videoclase not in [None, ''])

        # assert FinalScores were not changed
        nf1 = FinalScores.objects.filter(group=not_edited_group, student=a1)
        nf2 = FinalScores.objects.filter(group=not_edited_group, student=a2)
        nf3 = FinalScores.objects.filter(group=not_edited_group, student=a3)
        self.assertTrue(nf1.exists())
        self.assertTrue(nf2.exists())
        self.assertTrue(nf3.exists())

        # assert correct response
        resp_json = json.loads(response.content.decode("utf-8"))
        self.assertFalse(resp_json['success'])
        self.assertEqual(resp_json['message'],
                         u'Los números de los groups no son consecutivos. Revisa si hay algún error.')

    def test_edit_group_data_with_rare_group_numbers(self):
        self.client.login(username='profe', password='profe')

        # post edited groups data
        edited_groups_data = {}
        edited_groups_data['groups'] = '{"24":[34,37,38],"55":[31,39,40],"110":[32,33,35,36]}'
        edited_groups_data['homework'] = 2
        form = AssignGroupForm(edited_groups_data)

        # assert form is valid
        self.assertTrue(form.is_valid())

        # assert valid response
        response = self.client.post(reverse('edit_group_form'), edited_groups_data)
        self.assertEqual(response.status_code, 200)

        # assert correct response
        resp_json = json.loads(response.content.decode("utf-8"))
        self.assertFalse(resp_json['success'])
        self.assertEqual(resp_json['message'],
                         u'Los números de los groups no son consecutivos. Revisa si hay algún error.')


class EditHomeworkTestCase(TestCase):
    fixtures = all_fixturues

    def create_hw(self, homework_original):
        form_data = {}
        form_data['title'] = homework_original.title
        form_data['description'] = homework_original.description
        form_data['course'] = homework_original.course.id
        form_data['revision'] = homework_original.revision
        form_data['date_upload'] = homework_original.date_upload
        form_data['date_evaluation'] = homework_original.date_evaluation

        form_data['video'] = homework_original.video
        return form_data

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('homework', kwargs={'homework_id': 1}))
        self.assertEqual(response.status_code, 200)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        response = self.client.get(reverse('homework', kwargs={'homework_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('homework', kwargs={'homework_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_homework_get_data(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('homework', kwargs={'homework_id': 1}))
        homework = Homework.objects.get(id=1)
        user = User.objects.get(username='profe')
        videoclases = GroupOfStudents.objects.filter(homework=homework).exclude(
            videoclase__video__isnull=True) \
            .exclude(videoclase__video__exact='').count()
        # courses = user.teacher.courses.all()
        self.assertEqual(response.context['videoclases_recibidas'], videoclases)
        self.assertEqual(response.context['homework'], homework)

    def test_edit_homework_form(self):
        self.client.login(username='profe', password='profe')
        homework_original = Homework.objects.get(id=9)
        form_data = self.create_hw(homework_original)
        form_data['revision'] = 5
        form = EditHomeworkForm(form_data)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert processing of link
        link, success = Homework.process_youtube_default_link('https://www.youtube.com/embed/JFfcD-SkqIc')
        self.assertEqual(link, u'https://www.youtube.com/embed/JFfcD-SkqIc')
        form_data['video'] = link

        # assert valid response
        response = self.client.post(reverse('edit_homework_form', kwargs={'homework_id': 9}), form_data)
        self.assertEqual(response.status_code, 200)

        # assert valid edit of object
        homework_to_edit = Homework.objects.get(id=9)
        self.assertNotEqual(homework_to_edit.revision, homework_original.revision)
        self.assertEqual(homework_to_edit.date_upload, homework_original.date_upload)
        self.assertEqual(homework_to_edit.video, link)
        self.assertEqual(5, Homework.objects.get(id=9).revision)

    def test_edit_homework_form_empty_video(self):
        self.client.login(username='profe', password='profe')
        homework_original = Homework.objects.get(id=9)
        form_data = self.create_hw(homework_original)

        form_data['video'] = 'empty video'
        form = EditHomeworkForm(form_data)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response
        response = self.client.post(reverse('edit_homework_form', kwargs={'homework_id': 9}), form_data)
        self.assertEqual(response.status_code, 200)

        # assert valid edit of object
        homework_to_edit = Homework.objects.get(id=9)
        self.assertNotEqual(homework_to_edit.video, homework_original.video)
        self.assertEqual(homework_to_edit.revision, homework_original.revision)
        self.assertEqual(homework_to_edit.date_upload, homework_original.date_upload)
        self.assertEqual('', Homework.objects.get(id=9).video)


class SendVideoclaseTestCase(TestCase):
    fixtures = all_fixturues

    def test_student_has_homework_permissions(self):
        self.client.login(username='student1', password='alumno')
        response = self.client.get(reverse('send_videoclase', kwargs={'homework_id': 1}))
        self.assertEqual(response.status_code, 200)

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('send_videoclase', kwargs={'homework_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('send_videoclase', kwargs={'homework_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_student_does_not_have_homework_permissions(self):
        self.client.login(username='student1', password='alumno')
        response = self.client.get(reverse('send_videoclase', kwargs={'homework_id': 2}))
        self.assertEqual(response.status_code, 404)

    def test_student_homework_does_not_exist_permissions(self):
        self.client.login(username='student1', password='alumno')
        response = self.client.get(reverse('send_videoclase', kwargs={'homework_id': 1234567}))
        self.assertEqual(response.status_code, 404)

    def test_student_homework_status_after_upload_date_before_evaluation_date(self):
        self.client.login(username='student1', password='alumno')
        response = self.client.get(reverse('send_videoclase', kwargs={'homework_id': 10}))
        self.assertEqual(response.status_code, 200)

    def test_send_videoclase_get_data(self):
        self.client.login(username='student1', password='alumno')
        response = self.client.get(reverse('send_videoclase', kwargs={'homework_id': 1}))
        homework = Homework.objects.get(id=1)
        user = User.objects.get(username='student1')
        videoclase = VideoClase.objects.get(group__students=user.student, group__homework=homework)
        self.assertEqual(response.context['videoclase'], videoclase)

    def test_send_videoclase_form(self):
        self.client.login(username='student1', password='alumno')
        response = self.client.get(reverse('send_videoclase', kwargs={'homework_id': 1}))
        user = User.objects.get(username='student1')
        form_data = {}
        form_data['video'] = 'https://www.youtube.com/watch?v=KMFOVSWn0mI'
        form_data['question'] = u'¿1 + 2?'
        form_data['correct_alternative'] = '3'
        form_data['alternative_2'] = '4'
        form_data['alternative_3'] = '5'
        form = SendVideoclaseForm(form_data)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response
        response = self.client.post(reverse('send_videoclase', kwargs={'homework_id': 1}), form_data)
        self.assertEqual(response.status_code, 302)

        # assert valid creation of object
        link, success = VideoClase.process_youtube_default_link('https://www.youtube.com/watch?v=KMFOVSWn0mI')
        videoclase_enviada = VideoClase.objects.get(group__students=user.student, video=link)
        latest_edited_videoclase = VideoClase.objects.all().order_by('-upload_students')[0]
        self.assertEqual(videoclase_enviada, latest_edited_videoclase)


class ReviewVideoclaseTestCase(TestCase):
    fixtures = all_fixturues

    def test_student_has_homework_permissions(self):
        self.client.login(username='student2', password='alumno')
        response = self.client.get(reverse('review_videoclase', kwargs={'homework_id': 10}))
        self.assertEqual(response.status_code, 200)

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('review_videoclase', kwargs={'homework_id': 10}))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('review_videoclase', kwargs={'homework_id': 10}))
        self.assertEqual(response.status_code, 302)

    def test_student_does_not_have_homework_permissions(self):
        self.client.login(username='student1', password='alumno')
        response = self.client.get(reverse('review_videoclase', kwargs={'homework_id': 2}))
        self.assertEqual(response.status_code, 404)

    def test_student_homework_status_wrong_permissions(self):
        self.client.login(username='student1', password='alumno')
        response = self.client.get(reverse('api_get_videoclase', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('redirect', False))

    def test_student_homework_does_not_exist_permissions(self):
        self.client.login(username='student1', password='alumno')
        response = self.client.get(reverse('review_videoclase', kwargs={'homework_id': 1234567}))
        self.assertEqual(response.status_code, 404)

    def test_review_video_correct_data(self):
        self.client.login(username='student1', password='alumno')
        student = User.objects.get(username='student1').student
        group = GroupOfStudents.objects.get(id=51)
        original_review = StudentEvaluations.objects.get(
            author=student, videoclase=group.videoclase)
        value = 1 if original_review.value < 1 else 0
        form_data = {}
        form_data['value'] = value
        form_data['format'] = value
        form_data['copyright'] = value
        form_data['theme'] = value
        form_data['pedagogical'] = value
        form_data['rythm'] = value
        form_data['originality'] = value
        form_data['videoclase'] = 36
        form = StudentEvaluationsForm(form_data)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response
        response = self.client.post(reverse('evaluar_video'), form_data)
        self.assertEqual(response.status_code, 200)

        # assert valid edit of object
        edited_review = StudentEvaluations.objects.get(
            author=student, videoclase=group.videoclase)
        self.assertNotEqual(edited_review.value, original_review.value)
        self.assertEqual(value, edited_review.value)


class ReviewVideoclaseFormViewTestCase(TestCase):
    fixtures = all_fixturues

    def test_student_has_homework_permissions(self):
        self.client.login(username='student2', password='alumno')
        response = self.client.get(reverse('review_videoclase_form'))
        self.assertEqual(response.status_code, 200)

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('review_videoclase_form'))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('review_videoclase_form'))
        self.assertEqual(response.status_code, 302)

    def test_review_videoclase_form(self):
        self.client.login(username='student2', password='alumno')

    def test_answer_question_correct_data(self):
        self.client.login(username='student10', password='alumno')
        student = User.objects.get(username='student1').student
        videoclase = VideoClase.objects.get(id=38)
        form_data = {}
        form_data['videoclase'] = videoclase.id
        form_data['answer'] = videoclase.correct_alternative
        form = StudentResponsesForm(form_data)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response
        response = self.client.get(reverse('review_videoclase_form'), form_data)
        self.assertEqual(response.status_code, 200)

        # assert valid update of object
        obj = form.save(commit=False)
        obj.student = student
        obj.save()
        answer = StudentResponses.objects.filter(videoclase=videoclase, student=student,
                                                 answer=videoclase.correct_alternative).exists()
        self.assertTrue(answer)


class PerfilTestCase(TestCase):
    fixtures = all_fixturues

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('perfil'))
        self.assertEqual(response.status_code, 200)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        response = self.client.get(reverse('perfil'))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('perfil'))
        self.assertEqual(response.status_code, 302)


class TeacherTestCase(TestCase):
    fixtures = all_fixturues

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('teacher'))
        self.assertEqual(response.status_code, 200)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        response = self.client.get(reverse('teacher'))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('teacher'))
        self.assertEqual(response.status_code, 302)

    def test_teacher_get_courses_homeworks_table(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('teacher'))
        user = User.objects.get(username='profe')
        homeworks = Homework.objects.filter(course__teacher=user.teacher)
        courses_without_homework = Course.objects.filter(course_homework=None).filter(teacher=user.teacher)
        self.assertEqual(list(response.context['homeworks']), list(homeworks))
        self.assertEqual(list(response.context['courses_without_homework']), list(courses_without_homework))


class UploadScoreFormTestCase(TestCase):
    fixtures = all_fixturues

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('upload_score'))
        self.assertEqual(response.status_code, 200)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        response = self.client.get(reverse('upload_score'))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('upload_score'))
        self.assertEqual(response.status_code, 302)

    def test_teacher_upload_score_form(self):
        self.client.login(username='profe', password='profe')
        student_test = Student.objects.get(id=5)
        group_test = GroupOfStudents.objects.filter(students=student_test)[0]
        original_score = FinalScores.objects.get(student=student_test, group=group_test)
        form_data = {}
        form_data['group'] = group_test.id
        form_data['student'] = student_test.id
        form_data['nota'] = 3 if original_score.teacher_score >= 4 else 5
        form = UploadScoreForm(form_data)

        # assert valid form
        self.assertTrue(form.is_valid())

        # assert valid response
        response = self.client.post(reverse('upload_score'), form_data)
        self.assertEqual(response.status_code, 200)

        # assert valid edit of object
        edited_score = FinalScores.objects.get(student=student_test, group=group_test)
        self.assertNotEqual(edited_score.teacher_score, original_score.teacher_score)
        if original_score.teacher_score >= 4:
            self.assertEqual(edited_score.teacher_score, 3)
        else:
            self.assertEqual(edited_score.teacher_score, 5)


class HomeworkModelMethodsTestCase(TestCase):
    fixtures = all_fixturues

    def test_get_uploaded_videoclases(self):
        # homework with every group with videoclase uploaded
        homework_id = 16
        homework = Homework.objects.get(pk=homework_id)
        self.assertEqual(homework.get_uploaded_videoclases(), homework.groups.count())


class WatchVideoclaseTestCase(TestCase):
    fixtures = all_fixturues

    def test_student_permissions(self):
        self.client.login(username='student1', password='alumno')
        response = self.client.get(reverse('watch_videoclase', kwargs={'homework_id': 16}))
        self.assertEqual(response.status_code, 200)

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('watch_videoclase', kwargs={'homework_id': 16}))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('watch_videoclase', kwargs={'homework_id': 16}))
        self.assertEqual(response.status_code, 302)

    def test_student_tipo_homework_permissions(self):
        self.client.login(username='student1', password='alumno')
        response = self.client.get(reverse('watch_videoclase', kwargs={'homework_id': 10}))
        self.assertEqual(response.status_code, 302)

    def test_watch_videoclases_get_data(self):
        self.client.login(username='student1', password='alumno')
        response = self.client.get(reverse('watch_videoclase', kwargs={'homework_id': 16}))
        student = User.objects.get(username='student1').student
        homework = Homework.objects.get(id=16)
        group = GroupOfStudents.objects.get(homework=homework, students=student)
        self.assertEqual(response.context['group'], group)


class VideoClaseModelMethodsTestCase(TestCase):
    fixtures = all_fixturues

    def test_percentage_like(self):
        vc = VideoClase.objects.get(id=35)
        like = StudentEvaluations.objects.filter(videoclase=vc, value=1).count()
        total = StudentEvaluations.objects.filter(videoclase=vc).count()
        percentage = int(round(100 * like / total))
        self.assertEqual(vc.percentage_like(), percentage)

    def test_percentage_neutral(self):
        vc = VideoClase.objects.get(id=35)
        neutral = StudentEvaluations.objects.filter(videoclase=vc, value=0).count()
        total = StudentEvaluations.objects.filter(videoclase=vc).count()
        percentage = int(round(100 * neutral / total))
        self.assertEqual(vc.percentage_neutral(), percentage)

    def test_percentage_dont_like(self):
        vc = VideoClase.objects.get(id=35)
        dont_like = StudentEvaluations.objects.filter(videoclase=vc, value=-1).count()
        total = StudentEvaluations.objects.filter(videoclase=vc).count()
        percentage = int(round(100 * dont_like / total))
        self.assertEqual(vc.percentage_dont_like(), percentage)

    def test_members_percentage_like(self):
        vc = VideoClase.objects.get(id=35)
        others_vc = VideoClase.objects.filter(group__homework=vc.group.homework) \
            .exclude(id=vc.id)
        like = StudentEvaluations.objects.filter(author__in=vc.group.students.all(),
                                                     value=1,
                                                     videoclase__in=others_vc).count()
        total = StudentEvaluations.objects.filter(author__in=vc.group.students.all(),
                                                  videoclase__in=others_vc).count()
        percentage = int(round(100 * like / total))
        self.assertEqual(vc.members_percentage_like(), percentage)

    def test_members_percentage_neutral(self):
        vc = VideoClase.objects.get(id=35)
        others_vc = VideoClase.objects.filter(group__homework=vc.group.homework) \
            .exclude(id=vc.id)
        neutral = StudentEvaluations.objects.filter(author__in=vc.group.students.all(),
                                                   value=0,
                                                   videoclase__in=others_vc).count()
        total = StudentEvaluations.objects.filter(author__in=vc.group.students.all(),
                                                  videoclase__in=others_vc).count()
        percentage = int(round(100 * neutral / total))
        self.assertEqual(vc.members_percentage_neutral(), percentage)

    def test_members_percentage_dont_like(self):
        vc = VideoClase.objects.get(id=35)
        others_vc = VideoClase.objects.filter(group__homework=vc.group.homework) \
            .exclude(id=vc.id)
        dont_like = StudentEvaluations.objects.filter(author__in=vc.group.students.all(),
                                                        value=-1,
                                                        videoclase__in=others_vc).count()
        total = StudentEvaluations.objects.filter(author__in=vc.group.students.all(),
                                                  videoclase__in=others_vc).count()
        percentage = int(round(100 * dont_like / total))
        self.assertEqual(vc.members_percentage_dont_like(), percentage)

    def test_percentage_answers_correct(self):
        vc = VideoClase.objects.get(id=35)
        correct = StudentResponses.objects \
            .filter(videoclase=vc, answer=vc.correct_alternative) \
            .count()
        total = StudentResponses.objects.filter(videoclase=vc).count()
        percentage = int(round(100 * correct / total))
        self.assertEqual(vc.percentage_answers_correct(), percentage)

    def test_percentage_answers_wrong(self):
        vc = VideoClase.objects.get(id=35)
        wrong = StudentResponses.objects \
            .filter(videoclase=vc, answer=vc.alternative_2) \
            .count()
        wrong += StudentResponses.objects \
            .filter(videoclase=vc, answer=vc.alternative_3) \
            .count()
        total = StudentResponses.objects.filter(videoclase=vc).count()
        percentage = int(round(100 * wrong / total))
        self.assertEqual(vc.percentage_answers_wrong(), percentage)

    def test_members_and_answers(self):
        vc = VideoClase.objects.get(id=35)
        a = vc.group.students.all()[0]
        homework = vc.group.homework
        homework_base = vc.group.homework
        if homework.homework_to_evaluate is not None:
            homework = homework.homework_to_evaluate
        answers = StudentResponses.objects.filter(
            Q(videoclase__homework=homework) | Q(videoclase__homework=homework_base),
            student=a)
        correct = 0
        for r in answers:
            correct += r.answer == r.videoclase.correct_alternative
        wrong = 0
        for r in answers:
            wrong += r.answer == r.videoclase.alternative_2 \
                           or r.answer == r.videoclase.alternative_3
        result_dict = vc.members_and_answers()
        self.assertEqual(result_dict[0]['sum_correct'], correct)
        self.assertEqual(result_dict[0]['sum_wrong'], wrong)


class VideoclasesStudentTestCase(TestCase):
    fixtures = all_fixturues

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('videoclases_student', kwargs={'student_id': 1}))
        self.assertEqual(response.status_code, 200)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        response = self.client.get(reverse('videoclases_student', kwargs={'student_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('videoclases_student', kwargs={'student_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_videoclases_student_get_data(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('videoclases_student', kwargs={'student_id': 1}))
        student = Student.objects.get(id=1)
        groups = student.groupofstudents_set.exclude(videoclase__video=None).exclude(videoclase__video__exact='')
        pending_groups = student.groupofstudents_set.filter(
            Q(videoclase__video='') | Q(videoclase__video__isnull=True))
        vmerge = groups | pending_groups
        vmerge.order_by('-id')
        self.assertEqual(response.context['student'], student)
        self.assertEqual(list(response.context['groups']), list(vmerge))


class VideoclasesHomeworkTestCase(TestCase):
    fixtures = all_fixturues

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('videoclases_homework', kwargs={'homework_id': 1}))
        self.assertEqual(response.status_code, 200)

    def test_student_permissions(self):
        self.client.login(username='student', password='alumno')
        response = self.client.get(reverse('videoclases_homework', kwargs={'homework_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('videoclases_homework', kwargs={'homework_id': 1}))
        self.assertEqual(response.status_code, 302)

    def test_videoclases_homework_get_data(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('videoclases_homework', kwargs={'homework_id': 1}))
        homework = Homework.objects.get(id=1)
        self.assertEqual(response.context['homework'], homework)
        self.assertEqual(list(response.context['groups']), list(homework.groups.all()))
