"""Tests for User model."""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


@pytest.mark.integration
class TestUserModel:
    """Tests for User model."""

    def test_create_user_with_all_fields(self, db):
        """Should create user with all fields."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.check_password('testpass123')
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_user_minimal_fields(self, db):
        """Should create user with minimal required fields."""
        user = User.objects.create_user(
            username='minimal',
            password='testpass123'
        )
        
        assert user.username == 'minimal'
        assert user.check_password('testpass123')

    def test_create_superuser(self, db):
        """Should create superuser with elevated permissions."""
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        assert superuser.is_staff
        assert superuser.is_superuser
        assert superuser.is_active

    def test_str_returns_full_name(self, db):
        """Should return full name when both first and last name are set."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        assert str(user) == 'John Doe'

    def test_str_returns_email_when_no_full_name(self, db):
        """Should return email when full name is not available."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        assert str(user) == 'test@example.com'

    def test_str_returns_username_when_no_email_or_full_name(self, db):
        """Should return username when neither full name nor email available."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        assert str(user) == 'testuser'

    def test_str_returns_partial_name_as_email(self, db):
        """Should return email when only partial name is provided."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='John'
        )
        
        # get_full_name() returns empty string if last_name is missing
        # so it should fall back to email
        assert str(user) == 'test@example.com'

    def test_timestamps_auto_populated(self, db):
        """Should auto-populate created_at and updated_at timestamps."""
        before = timezone.now()
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        after = timezone.now()
        
        assert user.created_at is not None
        assert user.updated_at is not None
        assert before <= user.created_at <= after
        assert before <= user.updated_at <= after

    def test_updated_at_changes_on_save(self, db):
        """Should update updated_at timestamp on save."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        original_updated_at = user.updated_at
        
        # Wait a tiny bit and update
        user.email = 'newemail@example.com'
        user.save()
        
        assert user.updated_at > original_updated_at

    def test_created_at_does_not_change_on_save(self, db):
        """Should not change created_at on subsequent saves."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        original_created_at = user.created_at
        
        user.email = 'newemail@example.com'
        user.save()
        
        assert user.created_at == original_created_at

    def test_username_is_unique(self, db):
        """Should enforce unique username constraint."""
        User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Attempting to create another user with same username should fail
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='testuser',
                password='differentpass'
            )

    def test_email_can_be_blank(self, db):
        """Should allow blank email."""
        user = User.objects.create_user(
            username='testuser',
            email='',
            password='testpass123'
        )
        
        assert user.email == ''

    def test_is_active_default_true(self, db):
        """Should default is_active to True."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        assert user.is_active is True

    def test_user_fixture(self, user):
        """Should work with user fixture from conftest."""
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert str(user) == 'Test User'