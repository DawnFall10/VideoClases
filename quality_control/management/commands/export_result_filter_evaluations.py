from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder
from functools import reduce
from django.core.management.base import BaseCommand, CommandError

from quality_control.models.quality_item import QualityItem
from quality_control.utils import APIHomework
from videoclases.models.course import Course
from videoclases.models.homework import Homework
from videoclases.models.student_evaluations import StudentEvaluations
import pyexcel as pe
from pyexcel._compact import OrderedDict
import json


class Command(BaseCommand):
    help = 'Create a xls with a homework evaluation'

    def handle(self, *args, **options):
        for hw in Homework.objects.filter(course__in=Course.objects.filter(year=2018).exclude(id=48)).order_by('course','id'):
        # for hw in Homework.objects.filter(course__id__in=[40, 41]).exclude(id__in=[47, 48]).order_by('course','id'):
            # hw = Homework.objects.get(id=46)
            # print("Procesing hw: {0}".format(hw))

            api = APIHomework(hw.id)
            results = api.get_students_evaluations_filtered()

            raw_dict_with_filter = dict()
            for r in results.get("results",[]):
                group_number = r.get("group_number", None)
                if group_number:
                    raw_dict_with_filter[group_number] = r.get("final_score", None)

            # print(json.dumps(raw_dict_with_filter, sort_keys=True, cls=DjangoJSONEncoder))
            #
            evaluations = StudentEvaluations.objects.filter(videoclase__homework=hw)\
                .exclude(videoclase__group__number__isnull=True)\
                .order_by('videoclase__group__number')
            raw_data = OrderedDict()
            for e in evaluations:
                id = e.videoclase.group.number
                score = reduce((lambda x, y:x+y), e.get_score()) + 1
                name = "Grupo {0}".format(id)
                if name not in raw_data:
                    raw_data[name] = []
                raw_data[name].append(float(score))

            teacher_evaluations_raw = QualityItem.objects.filter(videoclase__homework=hw)\
                .exclude(videoclase__group__number__isnull=True)\
                .order_by('videoclase__group__number')
            teacher_evaluations = list(map(lambda e: float(reduce((lambda x, y: x+y), e.get_score()) + 1),
                                           teacher_evaluations_raw))
            labels_teacher_evaluations = ["{0}".format(e.videoclase.group.number) for e in teacher_evaluations_raw]

            raw_data_teacher = OrderedDict(zip(labels_teacher_evaluations, teacher_evaluations))
            # print("++++++++++++++")
            # print("++++++++++++++")
            # print(raw_data_teacher)
            # print(labels_teacher_evaluations)
            # print(teacher_evaluations)
            # print("++++++++++++++")
            # print("++++++++++++++")
            # sheet1 = pe.get_sheet(adict=raw_data)
            # sheet2 = pe.get_sheet(adict=raw_data_teacher)
            # book = pe.Book({
            #     "Alumnos" : sheet1.to_array(),
            #     "Profesores": sheet2.to_array()
            # })
            # book.save_as("raw-filtered-evaluations-{0}-{1}-{2}.xlsx".format(hw.course.year, hw.course.name, hw.title))

            valid_filters = 0.0
            for (key, value) in raw_dict_with_filter.items():
                if value:
                    teacher_value = raw_data_teacher.get(key, None)
                    if teacher_value:
                        diff = abs(Decimal(teacher_value) - value)
                        print(hw.course.name, hw.title, key, diff)
                    if teacher_value and abs(Decimal(teacher_value) - value) <= 0.5:
                        valid_filters += 1
                        # print("Valid group {0}".format(key))
            # print("{0}-{1}-{2}: {3}%".format(hw.course.year, hw.course.name, hw.title,
            #                                  100*valid_filters/len(raw_dict_with_filter)))

            len_values = len(raw_dict_with_filter)
            if len_values > 0:
                print("Validos: {0}/{1} - {2}".format(valid_filters,len_values,1.0*valid_filters/len_values))
