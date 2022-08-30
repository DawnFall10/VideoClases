import datetime
import json
import os

from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models.aggregates import Count
from django.test import TestCase

from quality_control.utils import APIHomework
from videoclases.models.groupofstudents import GroupOfStudents
from videoclases.models.homework import Homework
from videoclases.models.video_clase import VideoClase

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

todos_los_fixtures = ['devgroups', 'devusers', 'devcourses', 'devstudents', 'devteachers',
    'devschool', 'devhomeworks', 'devgroupsstudent', 'devvideoclasesevaluando', 'devfinalscores',
    'devstudentsresponses', 'devstudentevaluations']
this_year = datetime.date.today().year


class ApiPermissionsTestCase(TestCase):
    fixtures = todos_los_fixtures

    def test_student_has_api_permissions(self):
        self.client.login(username='student2', password='alumno')
        response = self.client.get(reverse('api_get_videoclase', kwargs={'pk':10}))
        self.assertEqual(response.status_code, 200)

    def test_teacher_permissions(self):
        self.client.login(username='profe', password='profe')
        response = self.client.get(reverse('api_get_videoclase', kwargs={'pk':10}))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_permissions(self):
        response = self.client.get(reverse('api_get_videoclase', kwargs={'pk':10}))
        self.assertEqual(response.status_code, 302)

    def test_student_does_not_have_api_permissions(self):
        self.client.login(username='student1', password='alumno')
        response = self.client.get(reverse('api_get_videoclase', kwargs={'pk':2}))
        self.assertEqual(response.status_code, 302)

    def test_student_api_does_not_exist_permissions(self):
        self.client.login(username='student1', password='alumno')
        response = self.client.get(reverse('api_get_videoclase', kwargs={'pk':1234567}))
        self.assertEqual(response.status_code, 404)

    def test_template_get_random_group_data(self):
        self.client.login(username='student2', password='alumno')
        response = self.client.get(reverse('api_get_videoclase', kwargs={'pk': 10}))
        homework = Homework.objects.get(id=10)
        user = User.objects.get(username='student2')

        # random group, with as less revision as possible
        group_student = GroupOfStudents.objects.get(students=user.student, homework=homework)
        groups = GroupOfStudents.objects.filter(homework=homework).exclude(id=group_student.id) \
            .exclude(videoclase__video__isnull=True) \
            .exclude(videoclase__video__exact='') \
            .annotate(revision=Count('videoclase__answers')) \
            .order_by('revision', '?')
        result = json.loads(response.content.decode("utf-8"))
        videoclase_id = result['videoclase_id']
        videoclase = VideoClase.objects.get(id=videoclase_id)
        self.assertTrue(groups[0].revision <= groups.reverse()[0].revision)

        # alternativas to question in content
        alternativas = [videoclase.correct_alternative,
                        videoclase.alternative_2,
                        videoclase.alternative_3]
        alternativas.sort()
        result['alternativas'].sort()
        self.assertEqual(result['alternativas'], alternativas)

        # videoclase question not responded before
        self.assertFalse(videoclase.answers.filter(student=user.student))
