import json
import boto3
import stripe
import os
from datetime import datetime, timedelta

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
    決済処理メイン関数
    Stripe決済の処理とDynamoDB記録
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
        
        # Stripe設定
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        # パス解析
        path = event.get('path', '').split('/')[-1]
        method = event.get('httpMethod')
        
        # ルーティング
        if method == 'POST':
            if path == 'create-payment-intent':
                return handle_create_payment_intent(event, headers)
            elif path == 'confirm-payment':
                return handle_confirm_payment(event, headers)
        elif method == 'GET':
            if path == 'history':
                return handle_payment_history(event, headers)
        
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


def handle_create_payment_intent(event, headers):
    """
    Stripe PaymentIntent作成
    """
    try:
        body = json.loads(event.get('body', '{}'))
        amount = body.get('amount')  # 円単位
        currency = body.get('currency', 'jpy')
        user_id = body.get('userId')
        service_type = body.get('serviceType', 'image_analysis')
        
        if not amount or not user_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Amount and userId are required'})
            }
        
        # PaymentIntent作成
        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount),
            currency=currency,
            metadata={
                'userId': user_id,
                'serviceType': service_type
            }
        )
        
        # DynamoDBに記録
        save_payment_record(
            user_id=user_id,
            payment_id=payment_intent.id,
            amount=amount,
            currency=currency,
            service_type=service_type,
            status='created'
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'clientSecret': payment_intent.client_secret,
                'paymentId': payment_intent.id
            })
        }
        
    except stripe.error.StripeError as e:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


def handle_confirm_payment(event, headers):
    """
    決済確認処理
    """
    try:
        body = json.loads(event.get('body', '{}'))
        payment_intent_id = body.get('paymentIntentId')
        
        if not payment_intent_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'PaymentIntent ID is required'})
            }
        
        # PaymentIntent状態確認
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if payment_intent.status == 'succeeded':
            # DynamoDB更新
            update_payment_status(
                user_id=payment_intent.metadata.get('userId'),
                payment_id=payment_intent_id,
                status='succeeded'
            )
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'status': 'succeeded',
                    'message': 'Payment confirmed successfully'
                })
            }
        else:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'status': payment_intent.status,
                    'message': 'Payment not completed'
                })
            }
            
    except stripe.error.StripeError as e:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


def handle_payment_history(event, headers):
    """
    決済履歴取得
    """
    try:
        user_id = event.get('queryStringParameters', {}).get('userId')
        
        if not user_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'userId is required'})
            }
        
        # DynamoDBから履歴取得
        history = get_payment_history(user_id)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'userId': user_id,
                'payments': history
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


def save_payment_record(user_id, payment_id, amount, currency, service_type, status):
    """
    決済記録をDynamoDBに保存
    """
    dynamodb = boto3.resource('dynamodb')
    table_name = f"ai-tourism-poc-payment-history-{os.environ.get('STAGE', 'dev')}"
    table = dynamodb.Table(table_name)
    
    item = {
        'userId': user_id,
        'paymentId': payment_id,
        'amount': amount,
        'currency': currency,
        'serviceType': service_type,
        'status': status,
        'createdAt': get_jst_isoformat(),
        'updatedAt': get_jst_isoformat()
    }
    
    table.put_item(Item=item)


def update_payment_status(user_id, payment_id, status):
    """
    決済ステータス更新
    """
    dynamodb = boto3.resource('dynamodb')
    table_name = f"ai-tourism-poc-payment-history-{os.environ.get('STAGE', 'dev')}"
    table = dynamodb.Table(table_name)
    
    table.update_item(
        Key={
            'userId': user_id,
            'paymentId': payment_id
        },
        UpdateExpression='SET #status = :status, updatedAt = :timestamp',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': status,
            ':timestamp': get_jst_isoformat()
        }
    )


def get_payment_history(user_id):
    """
    ユーザーの決済履歴取得
    """
    dynamodb = boto3.resource('dynamodb')
    table_name = f"ai-tourism-poc-payment-history-{os.environ.get('STAGE', 'dev')}"
    table = dynamodb.Table(table_name)
    
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('userId').eq(user_id),
        ScanIndexForward=False  # 新しい順
    )
    
    return response.get('Items', [])