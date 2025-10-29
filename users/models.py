from django.contrib.auth.models import AbstractUser
from django.db import models

from refuel_planner.models import TimestampedModel


class User(AbstractUser, TimestampedModel):
    def __str__(self) -> str:
        full_name = self.get_full_name().strip()
        if full_name and self.first_name and self.last_name:
            return full_name
        if self.email:
            return self.email
        return self.username