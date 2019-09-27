from django.contrib.auth.models import (AbstractBaseUser,
                                        BaseUserManager)
from django.utils import timezone
from django.db import models
from django.conf import settings


# ----- User & Profile -----

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("Users must have an email address.")

        user = self.model(
            email=self.normalize_email(email),
            username=username
        )

        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(
            email,
            username,
            password,
        )

        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user


class User(AbstractBaseUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    is_staff = models.BooleanField(default=False)
    joined_on = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return "@{}".format(self.username)

    def get_short_name(self):
        return self.username

    def get_long_name(self):
        return "Username: {} | Email: {}".format(self.username,
                                                 self.email)


class UserProfile(models.Model):
    name = models.CharField(max_length=50)
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name="user_profile")
    bio = models.TextField(max_length=250, default="")
    avatar = models.ImageField(default='default.jpg',
                               upload_to='profile_pictures')
    skills = models.ManyToManyField("Skill",
                                    related_name="user_skills")
    projects = models.ManyToManyField("Project",
                                      related_name="user_projects")


# ----- Skill & Projects -----

class Skill(models.Model):
    skill_name = models.CharField(max_length=50)


class Project(models.Model):
    project_title = models.CharField(max_length=50)
    project_owned_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                         on_delete=models.CASCADE,
                                         related_name="project_owner")
    project_description = models.TextField()
    project_timeline = models.TextField()
    project_application = models.TextField()


class PastProjects(models.Model):
    project_title = models.CharField(max_length=50)
    project_owned_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                         on_delete=models.CASCADE,
                                         related_name="past_project_owner")


# ----- Position & Application -----

class Position(models.Model):
    position_name = models.CharField(max_length=50)
    position_description = models.TextField()
    project = models.ForeignKey(Project,
                                on_delete=models.CASCADE,
                                related_name="project_position")
    position_filled = models.ForeignKey(User,
                                        on_delete=models.CASCADE,
                                        related_name="position_filled_by",
                                        blank=True,
                                        null=True)


class Application(models.Model):
    applied_on = models.DateTimeField(default=timezone.now)
    position = models.ForeignKey(Position,
                                 on_delete=models.CASCADE,
                                 related_name="application_position")
    applicant = models.ForeignKey(User,
                                  on_delete=models.CASCADE,
                                  related_name="position_applicant")
    applied_date = models.DateTimeField(default=timezone.now)
    accepted = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)


# ----- Notification -----

class Notification(models.Model):
    notified_on = models.DateTimeField(default=timezone.now)
    seen = models.BooleanField(default=False)
    description = models.CharField(max_length=255)
    notifying = models.ForeignKey(User,
                                  on_delete=models.CASCADE,
                                  related_name="notifying_user")
