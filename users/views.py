from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)


@extend_schema(
    tags=["Authentication"],
    summary="Register new user",
    description="Create a new user account and receive JWT tokens for immediate authentication.",
    request=UserRegistrationSerializer,
    responses={
        201: OpenApiResponse(
            description="User successfully registered",
            response=UserSerializer,
        ),
        400: OpenApiResponse(description="Invalid registration data"),
    },
    examples=[
        OpenApiExample(
            "Registration Example",
            value={
                "email": "user@example.com",
                "password": "SecurePass123!",
                "password2": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
            },
            request_only=True,
        ),
    ],
    auth=[],
)
class RegisterView(APIView):
    """API endpoint for user registration."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            refresh = RefreshToken.for_user(user)
            user_data = UserSerializer(user).data
            
            return Response(
                {
                    'user': user_data,
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh),
                    }
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Authentication"],
    summary="Login user",
    description="Authenticate user with email and password to obtain JWT access and refresh tokens.",
    examples=[
        OpenApiExample(
            "Login Example",
            value={"email": "user@example.com", "password": "SecurePass123!"},
            request_only=True,
        ),
    ],
    auth=[], 
)
class LoginView(TokenObtainPairView):
    """API endpoint for user login using JWT with email."""
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    tags=["Authentication"],
    summary="Refresh access token",
    description="Obtain a new access token using a valid refresh token.",
    auth=[],  
)
class CustomTokenRefreshView(TokenRefreshView):
    """API endpoint for refreshing access tokens."""
    permission_classes = [AllowAny]


@extend_schema(
    tags=["Authentication"],
    summary="Get or update user profile",
    description="Retrieve or update the authenticated user's profile information.",
    responses={
        200: UserSerializer,
        401: OpenApiResponse(description="Authentication required"),
    },
)
class UserDetailView(generics.RetrieveUpdateAPIView):
    """API endpoint for retrieving and updating current user details."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


@extend_schema(
    tags=["Authentication"],
    summary="Change password",
    description="Update the authenticated user's password.",
    request=ChangePasswordSerializer,
    responses={
        200: OpenApiResponse(description="Password updated successfully"),
        400: OpenApiResponse(description="Invalid password data"),
        401: OpenApiResponse(description="Authentication required"),
    },
    examples=[
        OpenApiExample(
            "Change Password Example",
            value={
                "old_password": "OldPass123!",
                "new_password": "NewSecurePass456!",
                "new_password_confirm": "NewSecurePass456!",
            },
            request_only=True,
        ),
    ],
)
class ChangePasswordView(generics.UpdateAPIView):
    """API endpoint for changing user password."""
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Password updated successfully'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)