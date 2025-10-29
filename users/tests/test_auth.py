import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    """Test cases for user registration endpoint."""
    
    def test_register_success(self, api_client, user_data):
        """Test successful user registration."""
        response = api_client.post('/api/auth/register/', user_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']
        assert response.data['user']['email'] == user_data['email']
        
        assert User.objects.filter(email=user_data['email']).exists()
    
    def test_register_duplicate_email(self, api_client, user_data, create_user):
        """Test registration with duplicate email."""
        create_user(email=user_data['email'])
        
        response = api_client.post('/api/auth/register/', user_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data
    
    def test_register_password_mismatch(self, api_client, user_data):
        """Test registration with password mismatch."""
        user_data['password2'] = 'DifferentPassword123!'
        
        response = api_client.post('/api/auth/register/', user_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data
    
    def test_register_weak_password(self, api_client, user_data):
        """Test registration with weak password."""
        user_data['password'] = 'weak'
        user_data['password2'] = 'weak'
        
        response = api_client.post('/api/auth/register/', user_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data
    
    def test_register_missing_email(self, api_client, user_data):
        """Test registration without email."""
        user_data.pop('email')
        
        response = api_client.post('/api/auth/register/', user_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data


@pytest.mark.django_db
class TestUserLogin:
    """Test cases for user login endpoint."""
    
    def test_login_success(self, api_client, create_user):
        """Test successful login with email."""
        email = 'loginuser@example.com'
        password = 'LoginPass123!'
        user = create_user(email=email, password=password)
        
        response = api_client.post('/api/auth/login/', {
            'email': email,
            'password': password
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
    
    def test_login_invalid_credentials(self, api_client, create_user):
        """Test login with invalid credentials."""
        create_user()
        
        response = api_client.post('/api/auth/login/', {
            'email': 'wronguser@example.com',
            'password': 'wrongpassword'
        }, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_wrong_password(self, api_client, create_user):
        """Test login with wrong password."""
        user = create_user()
        
        response = api_client.post('/api/auth/login/', {
            'email': user.email,
            'password': 'WrongPassword123!'
        }, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTokenRefresh:
    """Test cases for token refresh endpoint."""
    
    def test_refresh_token_success(self, api_client, create_user):
        """Test successful token refresh."""
        user = create_user()
        login_response = api_client.post('/api/auth/login/', {
            'email': user.email,
            'password': 'TestPass123!'
        }, format='json')
        
        refresh_token = login_response.data['refresh']
        
        response = api_client.post('/api/auth/token/refresh/', {
            'refresh': refresh_token
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
    
    def test_refresh_token_invalid(self, api_client):
        """Test token refresh with invalid token."""
        response = api_client.post('/api/auth/token/refresh/', {
            'refresh': 'invalid-token'
        }, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserDetail:
    """Test cases for user detail endpoint."""
    
    def test_get_user_detail_authenticated(self, api_client, create_user):
        """Test retrieving user details when authenticated."""
        user = create_user()
        login_response = api_client.post('/api/auth/login/', {
            'email': user.email,
            'password': 'TestPass123!'
        }, format='json')
        
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = api_client.get('/api/auth/me/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email
        assert 'id' in response.data
        assert 'created_at' in response.data
    
    def test_get_user_detail_unauthenticated(self, api_client):
        """Test retrieving user details without authentication."""
        response = api_client.get('/api/auth/me/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_user_detail(self, api_client, create_user):
        """Test updating user details."""
        user = create_user()
        login_response = api_client.post('/api/auth/login/', {
            'email': user.email,
            'password': 'TestPass123!'
        }, format='json')
        
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = api_client.patch('/api/auth/me/', {
            'first_name': 'Updated',
            'last_name': 'Name'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Updated'
        assert response.data['last_name'] == 'Name'
        
        user.refresh_from_db()
        assert user.first_name == 'Updated'


@pytest.mark.django_db
class TestChangePassword:
    """Test cases for password change endpoint."""
    
    def test_change_password_success(self, api_client, create_user):
        """Test successful password change."""
        old_password = 'OldPass123!'
        new_password = 'NewPass123!'
        user = create_user(password=old_password)
        
        login_response = api_client.post('/api/auth/login/', {
            'email': user.email,
            'password': old_password
        }, format='json')
        
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = api_client.put('/api/auth/change-password/', {
            'old_password': old_password,
            'new_password': new_password,
            'new_password2': new_password
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        
        user.refresh_from_db()
        assert user.check_password(new_password)
    
    def test_change_password_wrong_old_password(self, api_client, create_user):
        """Test password change with wrong old password."""
        user = create_user()
        login_response = api_client.post('/api/auth/login/', {
            'email': user.email,
            'password': 'TestPass123!'
        }, format='json')
        
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = api_client.put('/api/auth/change-password/', {
            'old_password': 'WrongOldPass123!',
            'new_password': 'NewPass123!',
            'new_password2': 'NewPass123!'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'old_password' in response.data
    
    def test_change_password_mismatch(self, api_client, create_user):
        """Test password change with new password mismatch."""
        user = create_user()
        login_response = api_client.post('/api/auth/login/', {
            'email': user.email,
            'password': 'TestPass123!'
        }, format='json')
        
        access_token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = api_client.put('/api/auth/change-password/', {
            'old_password': 'TestPass123!',
            'new_password': 'NewPass123!',
            'new_password2': 'DifferentPass123!'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'new_password' in response.data
    
    def test_change_password_unauthenticated(self, api_client):
        """Test password change without authentication."""
        response = api_client.put('/api/auth/change-password/', {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass123!',
            'new_password2': 'NewPass123!'
        }, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED