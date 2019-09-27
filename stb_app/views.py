from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.urls import reverse_lazy
from django.forms.models import modelformset_factory
from django.db.models import Q

import operator
import functools

from . import models
from . import forms


# ----- Home Page -----

@login_required
def index(request, skill_needed="All Skills"):
    try:
        my_profile = models.UserProfile.objects.get(user=request.user)
    except models.UserProfile.DoesNotExist:
        return redirect('social_team_builder:profile_new')

    skills_list = ["All Skills"]
    my_skills = my_profile.skills.all()
    for skill in my_skills:
        skills_list.append(skill.skill_name)

    if skill_needed != "All Skills":
        positions = models.Position.objects.filter(
            Q(position_name__icontains=skill_needed) |
            Q(position_description__icontains=skill_needed),
            position_filled__isnull=True).exclude(
            project__project_owned_by=request.user)

        context = {'positions': positions,
                   'skill_needed': skill_needed,
                   'skills_list': skills_list}
        return render(request, 'stb_app/index.html', context)

    elif my_skills:
        my_skills_name_list = []
        for skill in my_skills:
            my_skills_name_list.append(skill.skill_name)

        queryset = functools.reduce(operator.or_, (
            Q(position_name__icontains=the_skill) |
            Q(position_description__icontains=the_skill)
            for the_skill in my_skills_name_list))

        positions = models.Position.objects.filter(
            queryset,
            position_filled__isnull=True).exclude(
            project__project_owned_by=request.user)

        context = {'positions': positions,
                   'skill_needed': skill_needed,
                   'skills_list': skills_list}
        return render(request, 'stb_app/index.html', context)

    else:
        positions = None

    context = {'positions': positions}
    return render(request, 'stb_app/index.html', context)


# ----- User login/logout/sign up -----

class SignUpView(generic.CreateView):
    form_class = forms.UserCreateForm
    success_url = reverse_lazy('login')
    template_name = "registration/sign_up.html"


class LoginView(generic.FormView):
    form_class = AuthenticationForm
    success_url = reverse_lazy('home')
    success_message = "Login Successful"
    template_name = "registration/login.html"

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.request, **self.get_form_kwargs())

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super().form_valid(form)


class LogoutView(generic.RedirectView):
    url = reverse_lazy('social_team_builder:home')

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)


# ----- Profile stuff -----

@login_required
def my_profile(request):
    try:
        profile = models.UserProfile.objects.get(user=request.user)
    except models.UserProfile.DoesNotExist:
        return redirect('social_team_builder:profile_new')
    return redirect('social_team_builder:profile', pk=profile.pk)


def profile(request, pk):
    profile = get_object_or_404(models.UserProfile, pk=pk)
    my_projects = models.Project.objects.filter(project_owned_by=profile.user)
    my_past_projects = models.PastProjects.objects.filter(
        project_owned_by=profile.user)
    positions = models.Position.objects.filter(
        position_filled=profile.user)

    context = {'profile': profile,
               'positions': positions,
               'my_projects': my_projects,
               'my_past_projects': my_past_projects}
    return render(request, 'stb_app/profile.html', context)


@login_required
def profile_new(request):
    try:
        profile = models.UserProfile.objects.get(user=request.user)
    except models.UserProfile.DoesNotExist:
        past_projects = []
    else:
        return redirect('social_team_builder:profile_edit', pk=profile.pk)

    project_form = modelformset_factory(
        models.PastProjects,
        form=forms.PastProjectForm,
        extra=1)

    skill_form = modelformset_factory(
        models.Skill,
        form=forms.SkillForm,
        extra=1)

    user_profile_form = forms.ProfileForm(prefix='user_profile_new')

    project_formset = project_form(
        queryset=models.PastProjects.objects.none(),
        prefix='project_formset_new')

    skill_formset = skill_form(
        queryset=models.Skill.objects.none(),
        prefix='skill_formset_new')

    if request.method == "POST":
        user_profile_form = forms.ProfileForm(
            request.POST, request.FILES,
            prefix='user_profile_new')

        project_formset = project_form(
            request.POST,
            prefix='project_formset_new')

        skill_formset = skill_form(
            request.POST,
            prefix='skill_formset_new')

        if user_profile_form.is_valid():
            if project_formset.is_valid():
                if skill_formset.is_valid():
                    final_user_profile = user_profile_form.save(commit=False)
                    final_user_profile.user = request.user
                    final_user_profile.save()

                    for project in project_formset:
                        if project.is_valid():
                            if project.cleaned_data:
                                project = project.save(commit=False)
                                project.project_owned_by = request.user
                                project.save()

                    for skill in skill_formset:
                        if skill.is_valid():
                            if skill.cleaned_data:
                                name = skill.cleaned_data['skill_name'].lower()
                                if name == "":
                                    pass
                                else:
                                    try:
                                        add_skill = models.Skill.objects.get(
                                            skill_name=name)
                                    except models.Skill.DoesNotExist:
                                        add_skill = models.Skill.objects.create(
                                            skill_name=name)
                                    final_user_profile.skills.add(add_skill)

                    messages.success(request, 'Profile Created!')
                    try:
                        my_profile = models.UserProfile.objects.get(user=request.user)
                    except models.UserProfile.DoesNotExist:
                        my_profile = None
                    return redirect('social_team_builder:profile', pk=my_profile.pk)

    context = {'user_profile_form': user_profile_form,
               'project_formset': project_formset,
               'skill_formset': skill_formset,
               'past_projects': past_projects}
    return render(request, 'stb_app/profile_edit.html', context)


@login_required
def profile_edit(request, pk):
    try:
        user_profile = models.UserProfile.objects.get(
            user=request.user,
            id=pk
        )
    except models.UserProfile.DoesNotExist:
        return redirect('social_team_builder:profile_new')

    past_projects = models.Position.objects.filter(
        position_filled=request.user)

    my_projects = models.Project.objects.filter(
        project_owned_by=request.user)

    project_form = modelformset_factory(
        models.PastProjects,
        form=forms.PastProjectForm,
        extra=1,
        can_delete=True)

    skill_form = modelformset_factory(
        models.Skill,
        form=forms.SkillForm,
        extra=1,
        can_delete=True)

    user_profile_form = forms.ProfileForm(
        instance=user_profile,
        prefix='user_profile')

    project_formset = project_form(
        queryset=user_profile.user.past_project_owner.all(),
        prefix='project_formset')

    skill_formset = skill_form(
        queryset=user_profile.skills.all(),
        prefix='skill_formset')

    if request.method == "POST":
        user_profile_form = forms.ProfileForm(
            request.POST,
            request.FILES,
            instance=user_profile,
            prefix='user_profile')

        project_formset = project_form(
            request.POST,
            queryset=user_profile.user.past_project_owner.all(),
            prefix='project_formset')

        skill_formset =skill_form(
            request.POST,
            queryset=user_profile.skills.all(),
            prefix='skill_formset')

        if user_profile_form.is_valid():
            if project_formset.is_valid():
                if skill_formset.is_valid():
                    final_user_profile = user_profile_form.save()

                    for project in project_formset:
                        if project.is_valid():
                            if project.cleaned_data:
                                project_title = project.cleaned_data['project_title']
                                if project_title.strip() == "":
                                    project_delete = project.save(commit=False)
                                    project_delete.delete()

                                elif project_title != "":
                                    final_project = project.save(commit=False)
                                    final_project.project_owned_by = request.user
                                    final_project.save()

                    for project in project_formset.deleted_forms:
                        if project.is_valid():
                            project_to_delete = project.save(commit=False)
                            project_to_delete.delete()

                    for skill in skill_formset:
                        if skill.is_valid():
                            if skill.cleaned_data:
                                name = skill.cleaned_data['skill_name'].lower()
                                if name.strip() == "":
                                    skill = skill.save(commit=False)
                                    final_user_profile.skills.remove(skill)
                                else:
                                    try:
                                        skill_replace = models.Skill.objects.get(
                                            skill_name=name)
                                    except models.Skill.DoesNotExist:
                                        skill_replace = models.Skill.objects.create(
                                            skill_name=name)
                                    skill = skill.save(commit=False)
                                    final_user_profile.skills.add(skill_replace)

                    for skill in skill_formset.deleted_forms:
                        if skill.is_valid():
                            skill_remove = skill.save()
                            final_user_profile.skills.remove(skill_remove)

                    messages.success(request, 'Profile updated!')
                    return redirect('social_team_builder:profile', pk=user_profile.pk)

    context = {'user_profile': user_profile,
               'user_profile_form': user_profile_form,
               'project_formset': project_formset,
               'skill_formset': skill_formset,
               'past_projects': past_projects,
               'my_projects': my_projects}
    return render(request, 'stb_app/profile_edit.html', context)


# ----- Project stuff -----

def project(request, project_pk, position_pk=None, choice=None):
    try:
        profile = models.UserProfile.objects.get(
            user=request.user,
        )
    except models.UserProfile.DoesNotExist:
        profile = None

    if position_pk:
        position = models.Position.objects.get(id=position_pk)
        if choice == "apply":
            application = models.Application.objects.create(
                position=position,
                applicant=request.user)

            models.Notification.objects.create(
                notifying=application.position.project.project_owned_by,
                description="""
                An application for
                the project "{}" has
                been submitted.
                """.format(
                    application.position.project.project_title))
            messages.success(
                request,
                """
                You applied for the {} position. 
                """.format(
                position.position_name))

        elif choice == "rescind":
            app_to_delete = models.Application.objects.get(position=position)
            app_to_delete.delete()
            application = models.Application.objects.create(
                position=position,
                applicant=request.user)

            models.Notification.objects.create(
                notifying=application.position.project.project_owned_by,
                description="""
                            An application for
                            the project "{}" has
                            been rescinded.
                            """.format(
                    application.position.project.project_title))
            messages.success(
                request,
                """
                You cancelled your application 
                for the {} position.
                """.format(
                    position.position_name))

        elif choice == "undo":
            app_to_change = models.Application.objects.get(position=position)
            app_to_change.accepted = False
            app_to_change.rejected = False
            app_to_change.save()

            position.position_filled = None
            position.save()

            models.Notification.objects.create(
                notifying=app_to_change.applicant,
                description="""
                Your application for the "{}" position 
                for the project "{}" has been changed 
                to undecided.
                """.format(
                    app_to_change.position.position_name,
                    app_to_change.position.project.project_title))
            messages.success(
                request,
                """
                You changed the application for
                {} for the position {}
                to undecided.
                """.format(
                    app_to_change.applicant.user_profile.name,
                    position.position_name))

    project = get_object_or_404(models.Project, pk=project_pk)
    context = {'project': project, 'profile': profile}
    return render(request, 'stb_app/project.html', context)


@login_required
def project_new(request):
    try:
        profile = models.UserProfile.objects.get(
            user=request.user
        )
    except models.UserProfile.DoesNotExist:
        profile = None

    project_form = forms.ProjectForm(prefix='project_form')
    position_form = modelformset_factory(
        models.Position,
        form=forms.PositionForm)
    position_formset = position_form(
        queryset=models.Position.objects.none(), prefix='position_formset')

    if request.method == "POST":
        position_formset = position_form(
            request.POST, prefix='position_formset')
        project_form = forms.ProjectForm(request.POST, prefix='project_form')
        if position_formset.is_valid():
            if project_form.is_valid():
                user_project = project_form.save(commit=False)
                user_project.project_owned_by = request.user
                user_project.save()

                profile_to_link = models.UserProfile.objects.get(user=request.user)
                user_project.user_projects.add(profile_to_link)

                for position in position_formset:
                    if position.cleaned_data:
                        open_position = position.save(commit=False)
                        open_position.position_name = open_position.position_name.lower()
                        open_position.project = user_project
                        open_position.save()

                        if open_position.position_name == "":
                            if open_position.position_description == "":
                                open_position.delete()

                for position in position_formset.deleted_forms:
                    if position.is_valid():
                        delete_position = position.save()
                        delete_position.delete()

                messages.success(request, 'Project created!')
                return redirect('social_team_builder:project',
                                project_pk=user_project.pk)

    context = {'project_form': project_form,
               'position_formset': position_formset}
    return render(request, 'stb_app/project_new.html', context)


@login_required
def project_edit(request, project_pk):
    try:
        profile = models.UserProfile.objects.get(
            user=request.user
        )
    except models.UserProfile.DoesNotExist:
        profile = None

    try:
        projects = models.Project.objects.get(
            project_owned_by=request.user,
            id=project_pk
        )
    except models.Project.DoesNotExist:
        return redirect('social_team_builder:project_new')

    project_form = forms.ProjectForm(
        instance=projects,
        prefix='project_form')

    position_form = modelformset_factory(
        models.Position,
        form=forms.PositionForm,
        can_delete=True)

    position = models.Position.objects.filter(project=projects)
    position_formset = position_form(
        queryset=position,
        prefix='position_formset')

    if request.method == "POST":
        position_formset = position_form(
            request.POST,
            queryset=position,
            prefix='position_formset')

        project_form = forms.ProjectForm(
            request.POST,
            instance=projects,
            prefix='project_form')

        if position_formset.is_valid():
            if project_form.is_valid():
                user_project = project_form.save()
                profile_to_link = models.UserProfile.objects.get(user=request.user)
                user_project.user_projects.add(profile_to_link)

                for position in position_formset:
                    if position.cleaned_data:
                        open_position = position.save(commit=False)
                        open_position.position_name = open_position.position_name.lower()
                        open_position.project = user_project
                        open_position.save()

                        if open_position.position_name == "":
                            if open_position.position_description == "":
                                applications = models.Application.objects.filter(
                                    position=open_position)
                                if applications:
                                    for application in applications:
                                        application.delete()
                                open_position.delete()

                for position in position_formset.deleted_forms:
                    if position.is_valid():
                        delete_position = position.save()
                        applications = models.Application.objects.filter(
                            position=delete_position)
                        if applications:
                            for application in applications:
                                application.delete()
                        delete_position.delete()

                messages.success(request, 'Project updated!')
                return redirect('social_team_builder:project',
                                project_pk=projects.pk)

    context = {'projects': projects,
               'project_form': project_form,
               'position_formset': position_formset}
    return render(request, 'stb_app/project_edit.html', context)


@login_required
def project_delete(request, project_pk):
    try:
        project_delete = models.Project.objects.get(
            project_owned_by=request.user,
            id=project_pk
        )
    except models.Project.DoesNotExist:
        return redirect('social_team_builder:home')

    for position in project_delete.project_position.all():
        for application in position.application_position.all():
            application.delete()
        position.delete()

    messages.success(request,
                     'You deleted project: {}'.format(
                         project_delete.project_title))

    project_delete.delete()
    return redirect("social_team_builder:my_profile")


# ----- Applications -----

@login_required
def applications(request, applications="All Applications",
                 project="All Projects",
                 choice=False, app_pk=False):
    profile = models.UserProfile.objects.get(user=request.user)

    if choice:
        if app_pk:
            choice_applicant = models.Application.objects.get(id=app_pk)

            if choice == "accepted":
                choice_applicant.accepted = True
                choice_applicant.rejected = False
                choice_applicant.position.position_filled = choice_applicant.applicant
                choice_applicant.position.save()
                choice_applicant.save()

                models.Notification.objects.create(
                    notifying=choice_applicant.applicant,
                    description="""
                    Your application for "{}" 
                    for the project "{}" has
                    been approved.
                    """.format(
                        choice_applicant.position.position_name,
                        choice_applicant.position.project.project_title))
                messages.success(
                    request,
                    """
                    The application for {} for the 
                    {} position was accepted.
                    """.format(
                        choice_applicant.applicant.user_profile.name,
                        choice_applicant.position.position_name))

            elif choice == "rejected":
                choice_applicant.rejected = True
                choice_applicant.accepted = False
                choice_applicant.save()

                models.Notification.objects.create(
                    notifying=choice_applicant.applicant,
                    description="""
                    Your application for "{}" 
                    for the project "{}" has
                    been rejected.
                    """.format(
                        choice_applicant.position.position_name,
                        choice_applicant.position.project.project_title))
                messages.success(
                    request,
                    """
                    The application for {} for the 
                    {} position was rejected.
                    """.format(
                        choice_applicant.applicant.user_profile.name,
                        choice_applicant.position.position_name))

            elif choice == "undo":
                choice_applicant.rejected = False
                if choice_applicant.accepted:
                    choice_applicant.position.position_filled = None
                    choice_applicant.position.save()
                    choice_applicant.accepted = False
                    choice_applicant.save()


                models.Notification.objects.create(
                    notifying=choice_applicant.applicant,
                    description="""
                    Your application for "{}" 
                    for the project "{}" has
                    been changed to undecided.
                    """.format(
                        choice_applicant.position.position_name,
                        choice_applicant.position.project.project_title))
                messages.success(
                    request,
                    """
                    The application for {} for the 
                    {} position was changed to undecided.
                    """.format(
                        choice_applicant.applicant.user_profile.name,
                        choice_applicant.position.position_name))

    all_applications = models.Application.objects.filter(
        position__project__project_owned_by=request.user)

    if all_applications:
        if applications == "All Applications":
            all_applications = all_applications.filter(
                accepted=False,
                rejected=False)

        elif applications == "Accepted":
            all_applications = all_applications.filter(
                accepted=True)

        elif applications == "Rejected":
            all_applications = all_applications.filter(
                rejected=True)

        if project != "All Projects":
            all_applications = all_applications.filter(
                position__project__project_title=project)

    all_projects = models.Project.objects.filter(
        project_owned_by=request.user)


    statuses = ["All Applications", "Accepted", "Rejected"]

    context = {"applications": applications,
               "project": project,
               "all_projects": all_projects,
               "all_applications": all_applications,
               "statuses": statuses,
               "profile": profile}
    return render(request, 'stb_app/applications.html', context)


# ----- Notifications -----

@login_required
def notifications(request):
    notifications_all = models.Notification.objects.order_by(
        '-id').filter(notifying=request.user)
    context = {'notifications_all': notifications_all}
    return render(request, 'stb_app/notifications.html', context)


# ----- Search -----

@login_required
def search(request):
    term = request.GET.get('term')
    matches = models.Project.objects.filter(
        Q(project_title__icontains=term) |
        Q(project_description__icontains=term) |
        Q(project_application__icontains=term) |
        Q(project_position__position_name__icontains=term) |
        Q(project_position__position_description__icontains=term)).exclude(
            project_owned_by=request.user).distinct()

    try:
        my_profile = models.UserProfile.objects.get(user=request.user)
    except models.UserProfile.DoesNotExist:
        skills_list = []
    else:
        skills_list = ["All Skills"]
        my_skills = my_profile.skills.all()
        if my_skills:
            for skill in my_skills:
                skills_list.append(skill.skill_name)

    context = {'term': term,
               'matches': matches,
               'skills_list': skills_list}
    return render(request, 'stb_app/search.html', context)
