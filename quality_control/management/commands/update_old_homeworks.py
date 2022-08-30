from django.core.management.base import BaseCommand, CommandError
from videoclases.models.homework import Homework
from videoclases.models.teacher import Teacher
from quality_control.utils import update_old_model_evaluations


class Command(BaseCommand):
    help = 'Update old homework model'

    def handle(self, *args, **options):
        teacher = Teacher.objects.get(id=2)
        for hw in Homework.objects.filter(scala__isnull=True):
            self.stdout.write(self.style.SUCCESS("Updating HW: {0}, {1}".format(hw, hw.course.year)))
            update_old_model_evaluations(hw, teacher)
