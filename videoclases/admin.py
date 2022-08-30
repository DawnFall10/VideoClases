# coding=utf-8
from django.contrib import admin

from videoclases.models.boolean_parameters import BooleanParameters
from videoclases.models.course import Course
from videoclases.models.evaluation.criterion import Criterion
from videoclases.models.evaluation.criteria_by_teacher import CriteriaByTeacher
from videoclases.models.evaluation.scale import Scale
from videoclases.models.evaluation.scale_value import ScaleValue
from videoclases.models.final_scores import FinalScores
from videoclases.models.groupofstudents import GroupOfStudents
from videoclases.models.homework import Homework
from videoclases.models.pedagogical_questions.alternative import Alternative
from videoclases.models.pedagogical_questions.pedagogical_questions import PedagogicalQuestions
from videoclases.models.pedagogical_questions.pedagogical_questions_answers import PedagogicalQuestionsAnswers
from videoclases.models.pedagogical_questions.question import Question
from videoclases.models.pedagogical_questions.response import Response
from videoclases.models.school import School
from videoclases.models.student import Student
from videoclases.models.student_evaluations import StudentEvaluations
from videoclases.models.student_responses import StudentResponses
from videoclases.models.teacher import Teacher
from videoclases.models.video_clase import VideoClase


@admin.register(Student)
class StudenAdmin(admin.ModelAdmin):
    list_filter = ['courses']
    list_display = ('user', 'get_full_name', 'display_courses', 'changed_password')


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_filter = ['courses', 'school']
    list_display = ('user', 'get_full_name', 'display_courses', 'changed_password')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_filter = ['school', 'year']
    list_display = ('name', 'school', 'year')


@admin.register(VideoClase)
class VideoClaseAdmin(admin.ModelAdmin):
    readonly_fields = ('group',)
    list_filter = ['homework', 'homework__course']
    list_display = ('group_number', 'homework', 'upload_students', 'video')
    list_per_page = 20


@admin.register(FinalScores)
class FinalScoresAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('id', 'group_number', 'get_homework', 'get_course')
    list_filter = ['group__homework', 'group__homework__course']


@admin.register(StudentEvaluations)
class StudentEvaluationsAdmin(admin.ModelAdmin):
    readonly_fields = ('videoclase', 'author',
                       'created', 'criteria')

    list_display = ('author', 'videoclase','get_score')
    list_filter = ['videoclase__homework', 'videoclase__homework__course', 'videoclase']
    list_per_page = 30


@admin.register(StudentResponses)
class StudentResponsesAdmin(admin.ModelAdmin):
    readonly_fields = ('videoclase', 'student', 'answer')
    list_display = ('student', 'display_homework', 'is_correct')
    list_filter = ['videoclase__homework__course', 'videoclase__homework']


@admin.register(GroupOfStudents)
class GroupOfStudentsAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('number', 'homework', 'display_students')
    list_filter = ['homework', 'homework__course']

    def get_form(self, request, obj=None, **kwargs):
        form = super(GroupOfStudentsAdmin, self).get_form(request, obj, **kwargs)
        if obj is not None:
            course = obj.homework.course
            form.base_fields['homework'].queryset = Homework.objects.filter(course=course)
            form.base_fields['students'].queryset = Student.objects.filter(courses=course)
        return form


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'date_upload', 'date_evaluation', 'homework_to_evaluate')
    list_filter = ['course', 'course__year']


@admin.register(Criterion)
class CriteriaAdmin(admin.ModelAdmin):
    list_display = ('value', 'description')


@admin.register(PedagogicalQuestions)
class PedagogicalQuestionsAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('title', 'homework', 'delta_time')
    list_filter = ['homework', 'homework__course']


@admin.register(PedagogicalQuestionsAnswers)
class PedagogicalQuestionsAnswersAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('student', 'test', 'get_course', 'state')
    list_filter = ['state', 'test', 'test__homework', 'test__homework__course']

    def get_form(self, request, obj=None, **kwargs):
        form = super(PedagogicalQuestionsAnswersAdmin, self).get_form(request, obj, **kwargs)
        if obj is not None:
            course = obj.test.homework.course
            form.base_fields['students'].queryset = Student.objects.filter(courses=course)
        return form


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    readonly_fields = ('question', 'answer')
    list_per_page = 20
    list_display = ('question', 'answer')


admin.site.register(BooleanParameters)
admin.site.register(School)
admin.site.register(Question)
admin.site.register(Alternative)

admin.site.register(CriteriaByTeacher)
admin.site.register(Scale)
admin.site.register(ScaleValue)
