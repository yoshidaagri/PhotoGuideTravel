import json
import os
import boto3
from datetime import datetime
import urllib.request
import urllib.parse
import hashlib
import base64
import hmac

def main(event, context):
    """
    AWS Cognito統合認証関数
    """
    try:
        # CORS headers
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE'
        }
        
        if event['httpMethod'] == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': ''
            }
        
        # パス解析
        path = event.get('pathParameters', {}).get('proxy', '').lower()
        http_method = event['httpMethod']
        
        if http_method == 'POST':
            if path == 'register':
                return handle_register(event, headers)
            elif path == 'login':
                return handle_login(event, headers)
            elif path == 'confirm':
                return handle_confirm_signup(event, headers)
        elif http_method == 'GET':
            if path == 'verify':
                return handle_verify_token(event, headers)
        
        return {
            'statusCode': 404,
            'headers': headers,
            'body': json.dumps({'error': 'Endpoint not found'})
        }
        
    except Exception as e:
        print(f"Auth error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


def handle_register(event, headers):
    """
    Cognitoユーザー登録
    """
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        password = body.get('password')
        name = body.get('name', '')
        
        if not email or not password:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Email and password are required'})
            }
        
        # Cognito Client初期化
        cognito_client = boto3.client('cognito-idp')
        
        # ユーザープールIDとクライアントIDを取得（環境変数から）
        user_pool_id = get_user_pool_id()
        client_id = get_client_id()
        
        # ユーザー登録
        response = cognito_client.sign_up(
            ClientId=client_id,
            Username=email,
            Password=password,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                },
                {
                    'Name': 'name',
                    'Value': name
                }
            ]
        )
        
        return {
            'statusCode': 201,
            'headers': headers,
            'body': json.dumps({
                'message': 'User registered successfully',
                'userSub': response['UserSub'],
                'confirmationRequired': not response.get('UserConfirmed', True),
                'email': email,
                'name': name
            })
        }
        
    except cognito_client.exceptions.UsernameExistsException:
        return {
            'statusCode': 409,
            'headers': headers,
            'body': json.dumps({'error': 'User already exists'})
        }
    except cognito_client.exceptions.InvalidPasswordException as e:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'Invalid password format'})
        }
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Registration failed'})
        }


def handle_login(event, headers):
    """
    Cognitoユーザーログイン
    """
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        password = body.get('password')
        
        if not email or not password:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Email and password are required'})
            }
        
        # Cognito Client初期化
        cognito_client = boto3.client('cognito-idp')
        
        client_id = get_client_id()
        
        # ログイン
        auth_response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password
            }
        )
        
        # トークン取得
        tokens = auth_response['AuthenticationResult']
        
        # ユーザー情報取得
        user_info = cognito_client.get_user(
            AccessToken=tokens['AccessToken']
        )
        
        # ユーザー属性を解析
        user_attributes = {}
        for attr in user_info['UserAttributes']:
            user_attributes[attr['Name']] = attr['Value']
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Login successful',
                'accessToken': tokens['AccessToken'],
                'idToken': tokens['IdToken'],
                'refreshToken': tokens['RefreshToken'],
                'tokenType': tokens['TokenType'],
                'expiresIn': tokens['ExpiresIn'],
                'user': {
                    'sub': user_attributes.get('sub'),
                    'email': user_attributes.get('email'),
                    'name': user_attributes.get('name'),
                    'emailVerified': user_attributes.get('email_verified') == 'true'
                }
            })
        }
        
    except cognito_client.exceptions.NotAuthorizedException:
        return {
            'statusCode': 401,
            'headers': headers,
            'body': json.dumps({'error': 'Invalid credentials'})
        }
    except cognito_client.exceptions.UserNotConfirmedException:
        return {
            'statusCode': 403,
            'headers': headers,
            'body': json.dumps({'error': 'User not confirmed. Please check your email.'})
        }
    except Exception as e:
        print(f"Login error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Login failed'})
        }


def handle_confirm_signup(event, headers):
    """
    ユーザー確認（メール認証）
    """
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        confirmation_code = body.get('confirmationCode')
        
        if not email or not confirmation_code:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Email and confirmation code are required'})
            }
        
        cognito_client = boto3.client('cognito-idp')
        client_id = get_client_id()
        
        # 確認コード検証
        cognito_client.confirm_sign_up(
            ClientId=client_id,
            Username=email,
            ConfirmationCode=confirmation_code
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'User confirmed successfully'})
        }
        
    except cognito_client.exceptions.CodeMismatchException:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'Invalid confirmation code'})
        }
    except cognito_client.exceptions.ExpiredCodeException:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'Confirmation code has expired'})
        }
    except Exception as e:
        print(f"Confirmation error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Confirmation failed'})
        }


def handle_verify_token(event, headers):
    """
    アクセストークン検証
    """
    try:
        # Authorization ヘッダーからトークンを取得
        auth_header = event.get('headers', {}).get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({'error': 'No valid token provided'})
            }
        
        access_token = auth_header.replace('Bearer ', '')
        
        cognito_client = boto3.client('cognito-idp')
        
        # トークンでユーザー情報取得
        user_info = cognito_client.get_user(AccessToken=access_token)
        
        # ユーザー属性を解析
        user_attributes = {}
        for attr in user_info['UserAttributes']:
            user_attributes[attr['Name']] = attr['Value']
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'valid': True,
                'user': {
                    'sub': user_attributes.get('sub'),
                    'email': user_attributes.get('email'),
                    'name': user_attributes.get('name'),
                    'emailVerified': user_attributes.get('email_verified') == 'true'
                }
            })
        }
        
    except cognito_client.exceptions.NotAuthorizedException:
        return {
            'statusCode': 401,
            'headers': headers,
            'body': json.dumps({'valid': False, 'error': 'Invalid token'})
        }
    except Exception as e:
        print(f"Token verification error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'valid': False, 'error': 'Verification failed'})
        }


def get_user_pool_id():
    """
    Cognito User Pool IDを取得
    """
    # CloudFormationスタック名から取得
    stage = os.environ.get('STAGE', 'dev')
    service_name = 'ai-tourism-poc'
    
    # 実際にはスタック出力から取得する必要がある
    # 簡単な実装として固定値を返す（後で修正必要）
    return f"{service_name}-user-pool-{stage}"


def get_client_id():
    """
    Cognito User Pool Client IDを取得
    """
    # 実際にはスタック出力から取得する必要がある
    # 簡単な実装として固定値を返す（後で修正必要）
    stage = os.environ.get('STAGE', 'dev')
    service_name = 'ai-tourism-poc'
    return f"{service_name}-user-pool-client-{stage}"


# デモ用：固定ユーザーの自動作成
def create_demo_user_if_not_exists():
    """
    デモユーザー 'tourist-guide' を自動作成
    """
    try:
        cognito_client = boto3.client('cognito-idp')
        user_pool_id = get_user_pool_id()
        
        try:
            # ユーザーが存在するか確認
            cognito_client.admin_get_user(
                UserPoolId=user_pool_id,
                Username='tourist-guide@example.com'
            )
        except cognito_client.exceptions.UserNotFoundException:
            # ユーザーが存在しない場合は作成
            cognito_client.admin_create_user(
                UserPoolId=user_pool_id,
                Username='tourist-guide@example.com',
                UserAttributes=[
                    {'Name': 'email', 'Value': 'tourist-guide@example.com'},
                    {'Name': 'name', 'Value': 'Tourist Guide'},
                    {'Name': 'email_verified', 'Value': 'true'}
                ],
                TemporaryPassword='TempPass123!',
                MessageAction='SUPPRESS'
            )
            
            # パスワードを恒久的に設定
            cognito_client.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username='tourist-guide@example.com',
                Password='hokkaido2024',
                Permanent=True
            )
            
    except Exception as e:
        print(f"Demo user creation error: {str(e)}")