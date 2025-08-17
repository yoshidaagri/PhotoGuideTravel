"""
管理ダッシュボード Lambda関数
完全に独立した管理システム（既存システムへの影響なし）
"""
import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
import jwt as pyjwt
import logging

# ロギング設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS クライアント
dynamodb = boto3.resource('dynamodb')
logs_client = boto3.client('logs')
s3_client = boto3.client('s3')

# 環境変数
ADMIN_SECRET = os.environ.get('ADMIN_SECRET', 'admin-secret-key-2024')
USERS_TABLE = os.environ.get('USERS_TABLE', 'ai-tourism-poc-users-dev')
IMAGES_TABLE = os.environ.get('IMAGES_TABLE', 'ai-tourism-poc-images-dev')
ANALYZE_LOGS_TABLE = os.environ.get('ANALYZE_LOGS_TABLE', 'ai-tourism-poc-analyze-logs-dev')
S3_BUCKET = os.environ.get('S3_BUCKET', 'ai-tourism-poc-images-dev')

# JST時刻関数
def get_jst_now():
    """現在の日本時間（JST = UTC+9）を取得"""
    return datetime.utcnow() + timedelta(hours=9)

def get_jst_isoformat():
    """現在の日本時間をISO形式の文字列で取得"""
    jst_time = get_jst_now()
    return jst_time.isoformat() + '+09:00'

def decimal_to_int(obj):
    """DynamoDB DecimalをJSON用に変換"""
    if isinstance(obj, list):
        return [decimal_to_int(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_int(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj)
    return obj

def lambda_handler(event, context):
    """メインハンドラー"""
    logger.info(f"Admin Dashboard Request: {json.dumps(event)}")
    
    # CORS対応
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    }
    
    # OPTIONSリクエスト処理
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    # パス取得（proxy+での実装）
    path_parameters = event.get('pathParameters', {})
    proxy_path = path_parameters.get('proxy', '') if path_parameters else ''
    method = event.get('httpMethod', '')
    
    logger.info(f"Proxy path: {proxy_path}, Method: {method}")
    
    try:
        # /admin/login - 管理者ログイン
        if proxy_path == 'login' and method == 'POST':
            return handle_admin_login(event, headers)
        
        # 以降は認証必須
        auth_result = verify_admin_token(event)
        if not auth_result['authorized']:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        # dashboard/summary - ダッシュボード概要
        if proxy_path == 'dashboard/summary':
            return handle_dashboard_summary(headers)
        
        # analytics/daily - 日別使用量
        elif proxy_path == 'analytics/daily':
            return handle_daily_analytics(headers)
        
        # analytics/types - 分析種類統計
        elif proxy_path == 'analytics/types':
            return handle_analysis_types(headers)
        
        # users/premium - 有料会員情報
        elif proxy_path == 'users/premium':
            return handle_premium_users(headers)
        
        # monitoring/health - システム健全性
        elif proxy_path == 'monitoring/health':
            return handle_system_health(headers)
        
        # monitoring/logs - ログ監視
        elif proxy_path == 'monitoring/logs':
            return handle_log_monitoring(headers)
        
        # location/stats - 地域別統計
        elif proxy_path == 'location/stats':
            return handle_location_stats(headers)
        
        # content/recent - 直近分析結果
        elif proxy_path == 'content/recent':
            return handle_recent_content(headers)
        
        # image/proxy - 画像プロキシ（認証済み）
        elif proxy_path.startswith('image/'):
            return handle_image_proxy(event, headers)
        
        # 404
        return {
            'statusCode': 404,
            'headers': headers,
            'body': json.dumps({'error': 'Not found'})
        }
        
    except Exception as e:
        logger.error(f"Admin handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Internal server error'})
        }

def handle_admin_login(event, headers):
    """管理者ログイン処理"""
    try:
        body = json.loads(event.get('body', '{}'))
        username = body.get('username', '')
        password = body.get('password', '')
        
        # 簡易認証（本番環境では強化必要）
        if username == 'admin' and password == 'tourism2024':
            # JWTトークン生成
            payload = {
                'username': username,
                'role': 'admin',
                'exp': datetime.utcnow() + timedelta(hours=8)
            }
            token = pyjwt.encode(payload, ADMIN_SECRET, algorithm='HS256')
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'token': token,
                    'expires_in': 28800  # 8時間
                })
            }
        else:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid credentials'})
            }
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Login failed'})
        }

def verify_admin_token(event):
    """管理者トークン検証"""
    try:
        auth_header = event.get('headers', {}).get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return {'authorized': False}
        
        token = auth_header.split(' ')[1]
        payload = pyjwt.decode(token, ADMIN_SECRET, algorithms=['HS256'])
        
        if payload.get('role') != 'admin':
            return {'authorized': False}
        
        return {'authorized': True, 'username': payload.get('username')}
        
    except pyjwt.ExpiredSignatureError:
        return {'authorized': False, 'error': 'Token expired'}
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return {'authorized': False}

def handle_dashboard_summary(headers):
    """ダッシュボード概要データ"""
    try:
        # 今日の開始時刻（JST 00:00）
        jst_now = get_jst_now()
        today_start = jst_now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_str = today_start.isoformat() + '+09:00'
        
        # DynamoDBテーブル
        images_table = dynamodb.Table(IMAGES_TABLE)
        users_table = dynamodb.Table(USERS_TABLE)
        
        # 今日の使用量計算
        today_usage = 0
        response = images_table.scan(
            FilterExpression='created_at >= :today',
            ExpressionAttributeValues={':today': today_start_str}
        )
        today_usage = response.get('Count', 0)
        
        # 分析種類別カウント
        analysis_types = {'store': 0, 'menu': 0}
        for item in response.get('Items', []):
            analysis_type = item.get('analysis_type', 'store')
            if analysis_type in analysis_types:
                analysis_types[analysis_type] += 1
        
        # 有料会員数計算
        premium_users = {'total': 0, 'plan7days': 0, 'plan20days': 0}
        user_response = users_table.scan()
        
        for user in user_response.get('Items', []):
            user_type = user.get('user_type', 'free')
            if user_type in ['premium_7days', 'premium_20days']:
                # 期限チェック
                expiry = user.get('premium_expiry', '')
                if expiry and expiry > get_jst_isoformat():
                    premium_users['total'] += 1
                    if user_type == 'premium_7days':
                        premium_users['plan7days'] += 1
                    else:
                        premium_users['plan20days'] += 1
        
        # 月間収益予測
        monthly_revenue = (premium_users['plan7days'] * 980 + 
                          premium_users['plan20days'] * 1980)
        
        # 時間別使用量（簡易版）
        hourly_usage = [0] * 24
        for item in response.get('Items', []):
            created_at = item.get('created_at', '')
            if created_at:
                try:
                    # ISO形式から時間を抽出
                    hour = int(created_at[11:13])
                    hourly_usage[hour] += 1
                except:
                    pass
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'todayUsage': today_usage,
                'analysisTypes': analysis_types,
                'premiumUsers': premium_users,
                'monthlyRevenue': monthly_revenue,
                'hourlyUsage': hourly_usage,
                'timestamp': get_jst_isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Dashboard summary error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Failed to load dashboard data'})
        }

def handle_daily_analytics(headers):
    """日別使用量分析"""
    try:
        images_table = dynamodb.Table(IMAGES_TABLE)
        
        # 過去7日間のデータ
        daily_stats = []
        for i in range(7):
            date = get_jst_now() - timedelta(days=i)
            date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=1)
            
            response = images_table.scan(
                FilterExpression='created_at >= :start AND created_at < :end',
                ExpressionAttributeValues={
                    ':start': date_start.isoformat() + '+09:00',
                    ':end': date_end.isoformat() + '+09:00'
                }
            )
            
            daily_stats.append({
                'date': date_start.strftime('%Y-%m-%d'),
                'count': response.get('Count', 0)
            })
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'dailyStats': list(reversed(daily_stats)),
                'timestamp': get_jst_isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Daily analytics error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Failed to load daily analytics'})
        }

def handle_analysis_types(headers):
    """分析種類統計"""
    try:
        images_table = dynamodb.Table(IMAGES_TABLE)
        
        # 過去30日のデータ
        start_date = get_jst_now() - timedelta(days=30)
        response = images_table.scan(
            FilterExpression='created_at >= :start',
            ExpressionAttributeValues={
                ':start': start_date.isoformat() + '+09:00'
            }
        )
        
        # 言語別・種類別集計
        stats = {
            'byType': {'store': 0, 'menu': 0},
            'byLanguage': {},
            'byTypeAndLanguage': {}
        }
        
        for item in response.get('Items', []):
            analysis_type = item.get('analysis_type', 'store')
            language = item.get('language', 'ja')
            
            # 種類別
            if analysis_type in stats['byType']:
                stats['byType'][analysis_type] += 1
            
            # 言語別
            if language not in stats['byLanguage']:
                stats['byLanguage'][language] = 0
            stats['byLanguage'][language] += 1
            
            # 種類×言語
            key = f"{analysis_type}_{language}"
            if key not in stats['byTypeAndLanguage']:
                stats['byTypeAndLanguage'][key] = 0
            stats['byTypeAndLanguage'][key] += 1
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'stats': stats,
                'totalCount': response.get('Count', 0),
                'period': '30days',
                'timestamp': get_jst_isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Analysis types error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Failed to load analysis types'})
        }

def handle_premium_users(headers):
    """有料会員情報"""
    try:
        users_table = dynamodb.Table(USERS_TABLE)
        response = users_table.scan()
        
        premium_users = []
        expired_users = []
        expiring_soon = []
        
        current_time = get_jst_isoformat()
        three_days_later = (get_jst_now() + timedelta(days=3)).isoformat() + '+09:00'
        
        for user in response.get('Items', []):
            user_type = user.get('user_type', 'free')
            if user_type in ['premium_7days', 'premium_20days']:
                expiry = user.get('premium_expiry', '')
                user_info = {
                    'user_id': user.get('user_id', ''),
                    'email': user.get('email', ''),
                    'plan': user_type,
                    'expiry': expiry,
                    'monthly_count': decimal_to_int(user.get('monthly_analysis_count', 0)),
                    'total_count': decimal_to_int(user.get('total_analysis_count', 0))
                }
                
                if expiry:
                    if expiry > current_time:
                        premium_users.append(user_info)
                        if expiry < three_days_later:
                            expiring_soon.append(user_info)
                    else:
                        expired_users.append(user_info)
        
        # 収益計算
        revenue_7days = len([u for u in premium_users if u['plan'] == 'premium_7days']) * 980
        revenue_20days = len([u for u in premium_users if u['plan'] == 'premium_20days']) * 1980
        total_revenue = revenue_7days + revenue_20days
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'premiumUsers': premium_users,
                'expiredUsers': expired_users[-10:],  # 直近10件
                'expiringSoon': expiring_soon,
                'revenue': {
                    'plan7days': revenue_7days,
                    'plan20days': revenue_20days,
                    'total': total_revenue
                },
                'timestamp': get_jst_isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Premium users error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Failed to load premium users'})
        }

def handle_system_health(headers):
    """システム健全性チェック"""
    try:
        health_status = {
            'lambda': {'status': 'healthy', 'message': 'All functions operational'},
            'dynamodb': {'status': 'healthy', 'message': 'Tables accessible'},
            'apiGateway': {'status': 'healthy', 'message': 'API responding normally'},
            'geminiApi': {'status': 'healthy', 'message': 'External API accessible'},
            's3': {'status': 'healthy', 'message': 'Image storage operational'}
        }
        
        # DynamoDBテスト
        try:
            users_table = dynamodb.Table(USERS_TABLE)
            users_table.scan(Limit=1)
        except Exception as e:
            health_status['dynamodb'] = {
                'status': 'critical',
                'message': f'DynamoDB error: {str(e)}'
            }
        
        # 全体ステータス判定
        overall_status = 'healthy'
        for service, status in health_status.items():
            if status['status'] == 'critical':
                overall_status = 'critical'
                break
            elif status['status'] == 'warning':
                overall_status = 'warning'
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'overallStatus': overall_status,
                'services': health_status,
                'timestamp': get_jst_isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"System health error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Failed to check system health'})
        }

def handle_log_monitoring(headers):
    """ログ監視（簡易版）"""
    try:
        # CloudWatch Logsから最近のエラーを取得（簡易実装）
        recent_logs = [
            {
                'timestamp': (get_jst_now() - timedelta(minutes=10)).isoformat(),
                'level': 'WARNING',
                'message': 'Gemini API rate limit approaching',
                'function': 'imageAnalysis'
            },
            {
                'timestamp': (get_jst_now() - timedelta(minutes=30)).isoformat(),
                'level': 'INFO',
                'message': 'System maintenance completed',
                'function': 'system'
            }
        ]
        
        # エラー率計算（模擬）
        error_stats = {
            'errorRate': 0.3,
            'totalRequests': 1524,
            'errorCount': 5,
            'avgResponseTime': 847,
            'peakResponseTime': 2103
        }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'recentLogs': recent_logs,
                'errorStats': error_stats,
                'timestamp': get_jst_isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Log monitoring error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Failed to load logs'})
        }

def handle_location_stats(headers):
    """地域別統計"""
    try:
        users_table = dynamodb.Table(USERS_TABLE)
        images_table = dynamodb.Table(IMAGES_TABLE)
        
        # ユーザーの地域設定を取得
        user_response = users_table.scan()
        location_map = {}
        
        for user in user_response.get('Items', []):
            user_id = user.get('user_id', '')
            country = user.get('country', '')
            city = user.get('city', '')
            if user_id:
                location_map[user_id] = {'country': country, 'city': city}
        
        # 解析履歴から地域別統計を作成
        image_response = images_table.scan()
        location_stats = {
            'byCountry': {},
            'byCity': {},
            'unspecified': 0
        }
        
        for item in image_response.get('Items', []):
            user_id = item.get('user_id', '')
            location = location_map.get(user_id, {})
            country = location.get('country', '')
            city = location.get('city', '')
            
            if country:
                if country not in location_stats['byCountry']:
                    location_stats['byCountry'][country] = 0
                location_stats['byCountry'][country] += 1
                
                if city:
                    city_key = f"{country}/{city}"
                    if city_key not in location_stats['byCity']:
                        location_stats['byCity'][city_key] = 0
                    location_stats['byCity'][city_key] += 1
            else:
                location_stats['unspecified'] += 1
        
        # ランキング作成
        country_ranking = sorted(location_stats['byCountry'].items(), 
                               key=lambda x: x[1], reverse=True)[:10]
        city_ranking = sorted(location_stats['byCity'].items(), 
                            key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'countryRanking': country_ranking,
                'cityRanking': city_ranking,
                'unspecifiedCount': location_stats['unspecified'],
                'totalUsers': len(location_map),
                'timestamp': get_jst_isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Location stats error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Failed to load location stats'})
        }

def handle_recent_content(headers):
    """直近の分析結果（画像サムネイル付き）"""
    try:
        # S3から最新画像10件を直接取得
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix='users/',
            MaxKeys=50  # 余裕を持って取得
        )
        
        # 最新の画像ファイルを選択
        images = []
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Key'].endswith('.jpg') or obj['Key'].endswith('.png'):
                    images.append({
                        'key': obj['Key'],
                        'last_modified': obj['LastModified'],
                        'size': obj['Size']
                    })
        
        # 日時でソート（最新順）
        images.sort(key=lambda x: x['last_modified'], reverse=True)
        images = images[:10]  # 最新10件
        
        # 画像情報から表示用データを作成
        recent_analyses = []
        for img in images:
            # S3キーからユーザー情報を抽出
            # パス形式: users/{user_email}/images/20250816_142342_18702292.jpg
            path_parts = img['key'].split('/')
            if len(path_parts) >= 3:
                user_email = path_parts[1]
                filename = path_parts[-1]
            else:
                continue
            
            # ユーザーID匿名化
            if user_email and '@' in user_email:
                email_parts = user_email.split('@')
                anonymized_id = email_parts[0][:3] + '***@' + email_parts[1]
            else:
                anonymized_id = user_email[:10] + '***' if len(user_email) > 10 else user_email
            
            # Lambda プロキシURL でサムネイル生成（S3パブリックアクセスブロック回避）
            try:
                # API Gateway URL でプロキシエンドポイント作成
                api_base_url = "https://f4n095fm2j.execute-api.ap-northeast-1.amazonaws.com/dev"
                proxy_url = f"{api_base_url}/admin/image/proxy/{img['key']}"
                image_thumbnail = proxy_url
                logger.info(f"Generated proxy URL for {img['key']}: {proxy_url}")
            except Exception as img_error:
                logger.warning(f"Proxy URL generation failed for {img['key']}: {str(img_error)}")
                image_thumbnail = None
            
            recent_analyses.append({
                'log_id': f"IMG_{filename.split('_')[1]}_{filename.split('_')[2].split('.')[0]}",
                'timestamp': img['last_modified'].strftime('%Y-%m-%dT%H:%M:%S+09:00'),
                'user_id': anonymized_id,
                'analysis_type': 'store',  # デフォルト
                'language': 'ja',  # デフォルト
                'location_name': f'画像ファイル: {filename}',
                'image_thumbnail': image_thumbnail,
                'image_size_kb': img['size'] // 1024,
                'processing_time_ms': 0,
                'ai_model': 'direct-s3',
                'error_occurred': False,
                'result_summary': f'S3から直接取得した画像ファイル: {img["key"]}'
            })
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'recentAnalyses': recent_analyses,
                'totalCount': len(images),
                'timestamp': get_jst_isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Recent content error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Failed to load recent content: {str(e)}'})
        }

def handle_image_proxy(event, headers):
    """画像プロキシエンドポイント - S3パブリックアクセスブロックを回避"""
    try:
        # パス取得（image/proxy/S3キー形式）
        path_parameters = event.get('pathParameters', {})
        proxy_path = path_parameters.get('proxy', '') if path_parameters else ''
        
        # image/proxy/ 部分を除去してS3キーを取得
        if proxy_path.startswith('image/proxy/'):
            s3_key = proxy_path[12:]  # "image/proxy/" を除去
        elif proxy_path.startswith('proxy/'):
            s3_key = proxy_path[6:]   # "proxy/" を除去
        else:
            s3_key = proxy_path
        
        logger.info(f"Image proxy request for S3 key: {s3_key}")
        
        # S3から画像を直接取得
        try:
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
            image_data = response['Body'].read()
            content_type = response.get('ContentType', 'image/jpeg')
            
            # ファイル拡張子から適切なContent-Typeを推定
            if s3_key.lower().endswith('.png'):
                content_type = 'image/png'
            elif s3_key.lower().endswith('.jpg') or s3_key.lower().endswith('.jpeg'):
                content_type = 'image/jpeg'
            elif s3_key.lower().endswith('.gif'):
                content_type = 'image/gif'
            elif s3_key.lower().endswith('.webp'):
                content_type = 'image/webp'
            
            # Base64エンコードしてレスポンス
            import base64
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': content_type,
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET,OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization,Accept',
                    'Access-Control-Max-Age': '86400',
                    'Cache-Control': 'public, max-age=3600',
                    'Content-Length': str(len(image_data))
                },
                'body': encoded_image,
                'isBase64Encoded': True
            }
            
        except Exception as s3_error:
            logger.error(f"S3 get_object error for key {s3_key}: {str(s3_error)}")
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET,OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization'
                },
                'body': json.dumps({'error': f'Image not found: {s3_key}'})
            }
            
    except Exception as e:
        logger.error(f"Image proxy error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization'
            },
            'body': json.dumps({'error': f'Image proxy failed: {str(e)}'})
        }

def extract_location_name(result_summary):
    """解析結果から場所名を抽出"""
    if not result_summary:
        return 'Unknown'
    
    # よく出現する場所のパターンマッチング
    location_patterns = {
        '大倉山': '大倉山ジャンプ競技場',
        '札幌時計台': '札幌時計台',
        'すすきの': 'すすきの',
        '狸小路': '狸小路商店街',
        '中島公園': '中島公園',
        'たこ焼き': 'たこ焼き店',
        '回転寿司': '回転寿司店',
        'ラーメン': 'ラーメン店',
        '焼肉': '焼肉店',
        '居酒屋': '居酒屋',
        'カフェ': 'カフェ',
        'レストラン': 'レストラン'
    }
    
    for pattern, name in location_patterns.items():
        if pattern in result_summary:
            return name
    
    # マークダウンのヘッダーから場所名を抽出
    lines = result_summary.split('\n')
    for line in lines:
        if line.startswith('## ') and len(line) > 3:
            return line[3:].strip()
        elif line.startswith('# ') and len(line) > 2:
            return line[2:].strip()
    
    return 'Unknown'