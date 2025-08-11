import json
import boto3
import base64
import os
from datetime import datetime
from decimal import Decimal
import google.generativeai as genai

# Usage checking functions (imported from auth handler)
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
            ExpressionAttributeValues={':inc': 1, ':updated': datetime.now().isoformat()}
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
        
        timestamp = datetime.now().isoformat()
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
        cognito_client = boto3.client('cognito-idp', region_name='ap-northeast-1')
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
        
    except Exception as e:
        print(f"Error getting user from token: {str(e)}")
        return None


def main(event, context):
    """
    AI画像解析メイン関数
    Google Gemini APIを使用した画像解析とDynamoDB記録
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
            return {
                'statusCode': 200,
                'headers': headers,
                'body': ''
            }
        
        # ユーザー認証とID取得
        user_info = get_user_from_token(event)
        if not user_info:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({'error': 'Authentication required'})
            }
        
        user_id = user_info['user_id']
        print(f"Processing image analysis for user: {user_id}")
        
        # 使用制限チェック
        usage_check = check_usage_limit(user_id)
        print(f"Usage check result: {usage_check}")
        
        if not usage_check['allowed']:
            return {
                'statusCode': 403,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Usage limit exceeded',
                    'message': 'Free上限に達しました。アップグレードをお願いします',
                    'user_type': usage_check['user_type'],
                    'remaining': 0,
                    'upgrade_required': True
                })
            }
        
        # リクエスト解析
        body = json.loads(event.get('body', '{}'))
        image_data = body.get('image')
        language = body.get('language', 'en')
        
        if not image_data:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Image data is required'})
            }
        
        # Google Gemini API呼び出し
        analysis_result = analyze_image_with_gemini(image_data, language)
        
        # 解析成功時のみ使用回数を増加
        if not analysis_result.get('error', False):
            increment_result = increment_usage_count(user_id)
            print(f"Usage count increment result: {increment_result}")
        
        # DynamoDB記録
        save_analysis_log(user_id, analysis_result, image_data)
        
        # 使用状況を結果に追加
        updated_usage = check_usage_limit(user_id)
        analysis_result['usage_info'] = {
            'remaining': updated_usage.get('remaining', 0),
            'user_type': updated_usage.get('user_type', 'free'),
            'message': updated_usage.get('message', '')
        }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(analysis_result)
        }
        
    except Exception as e:
        print(f"Error in image analysis: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


def analyze_image_with_gemini(image_data, language='en'):
    """
    Google Gemini APIを使用した画像解析
    """
    try:
        # Gemini API設定
        genai.configure(api_key=os.environ.get('GOOGLE_GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Base64画像データをデコード
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        # プロンプト作成（言語別）
        prompts = {
            'en': """Analyze this travel/tourism image and provide:
1. Location identification (if recognizable)
2. Cultural and historical significance
3. Tourist information and tips
4. Interesting facts
5. Best photo spots nearby

Please be informative and engaging for travelers.""",
            
            'ja': """この旅行・観光の画像を分析して以下を提供してください：
1. 場所の特定（認識可能な場合）
2. 文化的・歴史的意義
3. 観光情報とコツ
4. 興味深い事実
5. 近くの撮影スポット

旅行者にとって有益で魅力的な情報をお願いします。""",
            
            'ko': """이 여행/관광 이미지를 분석하고 다음을 제공해주세요:
1. 장소 식별 (인식 가능한 경우)
2. 문화적 및 역사적 의미
3. 관광 정보 및 팁
4. 흥미로운 사실
5. 근처의 사진 촬영 명소

여행자들에게 유익하고 매력적인 정보를 제공해주세요."""
        }
        
        prompt = prompts.get(language, prompts['en'])
        
        # Gemini API 호출
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])
        
        return {
            'analysis': response.text,
            'language': language,
            'timestamp': datetime.now().isoformat(),
            'model': 'gemini-2.0-flash-exp'
        }
        
    except Exception as e:
        print(f"Gemini API error: {str(e)}")
        return {
            'analysis': f'Image analysis failed: {str(e)}',
            'language': language,
            'timestamp': datetime.now().isoformat(),
            'error': True
        }


def save_analysis_log(user_id, result, image_data):
    """
    分析結果をDynamoDBに保存
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table_name = f"ai-tourism-poc-analysis-history-{os.environ.get('STAGE', 'dev')}"
        table = dynamodb.Table(table_name)
        
        # 画像データサイズを記録（完全なデータは保存しない）
        image_size = len(image_data) if image_data else 0
        
        item = {
            'userId': user_id,
            'timestamp': datetime.now().isoformat(),
            'analysis': result.get('analysis', ''),
            'language': result.get('language', 'en'),
            'model': result.get('model', 'unknown'),
            'imageSize': image_size,
            'success': not result.get('error', False)
        }
        
        table.put_item(Item=item)
        
    except Exception as e:
        print(f"DynamoDB save error: {str(e)}")
        # エラーでも分析結果は返す