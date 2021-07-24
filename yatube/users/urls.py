from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),
    path('password_change/', views.PasswordChange.as_view(),
         name='password_change'
         ),
    path('password_reset/', views.PasswordReset.as_view(),
         name='password_reset'
         ),
]
