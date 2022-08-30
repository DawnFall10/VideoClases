from statistics import *
from functools import reduce
from scipy.spatial import distance
from decimal import Decimal
import numpy as np
import pyexcel

from django.shortcuts import get_object_or_404

from quality_control.models.quality_control import QualityControl
from quality_control.models.quality_item import QualityItem
from quality_control.models.quality_score import QualityScore
from videoclases.models.evaluation.criterion import Criterion
from videoclases.models.evaluation.criterion_response import CriterionResponse
from videoclases.models.evaluation.criteria_by_teacher import CriteriaByTeacher
from videoclases.models.evaluation.scale import Scale
from videoclases.models.groupofstudents import GroupOfStudents
from videoclases.models.homework import Homework
from videoclases.models.student import Student
from videoclases.models.teacher import Teacher
from videoclases.models.student_evaluations import StudentEvaluations
from videoclases.models.video_clase import VideoClase
from decimal import InvalidOperation
from django.db.models import Count


def calculate_score(evaluations):
    if len(evaluations) > 0:

        def funcion_to_reduce(res, curr):
            for element in curr:
                if element['id'] in res:
                    res[element['id']]['scores'].append(element['value'])
                else:
                    res[element['id']] = {
                        'id': element['id'],
                        'name': element['name'],
                        'scores': [element['value']]
                    }
            return res

        response = reduce(funcion_to_reduce, evaluations, {})

        def add_statistics(value, decimals=3):
            element = dict(value)
            del element['scores']
            scores = value.get('scores', [])
            if len(scores) > 0:
                element['avg'] = round(mean(scores), decimals)
                element['min_score'] = reduce(lambda x, y: x if x < y else y, scores)
                element['max_score'] = reduce(lambda x, y: x if x > y else y, scores)
                element['number_evaluations'] = len(scores)
                try:
                    element['mode'] = mode(scores)
                except StatisticsError:
                    # not unique common value
                    element['mode'] = '-'
                if len(scores) < 2:
                    # not enough data to calculate
                    element['standar_desv'] = '-'
                    element['variance'] = '-'
                else:
                    element['standar_desv'] = round(stdev(scores), decimals)
                    element['variance'] = round(variance(scores), decimals)
            else:
                element['empty'] = True
            return element

        return list(map(add_statistics, response.values()))
    return []


def load_teacher_evaluations_from_xls(teacher: Teacher, homework: Homework, path_file: str, delete_previous_evaluations = False) -> None:
    """

    Create teacher evaluations for filter

    File Format:
    HEADERS
    ---------------------------------------------------
    Name Student | ...Criteria (one column by criteria)

    :param teacher: Teacher of evaluations
    :param homework: Homework to add evaluations
    :param path_file: Path of xls
    :return: None
    """
    sheet = pyexcel.get_sheet(file_name=path_file)
    arr = sheet.to_array()
    criteria_xls = arr.pop(0) # removing headers
    criteria_xls.pop(0) # removing student name column
    students = homework.course.students
    criteria_base = homework.get_criteria_list()
    criteria_base_arr = list(map(lambda x: x["name"], criteria_base))
    print(criteria_base_arr)
    if len(arr) > students.count():
        raise Exception("XLS cannot have more evaluations that students")
    if len(criteria_base) != len(criteria_xls) or\
            all(criteria_base_arr.index(name) for name in criteria_xls):
        raise Exception("Cannot match criteria")

    control = None
    try:
        control, created = QualityControl.objects.get_or_create(homework=homework)
    except Exception:
        control = QualityControl()
        control.save()
        control.homework.add(homework)
    if delete_previous_evaluations:
        items = control.list_items.all()
        for item in items:
            item.delete()

    groups = GroupOfStudents.objects.filter(homework=homework)
    added_groups = []
    for evaluation_data in arr:
        name = evaluation_data.pop(0).split(", ") # Last Name, First name

        # Trying to find student
        try:
            student = students.get(user__last_name=name[0])
            group = groups.get(students=student)
        except Exception as e:
            print(e)
            print("\n --- \n")
            print("Student: {0}".format(name[0]))
            continue
        # import ipdb; ipdb.set_trace()
        if group in added_groups:
            continue # not process groups of more than 1 students
        else:
            added_groups.append(group)

        item, created = QualityItem.objects.get_or_create(
            videoclase=group.videoclase,
            teacher=teacher
        )
        if created:
            item.save()
            control.list_items.add(item)
            control.save()
        item.save()

        # Parsing list
        for i in range(0, len(criteria_xls)):
            criteria_index = criteria_base_arr.index(criteria_xls[i])
            criteria = criteria_base[criteria_index]
            score_value = evaluation_data[i]
            if score_value is not None and score_value != "":
                score, created =item.score_check.get_or_create(
                    criteria=Criterion.objects.get(id=criteria['id']),
                    teacher=teacher,
                )
                if created:
                    score.save()
                item.score_check.add(score)
                score.score = score_value
                score.save()
            else:
                print("Skipping criteria: {0} - Student: {1}".format(criteria["name"], student))


def update_old_model_evaluations(homework: Homework, teacher: Teacher) -> None:
    """
    Only fix for old evaluations
    :param homework: Homework
    :param teacher: Teacher
    :return: None
    """

    # Updating Homework model

    old_criteria = homework.get_criteria_list()
    if homework.scala is not None:
        raise Exception("Has new model")
    # Creating Scala
    homework.scala= Scale.objects.get(pk=1)
    teacher_criteria = CriteriaByTeacher.objects.create(
        name="Auto Update of criteria",
        teacher=teacher)
    teacher_criteria.save()
    homework.criteria.add(teacher_criteria)
    for criteria in old_criteria:
        name = criteria.get("name", "")
        new_criteria = Criterion.objects.create(value=name)
        new_criteria.save()
        criteria["new_criteria"] = new_criteria

        teacher_criteria.criteria.add(new_criteria)
    homework.save()

    # Updating StudentsEvaluations

    evaluations = StudentEvaluations.objects.filter(videoclase__homework=homework)

    for e in evaluations:
        for criteria in old_criteria:

            # I don't find better solution
            value = None
            name = criteria["name"]
            if name == "Originalidad":
                value = e.originality
                e.originality = None
            elif name == "Formato":
                value = e.format
                e.format = None
            elif name == "Licencias":
                value = e.copyright
                e.copyright = None
            elif name == "Tema":
                value = e.theme
                e.theme = None
            elif name == "Pedagogía":
                value = e.pedagogical
                e.pedagogical = None
            elif name == "Ritmo":
                value = e.rythm
                e.rythm = None

            new_response = CriterionResponse.objects.create(
                value=value, criteria= criteria["new_criteria"])
            new_response.save()
            e.criteria.add(new_response)
        e.save()


class APIHomework:
    def __init__(self, homework_id):
        self.homework = get_object_or_404(Homework, id=homework_id)
        self.students = Student.objects.filter(groupofstudents__homework__pk=45)

        self.studentsDict = dict()

        self.videoclases = VideoClase.objects.filter(homework=self.homework, video__isnull=False)

        self.videoclasesDict = dict()

        self.evaluations = StudentEvaluations.objects.filter(videoclase__homework=self.homework)

        self.__build()

    def get_students_evaluations(self):
        result = list()
        groups = GroupOfStudents.objects.filter(homework=self.homework)\
            .prefetch_related('students')\
            .select_related('videoclase')

        criteria = self.homework.get_criteria_list()
        score_base = criteria.copy()
        for s in score_base:
            s['empty'] = True
        for group in groups:
            v = self.videoclasesDict.get(group.videoclase.id, None)
            score = score_base.copy()
            if v:
                evaluations = [self.studentsDict[id]['videos'][group.videoclase.id]['evaluation'].get_evaluation()
                               for id in v['students']]
                if len(evaluations) > 0:
                    score = calculate_score(evaluations)

            videoclases_dict = {
                         'url': group.videoclase.video if group.videoclase.video is not None else "-",
                         'question': group.videoclase.question,
                         'response': group.videoclase.correct_alternative,
                         'date': group.videoclase.upload_students.strftime(
                             "%d-%m-%Y %H:%M") if group.videoclase.upload_students else None
                     }
            final_score = reduce(lambda x, y: x+y, list(map(lambda x: x.get('avg', 0.0), score)))
            for s in group.students.all():
                result.append(
                    {'criteria': score,
                     'final_score': final_score,
                     'student': {'first_name': s.user.first_name, 'last_name': s.user.last_name},
                     'videoclase': videoclases_dict
                     }
                )
        return {"headers_criteria": criteria, "results": result}

    def get_teacher_evaluations(self):
        videoclases = VideoClase.objects.filter(homework=self.homework).prefetch_related('qualityItemList',
                                                                                         'group__students')
        criteria = self.homework.get_criteria_list()
        score_base = criteria.copy()
        data = list()
        for v in videoclases:
            score = score_base.copy()
            videoclase_info = {
                "videoclase_id": v.id,
                'criteria': score,
                'students': [{'first_name': s.user.first_name, 'last_name': s.user.last_name}
                             for s in v.group.students.all()],
                'videoclase': {
                    'id': v.id,
                    'url': v.video,
                    'question': v.question,
                    'response': v.correct_alternative,
                    'date': v.upload_students.strftime(
                        "%d-%m-%Y %H:%M") if v.upload_students else None
                }

            }
            if v.qualityItemList.count() > 0:
                videoclase_info['criteria'] = calculate_score([e.get_evaluation() for e in v.qualityItemList.all()])
            data.append(videoclase_info)

        return {
            'headers': criteria,
            'evaluations': data
        }

    def get_students_evaluations_filtered(self, number_evaluations=None):
        results = dict()
        videoclase = VideoClase.objects.filter(homework=self.homework).\
            prefetch_related('qualityItemList', 'group__students') \
            .annotate(gcount=Count('evaluations')).filter(gcount__gt=0)\
            .order_by('-qualityItemList')
        # import ipdb; ipdb.set_trace()
        students = dict()
        criteria = self.homework.get_criteria_list()
        score_base = criteria.copy()
        valid_students = []
        for s in score_base:
            s['empty'] = True
        for not_used in range(1):
            for v in videoclase:
                ############ Load data ############
                arr_to_compare = np.array([])
                arr_teacher_evaluations = None
                arr_student_evaluations = None

                student_evaluations = self.evaluations.filter(videoclase=v)

                if v.qualityItemList.count() > 0:
                    # CASE: EXISTING TEACHER EVALUATIONS
                    arr_teacher_evaluations = [quailty_item.get_score() for quailty_item in v.qualityItemList.all()]
                    arr_teacher_evaluations = self.__normalize_arr(arr_teacher_evaluations)


                # CASE: ONLY STUDENTS EVALUATIONS
                dict_videoclases = self.videoclasesDict.get(v.pk, {'students':[]})
                list_students = dict_videoclases['students']

                for id_student in list_students:
                    dict_student = students.get(id_student, None)
                    if dict_student is None:
                        continue
                    if dict_student and dict_student['valid'] >= dict_student['invalid']*2:
                        valid_students.append(id_student)
                arr_student_evaluations = [e.get_score() for e in student_evaluations.filter(author__in=valid_students)]
                arr_student_evaluations = self.__normalize_arr(arr_student_evaluations)
                if arr_teacher_evaluations is not None and arr_student_evaluations is not None:
                        arr_to_compare = arr_teacher_evaluations * Decimal(0.65) + arr_student_evaluations* Decimal(0.35)
                elif arr_teacher_evaluations is not None:
                    arr_to_compare = arr_teacher_evaluations
                elif arr_student_evaluations is not None:
                    arr_to_compare = arr_student_evaluations
                else:
                    continue  # we don't have evaluations

                valid_evaluations = []
                arr_len = len(arr_to_compare)

                if arr_len > 0:
                    ############ FILTER ############
                    for e in student_evaluations:
                        score = np.array(e.get_score())
                        try:
                            score_norm = score / np.linalg.norm(score)
                        except InvalidOperation:
                            continue

                        diff = distance.euclidean(arr_to_compare,score_norm)
                        # print( "Distance: ${0}".format(diff))
                        data = students.get(e.author, {'invalid': 0, 'valid': 0})

                        val_to_compare = 0.43
                        if diff < val_to_compare: ## <--- EXPERIMENTAL VALUE ##

                            # Valid Student
                            valid_evaluations.append(e.get_evaluation())
                            data['valid'] += 1
                        else:
                            data['invalid'] += 1
                        students[e.author.id] = data
                elif len(students) == 0:
                    valid_evaluations = [e.get_evaluation() for e in student_evaluations]

                ############ FORMAT RESPONSE ############
                score = calculate_score(valid_evaluations)
                if len(score) == 0:
                    score = score_base.copy()
                evaluation_result = self.__generate_evaluation_result(v, score)
                results[v.id] = evaluation_result
        import itertools
        flat = itertools.chain.from_iterable(results.values())
        return {"headers_criteria": criteria, "results": list(flat) }

    def get_video_for_teacher_evaluation(self, teacher):
        items = []
        control = None
        try:
            control = QualityControl.objects.get(homework=self.homework)
        except QualityControl.DoesNotExist:
            pass

        if control and control.list_items.count() > 0:
            items = control.list_items.filter(
                teacher=teacher).prefetch_related('videoclase')
        videoclases = [i.videoclase for i in items]

        def filter_queryset(prev, curr):
            if curr['video'] not in videoclases and len(curr['students']) > prev['count']:
                return {
                    'videoclase': curr['video'],
                    'count': len(curr['students'])}
            return prev

        queryset = reduce(filter_queryset, self.videoclasesDict.values(), {'count': 0})
        return queryset['videoclase'] if queryset['count'] > 0 else None

    def __normalize_arr(self, arr):
        arr_len = len(arr)
        arr_to_compare = arr.copy()
        if arr_len > 1:
            arr_to_compare = np.array(arr_to_compare)
            arr_to_compare = arr_to_compare.mean(axis=0)
        elif arr_len == 1:
            arr_to_compare = np.array(arr_to_compare[0])
        else:
            return None

        try:
            arr_to_compare = arr_to_compare / np.linalg.norm(arr_to_compare)
        except InvalidOperation:
            return None
        return arr_to_compare

    def __build(self):
        for v in self.videoclases:
            self.videoclasesDict[v.pk] = {
                'students': [],
                'video': v
            }
        for e in self.evaluations:
            d = self.studentsDict.get(e.author.pk, {
                'student': e.author,
                'videos': dict()
            })
            d['videos'][e.videoclase.pk] = {'evaluation': e}
            self.studentsDict[e.author.pk] = d

            f = self.videoclasesDict[e.videoclase.pk]
            f['students'].append(e.author.pk)

    def __generate_evaluation_result(self, v: VideoClase, score):
        videoclases_dict = {
            'url': v.video if v.video is not None else "-",
            'question': v.question,
            'response': v.correct_alternative,
            'date': v.upload_students.strftime(
                "%d-%m-%Y %H:%M") if v.upload_students else None
        }
        result = []
        final_score = 0.0
        if len(score) > 0:
            final_score = reduce(lambda x, y: x + y, list(map(lambda x: x.get('avg', 0.0), score)))

        if v.group == None:
            result.append(
                {'criteria': score,
                 'final_score': final_score + Decimal(1.0) if final_score > 0 else None,
                 'student': {'first_name': "Test", 'last_name': "Test"},
                 'videoclase': videoclases_dict,
                 'videoclase_id': v.id,
                 "group_number": None
                 })
        else:
            for s in v.group.students.all().select_related('user'):
                result.append(
                    {'criteria': score,
                     'final_score': final_score + Decimal(1.0) if final_score > 0 else None,
                     'student': {'first_name': s.user.first_name, 'last_name': s.user.last_name},
                     'videoclase': videoclases_dict,
                     'videoclase_id': v.id,
                     "group_number": str(v.group.number)
                     })
        return result