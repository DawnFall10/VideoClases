from django.core.management.base import BaseCommand
from videoclases.models.homework import Homework
from videoclases.models.video_clase import VideoClase
from videoclases.models.student_evaluations import StudentEvaluations
import pyexcel as pe


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
            raw_data = [["alumno", "grupo"] + evaluations[0].get_score_name()]
            for e in evaluations:
                id = e.videoclase.group.number
                score = e.get_score()
                name = "Grupo {0}".format(id)
                raw_data.append([e.author.get_full_name(), name] + score)

            videoclases = VideoClase.objects.filter(homework=hw).order_by(
                "group__number"
            )

            videoclases_arr = [
                [
                    "Grupo",
                    "Alumnos",
                    "URL",
                    "Pregunta",
                    "Respuesta correcta",
                    "Opción 2",
                    "Opción 3",
                ]
            ] + [
                [
                    "Grupo {0}".format(v.group.number),
                    v.group.display_students(),
                    v.video,
                    v.question,
                    v.correct_alternative,
                    v.alternative_2,
                    v.alternative_3,
                ]
                for v in videoclases
            ]
            sheet1 = pe.get_sheet(array=raw_data)
            sheet2 = pe.get_sheet(array=videoclases_arr)

            book = pe.Book({"Alumnos": sheet1.to_array(), "Grupos": sheet2.to_array()})
            book.save_as(
                "raw-evaluations-groups-{0}-{1}-{2}.xlsx".format(
                    hw.course.year, hw.course.name, hw.title
                )
            )
