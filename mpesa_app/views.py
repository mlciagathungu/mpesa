from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
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
@method_decorator(csrf_exempt, name='dispatch')
class MpesaStkPushView(APIView):
    def post(self, request):
        phone = request.data.get('phone_number')
        amount = request.data.get('amount')
        account_reference = request.data.get('account_reference')
        description = request.data.get('description', 'WiFi Purchase')

        # Validate required fields
        if not phone or not amount or not account_reference:
            return Response(
                {"success": False, "CustomerMessage": "Missing required fields."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # -- Replace these with your actual credentials --
        consumer_key = "HXNYqA2gUlKqtj37sWQ2GvgNJu9PjfNGY5mkv8M8ZysqwA4D"
        consumer_secret = "TGADuZIMQQgpLM2xea4ujJIXhbApOt9IWFD9GiRVgELrYhmpmA5RoICDWDUx1nhu"
        shortcode= "174379"
        passkey= "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
        callback_url = "https://caac-102-140-248-44.ngrok-free.app/api/mpesa/callback/"
        base_url = "https://sandbox.safaricom.co.ke"
        # -- END credentials --

        # Step 1: Get access token
        try:
            auth_url = f'{base_url}/oauth/v1/generate?grant_type=client_credentials'
            auth = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()
            headers = {'Authorization': f'Basic {auth}'}
            r = requests.get(auth_url, headers=headers, timeout=10)
            r.raise_for_status()
            access_token = r.json().get('access_token')
            if not access_token:
                return Response(
                    {"success": False, "CustomerMessage": "Failed to get M-Pesa access token."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            return Response(
                {"success": False, "CustomerMessage": f"Error getting access token: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Step 2: Prepare STK Push request
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f"{shortcode}{passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()
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
            "TransactionDesc": description
        }

        # Step 3: Send STK Push request
        try:
            resp = requests.post(stk_url, json=payload, headers=headers, timeout=15)
            resp_json = resp.json()
        except Exception as e:
            return Response(
                {"success": False, "CustomerMessage": f"Error sending STK Push: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Step 4: Interpret Safaricom response
        if resp.ok and resp_json.get("ResponseCode") == "0":
            return Response({
                "success": True,
                "MerchantRequestID": resp_json.get("MerchantRequestID"),
                "CheckoutRequestID": resp_json.get("CheckoutRequestID"),
                "ResponseCode": resp_json.get("ResponseCode"),
                "ResponseDescription": resp_json.get("ResponseDescription"),
                "CustomerMessage": resp_json.get("CustomerMessage"),
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "success": False,
                "ResponseCode": resp_json.get("ResponseCode"),
                "ResponseDescription": resp_json.get("ResponseDescription"),
                "CustomerMessage": resp_json.get("CustomerMessage") or resp_json.get("errorMessage") or "STK Push failed.",
                "errorMessage": resp_json.get("errorMessage"),
            }, status=status.HTTP_400_BAD_REQUEST)











