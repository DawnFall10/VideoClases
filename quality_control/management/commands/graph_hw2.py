from functools import reduce
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from decimal import Decimal
from django.core.management.base import BaseCommand

from quality_control.models.quality_item import QualityItem
from videoclases.models.homework import Homework
from videoclases.models.student_evaluations import StudentEvaluations
from pyexcel._compact import OrderedDict
from django.db.models import Q


class Command(BaseCommand):
    help = 'Generate homework graph'

    def handle(self, *args, **opltions):

        for hw in Homework.objects.filter(course__id__in=[40, 41]):# id = 40 -> sección 1 ||| id = 41 -> sección 2
            print("Procesing hw: {0}".format(hw))
            #hw = Homework.objects.get(id=34)
            evaluations = StudentEvaluations.objects.filter(videoclase__homework=hw)\
                .exclude(Q(videoclase__group__number__isnull=True) | Q(videoclase__video__isnull=True)).order_by('videoclase__group__number')
            raw_data = OrderedDict()
            for e in evaluations:
                id = e.videoclase.group.number
                score = reduce((lambda x, y:x+y), e.get_score()) + 1
                name = id
                # name = "Grupo {0}".format(id)
                if score == 1: # Check 1 other day
                    # print("No score in evaluation :: {0}".format(e.id))
                    pass
                else:
                    if name not in raw_data:
                        raw_data[name] = []
                    raw_data[name].append(float(score))

            data = []
            labels = []
            data2 =  pd.DataFrame()
            for (key,value) in raw_data.items():
                data.append(value)
                labels.append(key)
                data2 = data2.append( pd.DataFrame({"Grupo": np.repeat(key, len(value)), "Nota": np.array(value),
                                                   "Legenda": "Evaluaciones de alumnos"}))

            teacher_evaluations_raw = QualityItem.objects.filter(videoclase__homework=hw)\
                .exclude(Q(videoclase__group__number__isnull=True) | Q(videoclase__video__isnull=True))\
                .order_by('videoclase__group__number')
            teacher_evaluations = list(map(lambda e: float(reduce((lambda x, y: x+y), e.get_score()) + 1),
                                           teacher_evaluations_raw))
            labels_teacher_evaluations = [e.videoclase.group.number for e in teacher_evaluations_raw]

            data3 = pd.DataFrame()
            for (key,value) in zip(labels_teacher_evaluations, teacher_evaluations):
                data3 = data3.append(pd.DataFrame({"Grupo": np.array([key]), "Nota": np.array(value),
                                                   "Legenda": "Evaluación docente"}))

            plt.text(-2, 7.4, '# Evaluaciones', horizontalalignment='left', size='small')
            pos = range(len(labels))
            total_evaluations = 0
            for tick, label in zip(pos, labels):
                plt.text(pos[tick], 7.4, len(data[tick]), horizontalalignment='center', size='medium',
                         weight='semibold')
                total_evaluations += len(data[tick])
            print("TOTAL EVALUATIONS:: {0}".format(total_evaluations))
            ax = sns.boxplot(x='Grupo', y='Nota', hue="Legenda", data=data2, color="skyblue")
            ax.set(ylim=(0, 7.2))
            sns.stripplot(x='Grupo', y='Nota', data=data2, color="orange", jitter=0.2, size=2.5)


            if len(data3.axes[1]) > 0:
                sns.stripplot(x='Grupo', y='Nota', hue="Legenda", data=data3, color="red", jitter=0.2, size=8.5, marker="D")
            plt.title("{2} | {1} | {0}".format(hw.course.year, hw.course.name, hw.title), loc="center", pad=20)

            plt.savefig("graphs/filtered_{0}-{1}-{2}.png".format(hw.course.year, hw.course.name, hw.title), loc="center", dpi=100)
            plt.close()
