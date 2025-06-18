from django.urls import path
from .views import SignUpView, LoginView, MpesaStkPushView

urlpatterns = [
    path('signup/', SignUpView.as_view(),name='signup'),
    path('login/', LoginView.as_view()),
    path('mpesa/stkpush/', MpesaStkPushView.as_view()),
]