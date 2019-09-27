from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django import forms

from . import models


class UserCreateForm(UserCreationForm):
    class Meta:
        fields = ("email", "username",
                  "password1", "password2")
        model = get_user_model()

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["email"].label = "Email Address"


class ProfileForm(forms.ModelForm):
    class Meta:
        model = models.UserProfile
        fields = ("name", "bio", "avatar")


class SkillForm(forms.ModelForm):
    my_skills = forms.CharField(required=False)
    class Meta:
        model = models.Skill
        fields = ("skill_name",)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = ("project_title", "project_description",
                  "project_timeline", "project_application")


class PositionForm(forms.ModelForm):
    class Meta:
        model = models.Position
        fields = ("position_name",
                  "position_description")


class PastProjectForm(forms.ModelForm):
    class Meta:
        model = models.PastProjects
        fields = ("project_title",)
