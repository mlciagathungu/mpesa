from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import UserSignupSerializer, UserLoginSerializer
import requests
import base64
import datetime

class SignUpView(APIView):
    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                username=serializer.data['username'],
                password=serializer.data['password']
            )
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({'token': token.key})
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MpesaStkPushView(APIView):
    def post(self, request):
        phone = request.data.get('phone_number')
        amount = request.data.get('amount')
        account_reference = request.data.get('account_reference')
        transaction_desc = request.data.get('transaction_desc')
        # -- Replace with your credentials --
        consumer_key = 'YOUR_CONSUMER_KEY'
        consumer_secret = 'YOUR_CONSUMER_SECRET'
        shortcode = 'YOUR_SHORTCODE'
        passkey = 'YOUR_PASSKEY'
        callback_url = 'https://yourdomain.com/api/mpesa/callback/'
        base_url = 'https://sandbox.safaricom.co.ke'
        # -- Get access token --
        auth_url = f'{base_url}/oauth/v1/generate?grant_type=client_credentials'
        auth = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()
        headers = {'Authorization': f'Basic {auth}'}
        r = requests.get(auth_url, headers=headers)
        access_token = r.json().get('access_token')
        # -- Prepare STK Push request --
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode()
        stk_url = f"{base_url}/mpesa/stkpush/v1/processrequest"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": shortcode,
            "PhoneNumber": phone,
            "CallBackURL": callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }
        resp = requests.post(stk_url, json=payload, headers=headers)
        if resp.ok and resp.json().get("ResponseCode") == "0":
            return Response({"success": True, "message": "STK Push initiated. Check your phone."})
        return Response({"success": False, "message": resp.json().get("errorMessage", "Failed")}, status=400)











