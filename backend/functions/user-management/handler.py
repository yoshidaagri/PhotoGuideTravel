import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal

# JST時刻関数
def get_jst_now():
    """現在の日本時間（JST = UTC+9）を取得"""
    return datetime.utcnow() + timedelta(hours=9)

def get_jst_isoformat():
    """現在の日本時間をISO形式の文字列で取得"""
    jst_time = get_jst_now()
    return jst_time.isoformat() + '+09:00'


def main(event, context):
    """
    ユーザー管理メイン関数
    ユーザー情報の取得・更新・削除
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
        path_parameters = event.get('pathParameters') or {}
        user_id = path_parameters.get('proxy', '').split('/')[-1]
        method = event.get('httpMethod')
        
        # ルーティング
        if method == 'GET':
            if user_id:
                return handle_get_user(user_id, headers)
            else:
                return handle_get_user_stats(event, headers)
        elif method == 'PUT':
            return handle_update_user(user_id, event, headers)
        elif method == 'DELETE':
            return handle_delete_user(user_id, headers)
        
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


def handle_get_user(user_id, headers):
    """
    ユーザー情報取得
    """
    try:
        if not user_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'User ID is required'})
            }
        
        user = get_user_by_id(user_id)
        if not user:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'User not found'})
            }
        
        # パスワードハッシュを除外
        user_info = {
            'userId': user['userId'],
            'email': user['email'],
            'name': user.get('name', ''),
            'createdAt': user.get('createdAt', ''),
            'lastLogin': user.get('lastLogin', ''),
            'analysisCount': user.get('analysisCount', 0),
            'totalSpent': float(user.get('totalSpent', 0))
        }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(user_info)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


def handle_update_user(user_id, event, headers):
    """
    ユーザー情報更新
    """
    try:
        if not user_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'User ID is required'})
            }
        
        body = json.loads(event.get('body', '{}'))
        name = body.get('name')
        
        if not name:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Name is required'})
            }
        
        # ユーザー存在確認
        user = get_user_by_id(user_id)
        if not user:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'User not found'})
            }
        
        # 更新実行
        update_user_info(user_id, name)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'userId': user_id,
                'message': 'User updated successfully'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


def handle_delete_user(user_id, headers):
    """
    ユーザー削除
    """
    try:
        if not user_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'User ID is required'})
            }
        
        # ユーザー存在確認
        user = get_user_by_id(user_id)
        if not user:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'User not found'})
            }
        
        # 削除実行
        delete_user_data(user_id)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'userId': user_id,
                'message': 'User deleted successfully'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


def handle_get_user_stats(event, headers):
    """
    ユーザー統計情報取得
    """
    try:
        user_id = event.get('queryStringParameters', {}).get('userId')
        
        if not user_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'userId parameter is required'})
            }
        
        stats = get_user_statistics(user_id)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(stats)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


def get_user_by_id(user_id):
    """
    ユーザーIDでユーザー取得
    """
    dynamodb = boto3.resource('dynamodb')
    table_name = f"ai-tourism-poc-users-{os.environ.get('STAGE', 'dev')}"
    table = dynamodb.Table(table_name)
    
    response = table.get_item(Key={'userId': user_id})
    return response.get('Item')


def update_user_info(user_id, name):
    """
    ユーザー情報更新
    """
    dynamodb = boto3.resource('dynamodb')
    table_name = f"ai-tourism-poc-users-{os.environ.get('STAGE', 'dev')}"
    table = dynamodb.Table(table_name)
    
    table.update_item(
        Key={'userId': user_id},
        UpdateExpression='SET #name = :name, updatedAt = :timestamp',
        ExpressionAttributeNames={'#name': 'name'},
        ExpressionAttributeValues={
            ':name': name,
            ':timestamp': get_jst_isoformat()
        }
    )


def delete_user_data(user_id):
    """
    ユーザーデータ削除（関連データも含む）
    """
    dynamodb = boto3.resource('dynamodb')
    stage = os.environ.get('STAGE', 'dev')
    
    # ユーザー情報削除
    users_table = dynamodb.Table(f"ai-tourism-poc-users-{stage}")
    users_table.delete_item(Key={'userId': user_id})
    
    # 分析履歴削除
    analysis_table = dynamodb.Table(f"ai-tourism-poc-analysis-history-{stage}")
    analysis_response = analysis_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('userId').eq(user_id)
    )
    
    for item in analysis_response.get('Items', []):
        analysis_table.delete_item(
            Key={
                'userId': user_id,
                'timestamp': item['timestamp']
            }
        )
    
    # 決済履歴削除
    payment_table = dynamodb.Table(f"ai-tourism-poc-payment-history-{stage}")
    payment_response = payment_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('userId').eq(user_id)
    )
    
    for item in payment_response.get('Items', []):
        payment_table.delete_item(
            Key={
                'userId': user_id,
                'paymentId': item['paymentId']
            }
        )


def get_user_statistics(user_id):
    """
    ユーザー統計情報取得
    """
    dynamodb = boto3.resource('dynamodb')
    stage = os.environ.get('STAGE', 'dev')
    
    # 分析回数
    analysis_table = dynamodb.Table(f"ai-tourism-poc-analysis-history-{stage}")
    analysis_response = analysis_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('userId').eq(user_id),
        Select='COUNT'
    )
    analysis_count = analysis_response.get('Count', 0)
    
    # 決済統計
    payment_table = dynamodb.Table(f"ai-tourism-poc-payment-history-{stage}")
    payment_response = payment_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('userId').eq(user_id),
        FilterExpression=boto3.dynamodb.conditions.Attr('status').eq('succeeded')
    )
    
    total_spent = sum(
        float(item.get('amount', 0)) for item in payment_response.get('Items', [])
    )
    payment_count = len(payment_response.get('Items', []))
    
    return {
        'userId': user_id,
        'analysisCount': analysis_count,
        'paymentCount': payment_count,
        'totalSpent': total_spent,
        'generatedAt': get_jst_isoformat()
    }