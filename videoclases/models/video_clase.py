# coding=utf-8
from urllib.parse import urlparse, parse_qs

from django.db import models
from django.db.models import Q
from django.db.models.functions import Coalesce

from videoclases.models.groupofstudents import GroupOfStudents


class VideoClase(models.Model):
    group = models.OneToOneField(GroupOfStudents, null=True, blank=True, on_delete=models.CASCADE)
    video = models.CharField(max_length=100, blank=True, null=True)
    question = models.CharField(max_length=100, blank=True, null=True)
    correct_alternative = models.CharField(max_length=100, blank=True, null=True)
    alternative_2 = models.CharField(max_length=100, blank=True, null=True)
    alternative_3 = models.CharField(max_length=100, blank=True, null=True)
    upload_students = models.DateTimeField(blank=True, null=True)
    homework = models.ForeignKey("Homework", blank=True, null=True, on_delete=models.CASCADE)

    def group_number(self):
        if self.group:
            return self.group.number
        return -1

    group_number.short_description = '# de grupo'
    group_number.admin_order_field = 'group__number'

    # StudentEvaluations
    def compute_percentage_evaluations(self, value):
        conjunto = self.evaluations.filter(videoclase=self, value=value).count()
        total = self.evaluations.filter(videoclase=self).count()
        return int(round(100 * conjunto / total)) if total else 0

    def percentage_like(self):
        return self.compute_percentage_evaluations(1)

    def percentage_neutral(self):
        return self.compute_percentage_evaluations(0)

    def percentage_dont_like(self):
        return self.compute_percentage_evaluations(-1)

    def sum_like(self):
        return self.evaluations.filter(videoclase=self, value=1).count()

    def sum_neutral(self):
        return self.evaluations.filter(videoclase=self, value=0).count()

    def sum_dont_like(self):
        return self.evaluations.filter(videoclase=self, value=-1).count()

    def members_sum_percentage_evaluations(self, value):
        from videoclases.models.student_evaluations import StudentEvaluations
        others_vc = VideoClase.objects.filter(group__homework=self.group.homework) \
            .exclude(id=self.id)
        evaluations = StudentEvaluations.objects.filter(author__in=self.group.students.all(),
                                                     value=value,
                                                     videoclase__in=others_vc).count()
        total = StudentEvaluations.objects.filter(author__in=self.group.students.all(),
                                                  videoclase__in=others_vc).count()
        return int(round(100 * evaluations / total)) if total else 0

    def members_percentage_like(self):
        return self.members_sum_percentage_evaluations(1)

    def members_percentage_neutral(self):
        return self.members_sum_percentage_evaluations(0)

    def members_percentage_dont_like(self):
        return self.members_sum_percentage_evaluations(-1)

    def compute_members_sum_votos(self, value):
        from videoclases.models.student_evaluations import StudentEvaluations
        otras_vc = VideoClase.objects.filter(group__homework=self.group.homework) \
            .exclude(id=self.id)
        return StudentEvaluations.objects.filter(author__in=self.group.students.all(),
                                                 value=value,
                                                 videoclase__in=otras_vc).count()

    def members_sum_like(self):
        return self.compute_members_sum_votos(1)

    def members_sum_neutral(self):
        return self.compute_members_sum_votos(0)

    def members_sum_dont_like(self):
        return self.compute_members_sum_votos(-1)

    # StudentResponses
    def compute_percentage_answers(self, answers):
        total_answer = 0
        for r in answers:
            total_answer += self.answers.filter(videoclase=self, answer=r).count()
        total = self.answers.filter(videoclase=self).count()
        return int(round(100 * total_answer / total)) if total else 0

    def percentage_answers_correct(self):
        return self.compute_percentage_answers([self.correct_alternative])

    def percentage_answers_wrong(self):
        return self.compute_percentage_answers([self.alternative_2, self.alternative_3])

    def sum_correct(self):
        return self.answers.filter(videoclase=self, answer=self.correct_alternative).count()

    def sum_wrong(self):
        answer = self.answers.filter(videoclase=self)
        return answer.count() - answer.filter(answer=self.correct_alternative).count()

    def members_and_answers(self):
        from videoclases.models.student_responses import StudentResponses
        students = self.group.students.all()
        students_array = []
        for a in students:
            student_dict = {}
            homework_base = self.group.homework
            homework = homework_base
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
            student_dict['user_id'] = a.user.id
            student_dict['name'] = a.user.first_name + ' ' + a.user.last_name
            student_dict['sum_correct'] = correct
            student_dict['sum_wrong'] = wrong
            total = correct + wrong
            student_dict['percentage_correct'] = int(round(100 * correct / total)) if total else 0
            student_dict['percentage_wrong'] = int(round(100 * wrong / total)) if total else 0
            students_array.append(student_dict)
        return students_array

    def others_answers(self):
        from videoclases.models.student_responses import StudentResponses
        correct = StudentResponses.objects.filter(
            videoclase=self,
            answer=self.correct_alternative).count()
        wrong = StudentResponses.objects.filter(
            videoclase=self) \
            .filter(Q(answer=self.alternative_2) | Q(answer=self.alternative_3)) \
            .count()
        return_dict = {}
        return_dict['correct'] = correct
        return_dict['wrong'] = wrong
        return return_dict

    # DEPRECATED, use next function
    def get_multiple_criteria_score(self):
        from videoclases.models.student_evaluations import StudentEvaluations
        from django.db.models import Avg
        evaluations = StudentEvaluations.objects.filter(videoclase=self)
        result = evaluations.aggregate(
            format=Coalesce(Avg('format'), 0),
            copyright=Coalesce(Avg('copyright'), 0),
            theme=Coalesce(Avg('theme'), 0),
            pedagogical=Coalesce(Avg('pedagogical'), 0),
            rythm=Coalesce(Avg('rythm'), 0),
            originality=Coalesce(Avg('originality'), 0)
        )
        try:
            result['total'] = sum(result.values()) + 1
        except TypeError:
            result['total'] = ''
        return result

    # new version
    def get_score_criteria(self):
        from django.db.models import Avg
        return self.evaluations.exclude(criterias__isnull=True) \
            .values('criteria__criteria__value').aggregate(value=Coalesce(Avg('criteria__value'), 0))

    @staticmethod
    def process_youtube_default_link(link):
        if 'youtu.be/' in link:
            video_id = link.split('youtu.be/', 1)[1]
            return 'https://www.youtube.com/embed/' + str(video_id), True
        url_data = urlparse(link)
        query = parse_qs(url_data.query)
        try:
            video_id = query['v'][0]
            return 'https://www.youtube.com/embed/' + str(video_id), True
        except:
            return None, False

    def save(self, *args, **kwargs):
        if self.video:
            link, success = self.process_youtube_default_link(self.video)
            if success:
                self.video = link
        if self.homework is None and self.group is not None:
            self.homework = self.group.homework

        super(VideoClase, self).save(*args, **kwargs)

    def __str__(self):
        if self.homework:
            return 'Curso: ' + self.homework.course.name + '. Tarea: ' + \
                   self.homework.title + '. Grupo de Estudiantes: ' + str(self.group.number if self.group else "")
        else:
            return "{0}".format(self.id)
