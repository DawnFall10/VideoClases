from functools import reduce
from django.core.management.base import BaseCommand

from quality_control.models.quality_item import QualityItem
from videoclases.models.homework import Homework
from videoclases.models.student_evaluations import StudentEvaluations
import pyexcel as pe
from pyexcel._compact import OrderedDict


class Command(BaseCommand):
    help = "Create a xls with a homework evaluation"

    def handle(self, *args, **options):
        for hw in Homework.objects.filter(course__year=2022):
            print("Procesing hw: {0}".format(hw))

            evaluations = (
                StudentEvaluations.objects.filter(videoclase__homework=hw)
                .exclude(videoclase__group__number__isnull=True)
                .order_by("videoclase__group__number")
            )
            raw_data = OrderedDict()
            for e in evaluations:
                id = e.videoclase.group.number
                score = reduce((lambda x, y: x + y), e.get_score()) + 1
                name = "Grupo {0}".format(id)
                if name not in raw_data:
                    raw_data[name] = []
                raw_data[name].append(float(score))

            teacher_evaluations_raw = (
                QualityItem.objects.filter(videoclase__homework=hw)
                .exclude(videoclase__group__number__isnull=True)
                .order_by("videoclase__group__number")
            )
            teacher_evaluations = list(
                map(
                    lambda e: float(reduce((lambda x, y: x + y), e.get_score()) + 1),
                    teacher_evaluations_raw,
                )
            )
            labels_teacher_evaluations = [
                "Grupo {0}".format(e.videoclase.group.number)
                for e in teacher_evaluations_raw
            ]

            raw_data_teacher = OrderedDict(
                zip(labels_teacher_evaluations, teacher_evaluations)
            )
            print("++++++++++++++")
            print("++++++++++++++")
            print(raw_data_teacher)
            print(labels_teacher_evaluations)
            print(teacher_evaluations)
            print("++++++++++++++")
            print("++++++++++++++")
            sheet1 = pe.get_sheet(adict=raw_data)
            # sheet2 = pe.get_sheet(adict=raw_data_teacher)
            book = pe.Book({"Alumnos": sheet1.to_array()})
            book.save_as(
                "raw-evaluations-{0}-{1}-{2}.xlsx".format(
                    hw.course.year, hw.course.name, hw.title
                )
            )
