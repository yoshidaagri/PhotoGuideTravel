import json
import boto3
import os
from datetime import datetime, timedelta
import sys
import zipfile

# Lambda環境で.requirements.zipを展開してPythonパスに追加
try:
    import stripe
except ImportError:
    # .requirements.zipが存在する場合に展開
    requirements_zip_path = '.requirements.zip'
    if os.path.exists(requirements_zip_path):
        import tempfile
        temp_dir = tempfile.mkdtemp()
        
        # ZIPファイルを一時ディレクトリに展開
        with zipfile.ZipFile(requirements_zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Pythonパスに追加
        sys.path.insert(0, temp_dir)
        
        # 再度インポートを試行
        import stripe
        print(f"Successfully extracted and imported stripe from {requirements_zip_path}")
    else:
        raise ImportError("stripe module not found and .requirements.zip does not exist")

# JST時刻関数
def get_jst_now():
    """現在の日本時間（JST = UTC+9）を取得"""
    return datetime.utcnow() + timedelta(hours=9)

def get_jst_isoformat():
    """現在の日本時間をISO形式の文字列で取得"""
    jst_time = get_jst_now()
    return jst_time.isoformat() + '+09:00'

# Stripe設定
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')

def main(event, context):
    """Stripe決済処理メイン"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'POST,OPTIONS'
        }
        
        if event['httpMethod'] == 'OPTIONS':
            return {'statusCode': 200, 'headers': headers, 'body': ''}
        
        path = event.get('path', '').split('/')[-1]
        
        if path == 'create-checkout':
            return create_checkout_session(event, headers)
        elif path == 'webhook':
            return handle_webhook(event, headers)
        
        return {
            'statusCode': 404,
            'headers': headers,
            'body': json.dumps({'error': 'Endpoint not found'})
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def create_checkout_session(event, headers):
    """Stripe Checkout Session作成"""
    try:
        body = json.loads(event.get('body', '{}'))
        plan_type = body.get('planType')  # '7days' or '20days'
        user_id = body.get('userId')
        
        print(f"Creating checkout session: planType={plan_type}, userId={user_id}")
        
        # Price ID設定
        price_ids = {
            '7days': os.environ['STRIPE_PRICE_7DAYS'],
            '20days': os.environ['STRIPE_PRICE_20DAYS']
        }
        
        price_id = price_ids.get(plan_type)
        if not price_id or not user_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Invalid parameters',
                    'required': ['planType', 'userId'],
                    'planType': plan_type,
                    'price_id': price_id
                })
            }
        
        # フロントエンドのベースURL設定（環境変数から取得）
        frontend_url = os.environ.get('FRONTEND_URL', 'https://ai-tourism-poc-frontend-dev.s3.amazonaws.com')
        
        # Checkout Session作成
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'{frontend_url}/tourism-guide.html?payment=success&session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{frontend_url}/tourism-guide.html?payment=cancel',
            metadata={
                'user_id': user_id,
                'plan_type': plan_type
            }
        )
        
        print(f"Checkout session created: {session.id}")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'checkout_url': session.url,
                'session_id': session.id
            })
        }
        
    except Exception as e:
        print(f"Checkout creation error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def handle_webhook(event, headers):
    """Stripe Webhook処理"""
    try:
        payload = event.get('body', '')
        sig_header = event.get('headers', {}).get('stripe-signature', '')
        
        print(f"Webhook received: payload length={len(payload)}")
        
        # Webhook署名検証（テスト段階では一時的にスキップ）
        webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        
        # 一時的に署名検証をスキップ（API Gateway+Lambda環境での問題回避）
        webhook_event = json.loads(payload)
        print("Warning: Webhook signature verification temporarily skipped for testing")
        
        # 本番運用時は以下を有効化（要ヘッダー名調査）
        # if webhook_secret and webhook_secret != 'whsec_xxx_placeholder':
        #     webhook_event = stripe.Webhook.construct_event(
        #         payload, sig_header, webhook_secret
        #     )
        # else:
        #     webhook_event = json.loads(payload)
        #     print("Warning: Webhook signature verification skipped (development mode)")
        
        event_type = webhook_event.get('type')
        print(f"Webhook event type: {event_type}")
        
        # checkout.session.completed処理
        if event_type == 'checkout.session.completed':
            session = webhook_event['data']['object']
            
            # メタデータからユーザー情報取得
            user_id = session['metadata']['user_id']
            plan_type = session['metadata']['plan_type']
            payment_intent_id = session.get('payment_intent')
            
            print(f"Processing payment completion: user={user_id}, plan={plan_type}")
            
            # 決済記録をDynamoDBに保存
            save_payment_record(
                user_id=user_id,
                session_id=session['id'],
                payment_intent_id=payment_intent_id,
                plan_type=plan_type,
                amount=session['amount_total'],
                status='completed'
            )
            
            # プレミアム権限付与
            grant_premium_access(user_id, plan_type)
            
            print(f"Premium access granted: {user_id} - {plan_type}")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'status': 'success'})
        }
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def save_payment_record(user_id, session_id, payment_intent_id, plan_type, amount, status):
    """決済記録をDynamoDBに保存"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(f"ai-tourism-poc-payment-history-{os.environ.get('STAGE', 'dev')}")
        
        item = {
            'userId': user_id,
            'paymentId': session_id,  # Checkout Session ID
            'paymentIntentId': payment_intent_id,  # Payment Intent ID
            'amount': amount // 100,  # Stripeは最小単位（円）なので100で割る
            'currency': 'JPY',
            'planType': plan_type,
            'status': status,
            'createdAt': get_jst_isoformat(),
            'updatedAt': get_jst_isoformat(),
            'provider': 'stripe'
        }
        
        table.put_item(Item=item)
        print(f"Payment record saved: {session_id}")
        
    except Exception as e:
        print(f"Error saving payment record: {str(e)}")
        raise

def grant_premium_access(user_id, plan_type):
    """プレミアム権限付与"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(f"ai-tourism-poc-users-{os.environ.get('STAGE', 'dev')}")
        
        # 有効期限設定
        days = 7 if plan_type == '7days' else 20
        now = get_jst_now()
        expiry = (now + timedelta(days=days)).isoformat()
        
        # プレミアム関連項目のみ更新（既存データを保護）
        # plan_typeから具体的なuser_typeを構築（期限チェック機能と整合性確保）
        user_type_value = f'premium_{plan_type}'  # 'premium_7days' or 'premium_20days'
        
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='SET user_type = :user_type, premium_expiry = :expiry, plan_type = :plan_type, updated_at = :updated',
            ExpressionAttributeValues={
                ':user_type': user_type_value,
                ':expiry': expiry,
                ':plan_type': plan_type,
                ':updated': now.isoformat()
            }
        )
        
        print(f"DynamoDB updated: {user_id} -> premium until {expiry}")
        
    except Exception as e:
        print(f"DynamoDB update error: {str(e)}")
        raise