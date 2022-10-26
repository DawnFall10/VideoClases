from django.contrib.auth.models import User
from django.db import models

from videoclases.models.course import Course
from videoclases.models.school import School


class Organizer(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    courses = models.ManyToManyField(Course, blank=True)
    changed_password = models.BooleanField(default=True)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name

    def get_full_name(self):
        return self.user.get_full_name()

    def display_courses(self):
        return ', '.join([
            u'{0} - {1}'.format(course.name, course.year)
            for course in self.courses.all()])

    display_courses.short_description = 'Courses'
    get_full_name.short_description = 'Name'
    get_full_name.admin_order_field = 'user__last_name'
    display_courses.admin_order_field = 'courses'

    class Meta:
        verbose_name = 'Organizador'
        verbose_name_plural = 'Organizadores'
