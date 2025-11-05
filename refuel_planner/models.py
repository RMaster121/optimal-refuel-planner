"""Base abstract models for the refuel planner application.

This module provides foundational abstract models that other models throughout
the application inherit from. These base models add automatic timestamp tracking
and comprehensive validation behavior to ensure data integrity.
"""

from django.db import models
from django.utils.text import camel_case_to_spaces


class TimestampedModel(models.Model):
    """Abstract model providing automatic timestamp tracking.
    
    Adds created_at and updated_at fields to any inheriting model, automatically
    managing these timestamps throughout the model's lifecycle. The created_at
    field is set once on creation, while updated_at is refreshed on every save.
    
    Attributes:
        created_at (DateTimeField): Timestamp of when the instance was created.
            Set automatically on first save and never modified afterward.
        updated_at (DateTimeField): Timestamp of the most recent update.
            Automatically refreshed on every save operation.
    
    Usage:
        Inherit from this model to add timestamp tracking to any Django model:
        
        >>> class MyModel(TimestampedModel):
        ...     name = models.CharField(max_length=100)
        
        >>> obj = MyModel.objects.create(name="Test")
        >>> print(obj.created_at)  # Timestamp of creation
        >>> obj.name = "Updated"
        >>> obj.save()
        >>> print(obj.updated_at)  # Newer timestamp than created_at
    
    Note:
        This is an abstract model and will not create a database table.
        It must be inherited by concrete models to be useful.
    """
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class ValidatedModel(models.Model):
    """Abstract model enforcing comprehensive validation on save.
    
    Ensures that Django's full_clean() validation runs automatically before
    every save operation, catching validation errors before they reach the
    database. Also provides automatic verbose_name generation from class names,
    converting CamelCase to human-readable "Camel Case" format.
    
    Validation Behavior:
        - Calls full_clean() before each save()
        - Raises ValidationError if any field validation fails
        - Enforces both field-level and model-level clean() validations
        - Prevents invalid data from being persisted to the database
    
    Verbose Name Behavior:
        - Automatically converts class name to verbose name
        - Example: "RefuelPlan" becomes "Refuel Plan"
        - Applied only to concrete (non-abstract) models
        - Overrides Django's default lowercase conversion
    
    Usage:
        Inherit from this model to add automatic validation:
        
        >>> class Car(ValidatedModel):
        ...     name = models.CharField(max_length=100)
        ...
        ...     def clean(self):
        ...         if not self.name:
        ...             raise ValidationError("Name required")
        
        >>> car = Car(name="")
        >>> car.save()  # Raises ValidationError before database interaction
    
    Example:
        Combining with TimestampedModel for both features:
        
        >>> class Route(ValidatedModel, TimestampedModel):
        ...     name = models.CharField(max_length=200)
        ...     distance_km = models.DecimalField(max_digits=8, decimal_places=2)
        ...
        ...     def clean(self):
        ...         if self.distance_km <= 0:
        ...             raise ValidationError("Distance must be positive")
        
        >>> route = Route(name="Test", distance_km=-10)
        >>> route.save()  # ValidationError: "Distance must be positive"
    
    Note:
        This is an abstract model and will not create a database table.
        Models using this base class should implement clean() methods
        to define their specific validation rules.
    """
    
    class Meta:
        abstract = True
    
    def __init_subclass__(cls, **kwargs):
        """Automatically set verbose names for concrete model subclasses.
        
        Converts CamelCase class names to human-readable verbose names.
        For example, "RefuelPlan" becomes "Refuel Plan". Only applies
        to concrete models (non-abstract).
        
        Args:
            **kwargs: Additional keyword arguments passed to parent.
        """
        super().__init_subclass__(**kwargs)
        if hasattr(cls, '_meta') and not cls._meta.abstract:
            meta = cls._meta
            if meta.verbose_name == meta.object_name.lower().replace('_', ' '):
                meta.verbose_name = camel_case_to_spaces(cls.__name__)
    
    def save(self, *args, **kwargs):
        """Save the model instance after running full validation.
        
        Ensures that full_clean() is called before persisting to the database,
        catching any validation errors defined in field validators or the
        model's clean() method. This prevents invalid data from being saved.
        
        Args:
            *args: Positional arguments passed to parent save().
            **kwargs: Keyword arguments passed to parent save().
        
        Returns:
            The result of the parent save() operation.
        
        Raises:
            ValidationError: If any field or model-level validation fails
                during the full_clean() call.
        
        Example:
            >>> car = Car(name="", fuel_type="invalid")
            >>> car.save()  # Raises ValidationError
            
            >>> car = Car(name="Toyota", fuel_type="gasoline")
            >>> car.save()  # Succeeds after validation passes
        """
        self.full_clean()
        return super().save(*args, **kwargs)