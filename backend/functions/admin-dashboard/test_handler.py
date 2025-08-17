"""
管理ダッシュボード Lambda関数 - テスト版
"""
import json
import logging

# ロギング設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """テスト用ハンドラー"""
    logger.info("Test Admin Dashboard Request received")
    
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
        # /admin/login - 管理者ログイン（簡易版）
        if proxy_path == 'login' and method == 'POST':
            try:
                body_str = event.get('body', '{}')
                logger.info(f"Raw body: {body_str}")
                
                body = json.loads(body_str)
                username = body.get('username', '')
                password = body.get('password', '')
                
                logger.info(f"Parsed username: {username}")
                
                if username == 'admin' and password == 'tourism2024':
                    return {
                        'statusCode': 200,
                        'headers': headers,
                        'body': json.dumps({
                            'token': 'test-token-' + str(abs(hash(username))),
                            'expires_in': 28800
                        })
                    }
                else:
                    return {
                        'statusCode': 401,
                        'headers': headers,
                        'body': json.dumps({'error': 'Invalid credentials'})
                    }
            except json.JSONDecodeError as je:
                logger.error(f"JSON decode error: {str(je)}")
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': f'JSON parse error: {str(je)}'})
                }
        
        # その他のパス
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Test endpoint',
                'proxy_path': proxy_path,
                'method': method
            })
        }
        
    except Exception as e:
        logger.error(f"Test handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Test error: {str(e)}'})
        }