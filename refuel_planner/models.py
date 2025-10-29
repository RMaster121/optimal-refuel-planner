from django.db import models
from django.utils.text import camel_case_to_spaces


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class ValidatedModel(models.Model):
    class Meta:
        abstract = True
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, '_meta') and not cls._meta.abstract:
            meta = cls._meta
            if meta.verbose_name == meta.object_name.lower().replace('_', ' '):
                meta.verbose_name = camel_case_to_spaces(cls.__name__)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)