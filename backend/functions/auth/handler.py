import json
import boto3
import hashlib
import jwt
import os
from datetime import datetime, timedelta


def main(event, context):
    """
    認証メイン関数
    ユーザー登録・ログイン・トークン検証
    """
    try:
        # CORS headers
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        }
        
        if event['httpMethod'] == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': ''
            }
        
        # パス解析
        path = event.get('path', '').split('/')[-1]
        method = event.get('httpMethod')
        
        # ルーティング
        if method == 'POST':
            if path == 'register':
                return handle_register(event, headers)
            elif path == 'login':
                return handle_login(event, headers)
            elif path == 'refresh':
                return handle_refresh_token(event, headers)
        elif method == 'GET':
            if path == 'verify':
                return handle_verify_token(event, headers)
        
        return {
            'statusCode': 404,
            'headers': headers,
            'body': json.dumps({'error': 'Endpoint not found'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


def handle_register(event, headers):
    """
    ユーザー登録処理
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
        
        # 既存ユーザー確認
        existing_user = get_user_by_email(email)
        if existing_user:
            return {
                'statusCode': 409,
                'headers': headers,
                'body': json.dumps({'error': 'User already exists'})
            }
        
        # ユーザー作成
        user_id = create_user(email, password, name)
        token = generate_jwt_token(user_id, email)
        
        return {
            'statusCode': 201,
            'headers': headers,
            'body': json.dumps({
                'userId': user_id,
                'email': email,
                'name': name,
                'token': token,
                'message': 'User registered successfully'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


def handle_login(event, headers):
    """
    ログイン処理
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
        
        # ユーザー認証
        user = authenticate_user(email, password)
        if not user:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid credentials'})
            }
        
        # JWT トークン生成
        token = generate_jwt_token(user['userId'], user['email'])
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'userId': user['userId'],
                'email': user['email'],
                'name': user.get('name', ''),
                'token': token,
                'message': 'Login successful'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


def handle_verify_token(event, headers):
    """
    トークン検証
    """
    try:
        auth_header = event.get('headers', {}).get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid authorization header'})
            }
        
        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)
        
        if not payload:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid or expired token'})
            }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'valid': True,
                'userId': payload['userId'],
                'email': payload['email']
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


def create_user(email, password, name):
    """
    新規ユーザーをDynamoDBに作成
    """
    dynamodb = boto3.resource('dynamodb')
    table_name = f"ai-tourism-poc-users-{os.environ.get('STAGE', 'dev')}"
    table = dynamodb.Table(table_name)
    
    user_id = hashlib.sha256(f"{email}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    item = {
        'userId': user_id,
        'email': email,
        'passwordHash': password_hash,
        'name': name,
        'createdAt': datetime.now().isoformat(),
        'lastLogin': datetime.now().isoformat()
    }
    
    table.put_item(Item=item)
    return user_id


def get_user_by_email(email):
    """
    メールアドレスでユーザー検索
    """
    dynamodb = boto3.resource('dynamodb')
    table_name = f"ai-tourism-poc-users-{os.environ.get('STAGE', 'dev')}"
    table = dynamodb.Table(table_name)
    
    # GSI が必要（実装時に追加）
    # 今回は簡易実装として全スキャン（本番環境では非推奨）
    response = table.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr('email').eq(email)
    )
    
    items = response.get('Items', [])
    return items[0] if items else None


def authenticate_user(email, password):
    """
    ユーザー認証
    """
    user = get_user_by_email(email)
    if not user:
        return None
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if user['passwordHash'] != password_hash:
        return None
    
    # ログイン時刻を更新
    update_last_login(user['userId'])
    
    return user


def update_last_login(user_id):
    """
    最終ログイン時刻更新
    """
    dynamodb = boto3.resource('dynamodb')
    table_name = f"ai-tourism-poc-users-{os.environ.get('STAGE', 'dev')}"
    table = dynamodb.Table(table_name)
    
    table.update_item(
        Key={'userId': user_id},
        UpdateExpression='SET lastLogin = :timestamp',
        ExpressionAttributeValues={':timestamp': datetime.now().isoformat()}
    )


def generate_jwt_token(user_id, email):
    """
    JWT トークン生成
    """
    payload = {
        'userId': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    
    secret_key = os.environ.get('JWT_SECRET', 'default-secret-key')
    return jwt.encode(payload, secret_key, algorithm='HS256')


def verify_jwt_token(token):
    """
    JWT トークン検証
    """
    try:
        secret_key = os.environ.get('JWT_SECRET', 'default-secret-key')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None