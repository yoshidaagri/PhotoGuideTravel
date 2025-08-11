import boto3
import json
from datetime import datetime, timedelta
from decimal import Decimal
import os

# JST時刻関数
def get_jst_now():
    """現在の日本時間（JST = UTC+9）を取得"""
    return datetime.utcnow() + timedelta(hours=9)

def get_jst_isoformat():
    """現在の日本時間をISO形式の文字列で取得"""
    jst_time = get_jst_now()
    return jst_time.isoformat() + '+09:00'

def check_usage_limit(user_id, user_type='free'):
    """
    ユーザーの解析使用制限をチェック
    
    Args:
        user_id (str): Cognito User ID
        user_type (str): 'free', 'premium_7days', 'premium_20days'
    
    Returns:
        dict: 使用可否と残り回数
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        
        # ユーザーテーブルから情報取得
        users_table = dynamodb.Table(f"{os.environ.get('PROJECT_NAME', 'ai-tourism-poc')}-users-{os.environ.get('STAGE', 'dev')}")
        
        try:
            user_response = users_table.get_item(Key={'user_id': user_id})
            if 'Item' not in user_response:
                # 新規ユーザーの場合、レコード作成
                create_new_user(user_id)
                user_data = {
                    'user_type': 'free',
                    'monthly_analysis_count': 0,
                    'premium_expiry': None
                }
            else:
                user_data = user_response['Item']
        except Exception as e:
            print(f"Error getting user data: {e}")
            # エラー時は新規ユーザー扱い
            create_new_user(user_id)
            user_data = {
                'user_type': 'free',
                'monthly_analysis_count': 0,
                'premium_expiry': None
            }
        
        current_user_type = user_data.get('user_type', 'free')
        
        # 無料ユーザーの制限チェック
        if current_user_type == 'free':
            return check_free_user_limit(user_id, user_data)
        
        # プレミアムユーザーの期限チェック
        elif current_user_type in ['premium_7days', 'premium_20days']:
            return check_premium_user_validity(user_id, user_data)
        
        else:
            # 不明なユーザータイプは無料扱い
            return check_free_user_limit(user_id, user_data)
            
    except Exception as e:
        print(f"Usage check error: {str(e)}")
        # エラー時は使用可能（安全側に倒す）
        return {
            'allowed': True,
            'remaining': 5,
            'user_type': 'free',
            'message': 'システムエラー: 一時的に制限なしで利用可能'
        }

def check_free_user_limit(user_id, user_data):
    """無料ユーザーの月5回制限チェック"""
    try:
        monthly_count = int(user_data.get('monthly_analysis_count', 0))
        
        if monthly_count >= 5:
            return {
                'allowed': False,
                'remaining': 0,
                'user_type': 'free',
                'message': '無料プランでは月5回まで解析可能です。プレミアムプランにアップグレードしてください。',
                'upgrade_required': True
            }
        
        return {
            'allowed': True,
            'remaining': 5 - monthly_count,
            'user_type': 'free',
            'message': f'残り{5 - monthly_count}回利用可能です。'
        }
        
    except Exception as e:
        print(f"Free user check error: {e}")
        return {
            'allowed': True,
            'remaining': 5,
            'user_type': 'free',
            'message': 'カウントエラー: 利用可能'
        }

def check_premium_user_validity(user_id, user_data):
    """プレミアムユーザーの期限チェック"""
    try:
        premium_expiry = user_data.get('premium_expiry')
        if not premium_expiry:
            # 期限がない場合は無料ユーザー扱い
            return check_free_user_limit(user_id, user_data)
        
        # 期限チェック
        if isinstance(premium_expiry, str):
            expiry_date = datetime.fromisoformat(premium_expiry.replace('Z', '+00:00'))
        else:
            expiry_date = premium_expiry
            
        current_time = datetime.now()
        
        if current_time > expiry_date:
            # 期限切れ → 無料ユーザーに降格
            downgrade_to_free(user_id)
            return {
                'allowed': False,
                'remaining': 0,
                'user_type': 'free',
                'message': 'プレミアムプランの期限が切れました。再度プレミアムプランにアップグレードしてください。',
                'upgrade_required': True
            }
        
        # プレミアムユーザー: 無制限利用可能
        days_remaining = (expiry_date - current_time).days
        return {
            'allowed': True,
            'remaining': -1,  # -1 = unlimited
            'user_type': user_data.get('user_type', 'premium_7days'),
            'message': f'プレミアムプラン利用中（残り{days_remaining}日）',
            'days_remaining': days_remaining
        }
        
    except Exception as e:
        print(f"Premium user check error: {e}")
        # エラー時は無料ユーザー扱い
        return check_free_user_limit(user_id, user_data)

def create_new_user(user_id, email='', display_name='', auth_provider='cognito'):
    """新規ユーザー作成"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(f"{os.environ.get('PROJECT_NAME', 'ai-tourism-poc')}-users-{os.environ.get('STAGE', 'dev')}")
        
        timestamp = get_jst_isoformat()
        
        item = {
            'user_id': user_id,
            'email': email,
            'auth_provider': auth_provider,
            'display_name': display_name,
            'profile_picture': '',
            'preferred_language': 'ja',
            'user_type': 'free',
            'premium_expiry': None,
            'monthly_analysis_count': 0,
            'total_analysis_count': 0,
            'last_login_at': timestamp,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        table.put_item(Item=item)
        print(f"New user created: {user_id}")
        return item
        
    except Exception as e:
        print(f"Error creating new user: {e}")
        return None

def increment_usage_count(user_id):
    """解析使用回数を増加"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(f"{os.environ.get('PROJECT_NAME', 'ai-tourism-poc')}-users-{os.environ.get('STAGE', 'dev')}")
        
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='ADD monthly_analysis_count :inc, total_analysis_count :inc SET updated_at = :updated',
            ExpressionAttributeValues={
                ':inc': 1,
                ':updated': get_jst_isoformat()
            }
        )
        
        print(f"Usage count incremented for user: {user_id}")
        return True
        
    except Exception as e:
        print(f"Error incrementing usage: {e}")
        return False

def downgrade_to_free(user_id):
    """プレミアムユーザーを無料ユーザーに降格"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(f"{os.environ.get('PROJECT_NAME', 'ai-tourism-poc')}-users-{os.environ.get('STAGE', 'dev')}")
        
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='SET user_type = :type, premium_expiry = :expiry, updated_at = :updated',
            ExpressionAttributeValues={
                ':type': 'free',
                ':expiry': None,
                ':updated': get_jst_isoformat()
            }
        )
        
        print(f"User downgraded to free: {user_id}")
        return True
        
    except Exception as e:
        print(f"Error downgrading user: {e}")
        return False