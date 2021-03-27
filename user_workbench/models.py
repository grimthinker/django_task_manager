
from django.urls import reverse
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from .utils import *
import datetime as dt


class UserProfile(models.Model):
    """
    Model stores user data which using in this app
    Each UserProfile entity can correspond to only
    one User entity.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    name = models.CharField('Имя', max_length=50, db_index=True,  )
    second_name = models.CharField('Фамилия', max_length=50, db_index=True, )
    middle_name = models.CharField('Отчество', max_length=50, db_index=True, )
    roles = models.ManyToManyField('UserRole', blank=True, related_name='profile')
    chief = models.BooleanField(default=False)
    department = models.ForeignKey('Department',
                                    null=True,
                                    blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='workers') # Department in which that user is

    class Meta:
        ordering = ['second_name']

    def get_absolute_url(self):
        return reverse('user_detail_url', kwargs={'id': self.id})

    def __str__(self):
        try:
            self.slave_department
            department_name = " (гл. " + self.slave_department.name + ")"
        except ObjectDoesNotExist:
            department_name = ''
        return '{} {}.{}.'.format(self.second_name, self.name[0], self.middle_name[0]) + department_name


class Task(models.Model):

    NOT_STARTED = 'ns'
    NO_WORKERS = 'nw'
    IN_PROCESS = 'ip'
    HAS_SUBTASK = 'hs'
    CANCELED = 'cn'
    DONE = 'dn'
    CHECKED = 'ch'

    STATUSES = (
        (NO_WORKERS, 'Нет ответственных'),
        (NOT_STARTED, 'Не начато'),
        (IN_PROCESS, 'В процессе выполнения'),
        (HAS_SUBTASK, 'Есть подзадачи'),
        (DONE, 'Выполнено'),
        (CHECKED, 'Проверено'),
        (CANCELED, 'Отменено'),)

    def return_status(status, dict={i: j for (i, j) in STATUSES}):
        return dict[status]

    name = models.CharField(max_length=150, db_index=True)
    body = models.CharField(max_length=1000, blank=True, default='У этой задачи нет описания')
    creation_datetime = models.DateTimeField(auto_now_add=True)
    closure_datetime = models.DateTimeField(null=True, blank=True)
    author = models.ForeignKey('UserProfile', null=True, blank=True, on_delete=models.SET_NULL, related_name="created_tasks")
    responsible_users = models.ManyToManyField('UserProfile', related_name='assigned_tasks')
    status = models.CharField(max_length=2, choices=STATUSES, default=NOT_STARTED)
    justification = models.CharField(max_length=300, null=True, blank=True, )
    comment = models.CharField(max_length=600, null=True, blank=True, )
    deadline = models.DateTimeField(default=dt.datetime(9999, 1, 1, 1, 1, 1))
    super_task = models.ForeignKey('Task',
                                null=True,
                                blank=True,
                                on_delete=models.CASCADE,
                                related_name="sub_tasks") # Task of which that task is subtask

    class Meta:
        ordering = ['creation_datetime']

    def check_subtask_status(self):
        for t in self.sub_tasks.all():
            if t.status != 'dn':
                return False


    def calc_elap_time(self):
        now = dt.datetime.now()
        elsapsed_time = self.deadline - now
        d = str(elsapsed_time.days)
        h = str((elsapsed_time.seconds // 3600) % 24)
        m = str((elsapsed_time.seconds // 60) % 60)
        return d + ' дн, ' + h + ' ч, ' + m + ' мин'


    def close(self, new_status='cn'):
        # Task will only be closed in case if it checked or canceled AND it has not been closed yet
        if new_status in ['cn', 'ch'] and self.status in ['cn', 'ch']:
            self.closure_datetime = dt.datetime.now()
            self.status = new_status
            self.save()

    def close_sub_tasks(self, new_supertask_status='cn'):
        if self.sub_tasks:
            for t in self.sub_tasks.all():
                if t.status in ['ip', 'ns', 'hs']: # If subtask is undone, cancel it
                    t.close('cn')
                    t.close_sub_tasks('cn')
                elif t.status == 'dn':
                    if new_supertask_status == 'cn':
                        t.close('cn')
                        t.close_sub_tasks('cn')
                    elif new_supertask_status == 'dn':
                        t.close('ch')

    def continue_super_task(self):
        if self.super_task:
            if self.super_task.status not in ['ch', 'dn']:
                if not self.super_task.has_unchecked_sub_task(exclude=(self,)):
                    self.super_task.status = 'ip'
                    self.super_task.save()

    def has_unchecked_sub_task(self, exclude=None):
        if exclude == None:
            exclude = list()
        if self.sub_tasks.all():
            for t in self.sub_tasks.all():
                if t not in exclude and t.status in ['ip', 'ns', 'hs', 'dn']:
                    return True


    def set_new_status(self):
        """
        Will not save changes for this task, as it is assumed that we will call
        save() later anyway, but will make accompanying changes with this task's
        instance if it got 'dn', 'cn' or 'ch' status, and WILL change and save
        in DB all related tasks accordingly to their current statuses

        """
        if self.status in ['dn', 'cn']:  # If new task's status is done or canseled, all undone subtasks must be closed
            self.close_sub_tasks(new_supertask_status=self.status)

        if self.status in ['ch', 'cn']:  # If new task's status is checked or canseled, then this task must be closed.
            self.closure_datetime = dt.datetime.now()
            self.continue_super_task() # If the task has supertask, set supertask's status as 'ip', if it has no other undone subtasks


    def get_absolute_url(self):
        return reverse('task_detail_url', kwargs={'id': self.id})

    def __str__(self):
        return '{}'.format(self.name)


class UserRole(models.Model):
    """
    Class should have default entities created before adding users.
    Using 'id' in url.
    """
    name = models.CharField(max_length=150, db_index=True)
    body = models.CharField(max_length=350, db_index=True, default='У этой роли нет описания')

    def __str__(self):
        return '{}'.format(self.name)

    def get_absolute_url(self):
        return reverse('user_role_url', kwargs={'id': self.id})


class Department(models.Model):
    """
    Class should have default entities created before adding users.
    """
    creation_date = models.DateTimeField(auto_now_add=True, null=True)
    name = models.CharField(max_length=150, db_index=True)
    body = models.CharField(max_length=350, db_index=True, default='У этого отделения нет описания')
    super_department = models.ForeignKey('Department',
                                        null=True,
                                        blank=True,
                                        on_delete=models.SET_NULL,
                                        related_name="sub_departments")
    chief = models.OneToOneField('UserProfile', null=True,
                                    on_delete=models.SET_NULL,
                                    related_name="slave_department")

    def __str__(self):
        return '{}'.format(self.name)

    def get_absolute_url(self):
        return reverse('department_detail_url', kwargs={'id': self.id})

    class Meta:
        ordering = ['name']





class InfoMessage(models.Model):
    REMINDER = 'rmd'
    INFO = 'inf'
    OTHER = 'oth'

    TYPES = (
        (REMINDER, 'Напоминание'),
        (INFO, 'Информация'),
        (OTHER, 'Другое'),)

    message = models.CharField(max_length=350, db_index=True, default='Нет описания')
    date = models.DateTimeField(auto_now_add=True)
    receivers = models.ManyToManyField('UserProfile', related_name="received_messages")
    message_type = models.CharField(max_length=3, choices=TYPES, default=OTHER)
    was_read = models.BooleanField(default=False)
    initiator = models.ForeignKey('UserProfile', null=True, blank=True, on_delete=models.SET_NULL, related_name="initiated_messages")
    task = models.ForeignKey('Task', null=True, blank=True, on_delete=models.CASCADE, related_name="messages_log")

    def __str__(self):
        return 'Сообщение: {}, получатели: {}'.format(self.message, self.receivers)

    def get_absolute_url(self):
        return reverse('message_detail_url', kwargs={'id': self.id})

    class Meta:
        ordering = ['date']
