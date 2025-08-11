import json
import boto3
import os
from datetime import datetime, timedelta

# JST時刻ユーティリティ関数
def get_jst_now():
    """現在の日本時間（JST = UTC+9）を取得"""
    return datetime.utcnow() + timedelta(hours=9)

def get_jst_isoformat():
    """現在の日本時間をISO形式の文字列で取得"""
    jst_time = get_jst_now()
    return jst_time.isoformat() + '+09:00'

# Import usage checker functions (inline to avoid module dependency issues)
def check_usage_limit(user_id, user_type='free'):
    """ユーザーの解析使用制限をチェック"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(f"{os.environ.get('PROJECT_NAME', 'ai-tourism-poc')}-users-{os.environ.get('STAGE', 'dev')}")
        
        try:
            user_response = table.get_item(Key={'user_id': user_id})
            if 'Item' not in user_response:
                create_new_user(user_id)
                user_data = {'user_type': 'free', 'monthly_analysis_count': 0, 'premium_expiry': None}
            else:
                user_data = user_response['Item']
        except Exception as e:
            print(f"Error getting user data: {e}")
            create_new_user(user_id)
            user_data = {'user_type': 'free', 'monthly_analysis_count': 0, 'premium_expiry': None}
        
        current_user_type = user_data.get('user_type', 'free')
        
        if current_user_type == 'free':
            monthly_count = int(user_data.get('monthly_analysis_count', 0))
            if monthly_count >= 5:
                return {
                    'allowed': False, 'remaining': 0, 'user_type': 'free',
                    'message': '無料プランでは月5回まで解析可能です。プレミアムプランにアップグレードしてください。',
                    'upgrade_required': True
                }
            return {'allowed': True, 'remaining': 5 - monthly_count, 'user_type': 'free', 'message': f'残り{5 - monthly_count}回利用可能です。'}
        else:
            return {'allowed': True, 'remaining': -1, 'user_type': current_user_type, 'message': 'プレミアムプラン利用中'}
    except Exception as e:
        print(f"Usage check error: {str(e)}")
        return {'allowed': True, 'remaining': 5, 'user_type': 'free', 'message': 'システムエラー: 一時的に制限なしで利用可能'}

def increment_usage_count(user_id):
    """解析使用回数を増加"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(f"{os.environ.get('PROJECT_NAME', 'ai-tourism-poc')}-users-{os.environ.get('STAGE', 'dev')}")
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='ADD monthly_analysis_count :inc, total_analysis_count :inc SET updated_at = :updated',
            ExpressionAttributeValues={':inc': 1, ':updated': get_jst_isoformat()}
        )
        print(f"Usage count incremented for user: {user_id}")
        return True
    except Exception as e:
        print(f"Error incrementing usage: {e}")
        return False

def create_new_user(user_id, email='', display_name='', auth_provider='cognito'):
    """新規ユーザー作成"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(f"{os.environ.get('PROJECT_NAME', 'ai-tourism-poc')}-users-{os.environ.get('STAGE', 'dev')}")
        
        timestamp = get_jst_isoformat()
        item = {
            'user_id': user_id, 'email': email, 'auth_provider': auth_provider, 'display_name': display_name,
            'profile_picture': '', 'preferred_language': 'ja', 'user_type': 'free', 'premium_expiry': None,
            'monthly_analysis_count': 0, 'total_analysis_count': 0, 'last_login_at': timestamp,
            'created_at': timestamp, 'updated_at': timestamp
        }
        table.put_item(Item=item)
        print(f"New user created: {user_id}")
        return item
    except Exception as e:
        print(f"Error creating new user: {e}")
        return None

# Cognito客户端初始化
cognito_client = boto3.client('cognito-idp', region_name='ap-northeast-1')

def main(event, context):
    """
    認証・ユーザー管理のメインハンドラー（Cognito版）
    """
    try:
        # CORS headers
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        }
        
        if event['httpMethod'] == 'OPTIONS':
            return {'statusCode': 200, 'headers': headers, 'body': ''}
        
        # パスによる処理分岐
        path = event.get('pathParameters', {}).get('proxy', '')
        
        if path == 'check-usage':
            return handle_check_usage(event, headers)
        elif path == 'increment-usage':
            return handle_increment_usage(event, headers)
        elif path == 'create-user':
            return handle_create_user(event, headers)
        elif path == 'user-info':
            return handle_get_user_info(event, headers)
        elif path == 'verify-token':
            return handle_verify_token(event, headers)
        elif path == 'signup':
            return handle_signup_with_email(event, headers)
        elif path == 'confirm-signup':
            return handle_confirm_signup(event, headers)
        elif path == 'login':
            return handle_login_with_email(event, headers)
        elif path == 'resend-code':
            return handle_resend_confirmation_code(event, headers)
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Endpoint not found'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Authentication error: {str(e)}'})
        }


def handle_check_usage(event, headers):
    """
    使用制限チェック処理
    """
    try:
        # Cognitoトークンからユーザー情報取得
        user_info = get_user_from_token(event)
        if not user_info:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid or expired token'})
            }
        
        user_id = user_info['user_id']
        
        # 使用制限チェック
        usage_result = check_usage_limit(user_id)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(usage_result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Usage check failed: {str(e)}'})
        }


def handle_increment_usage(event, headers):
    """
    使用回数増加処理
    """
    try:
        # Cognitoトークンからユーザー情報取得
        user_info = get_user_from_token(event)
        if not user_info:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid or expired token'})
            }
        
        user_id = user_info['user_id']
        
        # 使用回数増加
        success = increment_usage_count(user_id)
        
        if success:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'Usage count updated successfully'})
            }
        else:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': 'Failed to update usage count'})
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Usage increment failed: {str(e)}'})
        }


def handle_create_user(event, headers):
    """
    新規ユーザー作成処理（Cognitoからコールバック用）
    """
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id')
        email = body.get('email', '')
        display_name = body.get('display_name', '')
        auth_provider = body.get('auth_provider', 'cognito')
        
        if not user_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'User ID is required'})
            }
        
        # 新規ユーザー作成
        user_data = create_new_user(user_id, email, display_name, auth_provider)
        
        if user_data:
            return {
                'statusCode': 201,
                'headers': headers,
                'body': json.dumps({
                    'message': 'User created successfully',
                    'user_data': user_data
                })
            }
        else:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': 'Failed to create user'})
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'User creation failed: {str(e)}'})
        }


def handle_get_user_info(event, headers):
    """
    ユーザー情報取得処理
    """
    try:
        # Cognitoトークンからユーザー情報取得
        user_info = get_user_from_token(event)
        if not user_info:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid or expired token'})
            }
        
        user_id = user_info['user_id']
        print(f"Getting user info for user_id: {user_id}")
        
        # 緊急ログインユーザーの場合はダミーデータを返す
        if user_id == 'emergency-user':
            safe_user_data = {
                'user_id': 'emergency-user',
                'email': 'emergency@test.com',
                'display_name': 'Emergency User',
                'user_type': 'free',
                'monthly_analysis_count': 2,  # テスト用に2回使用済みとする
                'total_analysis_count': 5,
                'premium_expiry': None,
                'preferred_language': 'ja'
            }
            print(f"Emergency user data: {safe_user_data}")
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(safe_user_data)
            }
        
        # DynamoDBからユーザー詳細情報取得
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(f"{os.environ.get('PROJECT_NAME', 'ai-tourism-poc')}-users-{os.environ.get('STAGE', 'dev')}")
        
        try:
            response = table.get_item(Key={'user_id': user_id})
            print(f"DynamoDB response for {user_id}: {response}")
            if 'Item' in response:
                user_data = response['Item']
                print(f"User data from DynamoDB: {user_data}")
                # 機密情報を除外
                safe_user_data = {
                    'user_id': user_data.get('user_id'),
                    'email': user_data.get('email'),
                    'display_name': user_data.get('display_name', ''),
                    'user_type': user_data.get('user_type', 'free'),
                    'monthly_analysis_count': int(user_data.get('monthly_analysis_count', 0)),
                    'total_analysis_count': int(user_data.get('total_analysis_count', 0)),
                    'premium_expiry': user_data.get('premium_expiry'),
                    'preferred_language': user_data.get('preferred_language', 'ja')
                }
                print(f"Safe user data to return: {safe_user_data}")
                
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps(safe_user_data)
                }
            else:
                # ユーザーが存在しない場合は作成してデフォルト値を返す
                print(f"User {user_id} not found in DynamoDB, creating new user")
                create_success = create_new_user(user_id, user_info.get('email', ''), user_info.get('display_name', ''))
                if create_success:
                    safe_user_data = {
                        'user_id': user_id,
                        'email': user_info.get('email', ''),
                        'display_name': user_info.get('display_name', ''),
                        'user_type': 'free',
                        'monthly_analysis_count': 0,
                        'total_analysis_count': 0,
                        'premium_expiry': None,
                        'preferred_language': 'ja'
                    }
                    return {
                        'statusCode': 200,
                        'headers': headers,
                        'body': json.dumps(safe_user_data)
                    }
                else:
                    return {
                        'statusCode': 500,
                        'headers': headers,
                        'body': json.dumps({'error': 'Failed to create user'})
                    }
        except Exception as e:
            print(f"Database error: {str(e)}")
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': f'Database error: {str(e)}'})
            }
        
    except Exception as e:
        print(f"User info retrieval error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'User info retrieval failed: {str(e)}'})
        }


def handle_verify_token(event, headers):
    """
    Cognitoトークン検証
    """
    try:
        user_info = get_user_from_token(event)
        
        if user_info:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'valid': True,
                    'user_id': user_info['user_id'],
                    'email': user_info.get('email', ''),
                    'display_name': user_info.get('display_name', '')
                })
            }
        else:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({
                    'valid': False,
                    'error': 'Invalid or expired token'
                })
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'valid': False,
                'error': f'Token verification failed: {str(e)}'
            })
        }


def get_user_from_token(event):
    """
    Cognitoトークンからユーザー情報を取得（緊急ログイントークン対応）
    """
    try:
        # Authorization ヘッダーから JWT トークン取得
        auth_header = event.get('headers', {}).get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            print("No Bearer token found in Authorization header")
            return None
        
        access_token = auth_header.split(' ')[1]
        print(f"Processing token: {access_token[:50]}...")
        
        # 緊急ログイン用トークンのチェック
        if access_token == 'emergency-login-token':
            print("Emergency login token detected")
            return {
                'user_id': 'emergency-user',
                'email': 'emergency@test.com',
                'display_name': 'Emergency User',
                'auth_provider': 'emergency'
            }
        
        # CognitoでJWTトークンを検証してユーザー情報取得
        response = cognito_client.get_user(AccessToken=access_token)
        print(f"Cognito user response: {response['Username']}")
        
        # ユーザー属性から情報抽出
        user_attributes = {attr['Name']: attr['Value'] for attr in response['UserAttributes']}
        
        user_info = {
            'user_id': response['Username'],  # CognitoのUsernameを user_id として使用
            'email': user_attributes.get('email', ''),
            'display_name': user_attributes.get('name', user_attributes.get('given_name', '')),
            'auth_provider': 'cognito'
        }
        
        print(f"Extracted user info: {user_info}")
        return user_info
        
    except cognito_client.exceptions.NotAuthorizedException as e:
        print(f"Token is invalid or expired: {str(e)}")
        return None
    except Exception as e:
        print(f"Error getting user from token: {str(e)}")
        return None


def handle_signup_with_email(event, headers):
    """
    メール認証付きユーザー登録
    """
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').strip().lower()
        password = body.get('password', '').strip()
        display_name = body.get('display_name', '').strip()
        
        if not email or not password:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Email and password are required'})
            }
        
        # Cognitoユーザー作成
        response = cognito_client.sign_up(
            ClientId=os.environ.get('COGNITO_CLIENT_ID'),
            Username=email,
            Password=password,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'name', 'Value': display_name or email.split('@')[0]}
            ]
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'User registered successfully. Please check your email for confirmation code.',
                'user_sub': response['UserSub'],
                'confirmation_required': True
            })
        }
        
    except cognito_client.exceptions.UsernameExistsException:
        return {
            'statusCode': 409,
            'headers': headers,
            'body': json.dumps({'error': 'User already exists'})
        }
    except cognito_client.exceptions.InvalidParameterException as e:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': f'Invalid parameter: {str(e)}'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Signup failed: {str(e)}'})
        }


def handle_confirm_signup(event, headers):
    """
    メール認証コード確認
    """
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').strip().lower()
        confirmation_code = body.get('confirmation_code', '').strip()
        
        if not email or not confirmation_code:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Email and confirmation code are required'})
            }
        
        # 認証コード確認
        cognito_client.confirm_sign_up(
            ClientId=os.environ.get('COGNITO_CLIENT_ID'),
            Username=email,
            ConfirmationCode=confirmation_code
        )
        
        # 確認後、自動ログインしてトークン取得
        auth_response = cognito_client.initiate_auth(
            ClientId=os.environ.get('COGNITO_CLIENT_ID'),
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': body.get('password', '')  # フロントエンドから送信される必要
            }
        )
        
        # DynamoDBにユーザーレコード作成
        user_response = cognito_client.get_user(
            AccessToken=auth_response['AuthenticationResult']['AccessToken']
        )
        
        user_attributes = {attr['Name']: attr['Value'] for attr in user_response['UserAttributes']}
        create_new_user(
            user_response['Username'],
            user_attributes.get('email', ''),
            user_attributes.get('name', ''),
            'cognito'
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Email confirmed successfully',
                'tokens': auth_response['AuthenticationResult'],
                'user_info': {
                    'user_id': user_response['Username'],
                    'email': user_attributes.get('email', ''),
                    'display_name': user_attributes.get('name', '')
                }
            })
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
            'body': json.dumps({'error': 'Confirmation code expired'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Confirmation failed: {str(e)}'})
        }


def handle_login_with_email(event, headers):
    """
    メール・パスワードログイン
    """
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').strip().lower()
        password = body.get('password', '').strip()
        
        if not email or not password:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Email and password are required'})
            }
        
        # Cognitoログイン
        auth_response = cognito_client.initiate_auth(
            ClientId=os.environ.get('COGNITO_CLIENT_ID'),
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password
            }
        )
        
        # ユーザー情報取得
        user_response = cognito_client.get_user(
            AccessToken=auth_response['AuthenticationResult']['AccessToken']
        )
        
        user_attributes = {attr['Name']: attr['Value'] for attr in user_response['UserAttributes']}
        user_id = user_response['Username']
        
        # 最終ログイン更新
        update_last_login(user_id)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Login successful',
                'tokens': auth_response['AuthenticationResult'],
                'user_info': {
                    'user_id': user_id,
                    'email': user_attributes.get('email', ''),
                    'display_name': user_attributes.get('name', '')
                }
            })
        }
        
    except cognito_client.exceptions.NotAuthorizedException:
        return {
            'statusCode': 401,
            'headers': headers,
            'body': json.dumps({'error': 'Invalid email or password'})
        }
    except cognito_client.exceptions.UserNotConfirmedException:
        return {
            'statusCode': 403,
            'headers': headers,
            'body': json.dumps({'error': 'User not confirmed. Please check your email for confirmation code.'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Login failed: {str(e)}'})
        }


def handle_resend_confirmation_code(event, headers):
    """
    認証コード再送信
    """
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').strip().lower()
        
        if not email:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Email is required'})
            }
        
        # 認証コード再送信
        cognito_client.resend_confirmation_code(
            ClientId=os.environ.get('COGNITO_CLIENT_ID'),
            Username=email
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Confirmation code resent successfully. Please check your email.'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Resend failed: {str(e)}'})
        }


def update_last_login(user_id):
    """
    最終ログイン時刻更新
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(f"{os.environ.get('PROJECT_NAME', 'ai-tourism-poc')}-users-{os.environ.get('STAGE', 'dev')}")
        
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='SET last_login_at = :timestamp, updated_at = :timestamp',
            ExpressionAttributeValues={
                ':timestamp': get_jst_isoformat()
            }
        )
        
        print(f"Last login updated for user: {user_id}")
        return True
        
    except Exception as e:
        print(f"Error updating last login: {e}")
        return False