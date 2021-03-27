import datetime as dt
from dateutil.relativedelta import*
from django.db.models import Q
from django.core.exceptions import ValidationError

from .utils import*
from .forms import*

def task_create_permission(supertask, user, onelevel=True, onlyauthors=False):
    """
    All permission checkers about creation and editing a new task are defined
    here.

    onelevel - if True, only author (optional: and responsible users) of this
    task has permission to create its subtask, otherwise author of every
    supertask of the task (not supertasks' responsible users) also has the
    permission

    onlyauthor - if True, only authors of supertask has permission to create its
    subtask, otherwise authors and responsible users have permission
    """
    if supertask == None:    # If there is no supertask, then everyone can create the task
        return True
    if user.user.is_staff:
        return True
    if onlyauthors == True:       # Checking if user is author of supertask of current task if onlyauthors set to True
        if user == supertask.author:
            return True
    elif user in supertask.responsible_users.all() or user == supertask.author: # Otherwise check if user is author or is in responsible users' list
        return True
    if onelevel == False:   # If onelevel set to False, check the same for supertask, with onlyauthors set to True
        return task_create_permission(supertask.super_task, user, onelevel=False, onlyauthors=True)


def calc_deadline(start_date, delta_time_dict):
    h = int(delta_time_dict.get('hours', 0))
    d = int(delta_time_dict.get('days', 0))
    m = int(delta_time_dict.get('months', 0))
    use_date = start_date + relativedelta(months=+m)
    use_date = use_date + relativedelta(days=+d)
    use_date = use_date + relativedelta(hours=+h)
    return use_date


def check_user_to_task_rel(task, userprofile):
    user_to_task = 'others'
    if userprofile.user.is_staff:
        user_to_task = 'admin'
    elif userprofile == task.author:
        user_to_task = 'author'
    elif userprofile in task.responsible_users.all():
        user_to_task = 'responsible'
    return user_to_task


def check_user_to_task_rel_re(task, userprofile):
    user_to_task = []
    if userprofile.user.is_staff:
        user_to_task.append('admin')
    if userprofile == task.author:
        user_to_task.append('author')
    if userprofile in task.responsible_users.all():
        user_to_task.append('responsible')
    return user_to_task


def define_template_containing(task, userprofile):
    user_to_task = check_user_to_task_rel_re(task, userprofile)
    closed = bool(task.closure_datetime)

    admin = 'admin' in user_to_task

    admin_or_author = 'admin' in user_to_task or \
                        ('author' in user_to_task and not closed)

    admin_or_author_or_responsible ='admin' in user_to_task or \
                                    (('author' in user_to_task or \
                                    'responsible' in user_to_task) and \
                                    not closed)

    status_is_undone = task.status not in ['dn', 'ch', 'cn']
    name = admin_or_author
    body = admin_or_author
    deadline = admin_or_author
    justification = admin_or_author
    responsible_users = admin_or_author
    status = admin_or_author_or_responsible
    subtasks = admin_or_author_or_responsible and status_is_undone
    delete_task = admin
    show_time_remains = not closed
    template_contains = {
                    'name': name,
                    'body': body,
                    'status': status,
                    'deadline': deadline,
                    'justification': justification,
                    'responsible_users': responsible_users,
                    'subtasks': subtasks,
                    'delete_task': delete_task,
                    'show_time_remains': show_time_remains}
    return template_contains



def define_mf_for_task(task, userprofile):
    if userprofile == task.author or userprofile.user.is_staff:
        return create_task_form(['name', 'body', 'status', 'responsible_users', 'justification', 'comment', 'deadline'], userprofile, task)
    elif userprofile in task.responsible_users.all():
        return create_task_form(['comment', 'status'], userprofile, task)
    else:
        return create_task_form(['comment'], userprofile)


def create_task_form(fields_list, userprofile, task=None):
    all_widgets = {
        'name': forms.TextInput(attrs={'class':'form-control', 'style':'background-color: {};'.format(COLORS['enabled'])}),
        'status': forms.Select(attrs={'class':'form-control', 'style':'background-color: {};'.format(COLORS['enabled'])}),
        'justification': forms.Textarea(attrs={'class':'form-control', "rows":2, "cols":24, 'style':'background-color: {};'.format(COLORS['enabled'])}),
        'responsible_users': forms.SelectMultiple(attrs={'class':'form-select', 'size':8, 'style':'background-color: {};'.format(COLORS['enabled'])}),
        'body': forms.Textarea(attrs={'class':'form-control', "rows":9, "cols":24, 'style':'background-color: {};'.format(COLORS['enabled'])}),
        'comment': forms.Textarea(attrs={'class':'form-control', "rows":3, "cols":24, 'style':'background-color: {};'.format(COLORS['enabled'])}),
        'deadline': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type':'datetime-local', 'class': 'form-control',})}

    class TaskForm(TaskCreateForm):
        class Meta(TaskCreateForm.Meta):
            fields = fields_list
            widgets = {}
            for field in fields:
                if field in all_widgets:
                    widgets[field] = all_widgets[field]

        def __init__(self, *args, **kwargs):
            super(TaskCreateForm, self).__init__(*args, **kwargs)
            if 'responsible_users' in self.fields:
                if hasattr(userprofile, 'slave_department'):
                    queryset = userprofile.slave_department.workers.all().order_by('second_name')
                    queryset = UserProfile.objects.filter(Q(department=userprofile.slave_department) \
                                    | Q(id__exact=userprofile.id))
                    self.fields['responsible_users'].queryset = queryset
                else:
                    queryset = UserProfile.objects.filter(id__exact=userprofile.id)
                    self.fields['responsible_users'].queryset = queryset

            if 'status' in self.fields:
                all_choices = self.fields['status'].choices
                all_choices_dict = {a: b for a, b in all_choices}
                new_choices = [(task.status, all_choices_dict[task.status])] # Current status must always remain in choices
                self.fields['status'].choices = []
                if task:
                    user_to_task = check_user_to_task_rel_re(task, userprofile)

                    if 'author' in user_to_task:
                        # If task is done, it can be checked by author:
                        if task.status == 'dn':
                            new_choices.append(('ch', 'Проверено')) # The task closes

                        # Also task can be canseled by author, if it is not already canseled or checked:
                        if task.status not in ['cn', 'ch']:
                            new_choices.append(('cn', 'Отменено')) # All undone subtasks become canceled AND the task closes

                    if 'responsible' in user_to_task:
                        # If task is not started, it can be checked by author:
                        if task.status in ('ns', 'dn'):
                            new_choices.append(('ip', 'В процессе выполнения'))
                        if task.status in ('ns', 'ip', 'hs'):
                            new_choices.append(('dn', 'Выполнено')) # All undone subtasks become canceled

                    if 'admin' in user_to_task:
                        new_choices = all_choices

                self.fields['status'].choices = new_choices
    return TaskForm


def deadline_validator_gen(deadline_limit):
    def validate_deadline(value):
        if value > deadline_limit:
            raise ValidationError('%s Сроки выполнения подзадачи больше сроков основной задачи!' % value)
    return validate_deadline


def has_changed(instance, field):
    if not instance.pk:
        return False
    old_value = instance.__class__._default_manager.filter(pk=instance.pk).values(field).get()[field]
    return not getattr(instance, field) == old_value


def _make_message(message, receivers, make_log=True):
    m = InfoMessage(message=message,
                    message_type=InfoMessage.INFO,
                    initiator=current_user,
                    task=task)
    m.save()
    m.receivers.set(receivers)


def make_messages_about_creation(task):
    message = 'Создана новая задача!'
    receivers = list(task.responsible_users.all())
    _make_message(message, receivers)


def make_messages_about_changes(old, new, current_user, task):
    changes = {}


    for field in old:
        if new[field] != old[field]:
            changes[field] = (old[field], new[field])

    for key, value in changes.items():

        if key == 'responsible_users':
            removed_workers = [i for i in value[0] if i not in value[1]]
            new_workers = [i for i in value[1] if i not in value[0]]
            r = ' Убраны: ' + str(*[str(i) for i in removed_workers]) if removed_workers else ''
            n = ', добавлены: ' + str(*[str(i) for i in new_workers]) if new_workers else ''
            message_all = 'У задачи изменены исполнители.' + r + n
            message_for_old = 'Вас убрали из ответственных за выполнение этой задачи'
            message_for_new = 'Вам назаначили данную задачу'
            receivers_other = [i for i in task.responsible_users.all() if i not in set().union(removed_workers, new_workers)] + [task.author]
            _make_message(message_all, receivers_other)
            _make_message(message_for_old, removed_workers)
            _make_message(message_for_new, new_workers)

        if key == 'deadline':
            message = 'Изменены сроки исполнения (' \
                + str(value[0].strftime("%d.%m.%Y %H:%M")) + ' -> ' \
                + str(value[1].strftime("%d.%m.%Y %H:%M")) + ')'
            receivers = list(task.responsible_users.all()) + [task.author]
            _make_message(message, receivers)

        if key == 'body':
            message = 'Изменено описание задачи'
            receivers = list(task.responsible_users.all()) + [task.author]
            _make_message(message, receivers)

        if key == 'name':
            message = 'Изменено название (' + str(value[0]) + ' -> ' + str(value[1]) + ')'
            receivers = list(task.responsible_users.all()) + [task.author]
            _make_message(message, receivers)

        if key == 'status':
            message = 'Изменен статус (' + Task.return_status(value[0]) + \
                                  ' -> ' + Task.return_status(value[1]) + ')'

            receivers = list(task.responsible_users.all()) + [task.author]
            _make_message(message, receivers)

            if value[1] == 'dn':
                message = 'Задача выполнена, можно проверять'
                receivers = [task.author]
                _make_message(message, receivers)

            if value[1] == 'сn':
                message = 'Задача отменена!'
                receivers = list(task.responsible_users.all())
                _make_message(message, receivers)

            if value[1] == 'ch':
                message = 'Задача проверена'
                receivers = list(task.responsible_users.all())
                _make_message(message, receivers)
