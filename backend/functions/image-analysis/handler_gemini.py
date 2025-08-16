import json
import os
import base64
import time
from datetime import datetime, timedelta
import urllib.request
import urllib.parse
import boto3
from decimal import Decimal

# JST時刻ユーティリティ関数（Lambda内実装）
def get_jst_now():
    """現在の日本時間（JST = UTC+9）を取得"""
    return datetime.utcnow() + timedelta(hours=9)

def get_jst_isoformat():
    """現在の日本時間をISO形式の文字列で取得"""
    jst_time = get_jst_now()
    return jst_time.isoformat() + '+09:00'

def get_jst_timestamp():
    """ファイル名用のタイムスタンプ（JST）を取得"""
    return get_jst_now().strftime('%Y%m%d_%H%M%S')

# Cognitoクライアント初期化
cognito_client = boto3.client('cognito-idp', region_name='ap-northeast-1')

# Usage checker functions
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

def increment_usage_count(user_id):
    """解析使用回数を増加"""
    try:
        import boto3
        from datetime import datetime
        
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
        
        print(f"DynamoDB: Usage count incremented for user: {user_id}")
        return True
        
    except Exception as e:
        print(f"DynamoDB Error: Failed to increment usage count for {user_id}: {e}")
        return False

def main(event, context):
    """
    実際のGemini APIを使用した画像解析関数（使用制限チェック付き）
    """
    start_time = time.time()  # Phase 6.9.6: 処理時間計測開始
    
    # Phase 6.9.6: ヘッダー確保（ログ保存でアクセスする場合もある）
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
    }
    
    try:
        
        if event['httpMethod'] == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': ''
            }
            
        # Cognito認証とユーザー情報取得
        user_info = get_user_from_token(event)
        if not user_info:
            # 緊急ログイントークンをチェック
            auth_header = event.get('headers', {}).get('Authorization', '')
            if auth_header == 'Bearer emergency-login-token':
                # 緊急ログイン用のダミーユーザー情報
                user_info = {
                    'user_id': 'emergency-user',
                    'email': 'emergency@test.com',
                    'display_name': 'Emergency User'
                }
            else:
                return {
                    'statusCode': 401,
                    'headers': headers,
                    'body': json.dumps({
                        'error': 'Authentication required',
                        'message': '画像解析にはログインが必要です。'
                    })
                }
        
        user_id = user_info['user_id']
        print(f"User ID for usage counting: {user_id}")
        print(f"User info: {user_info}")
        
        # 使用制限チェック
        usage_check = check_usage_limit(user_id)
        if not usage_check.get('allowed', False):
            return {
                'statusCode': 403,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Usage limit exceeded',
                    'message': usage_check.get('message', '使用制限に達しました'),
                    'remaining': usage_check.get('remaining', 0),
                    'user_type': usage_check.get('user_type', 'free'),
                    'upgrade_required': usage_check.get('upgrade_required', False)
                })
            }
        
        # リクエスト解析
        body = json.loads(event.get('body', '{}'))
        image_data = body.get('image')
        language = body.get('language', 'ja')
        analysis_type = body.get('type', 'store')  # 'store' or 'menu'
        image_id = body.get('imageId')  # フロントエンドから送信される画像ID
        s3_url = body.get('s3Url')      # S3 URL
        
        if not image_data:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Image data is required'})
            }
        
        # Gemini API呼び出し
        analysis_result = analyze_image_with_gemini_rest(image_data, language, analysis_type)
        
        # 解析成功時に使用回数を増加
        if analysis_result.get('status') == 'success':
            print(f"Analysis successful, incrementing usage count for user: {user_id}")
            increment_success = increment_usage_count(user_id)
            if increment_success:
                print(f"Successfully incremented usage count for user: {user_id}")
            else:
                print(f"Failed to increment usage count for user: {user_id}")
        
        # 解析結果をDynamoDBに保存（image_idがある場合のみ）
        if image_id and analysis_result.get('analysis'):
            update_image_with_analysis(image_id, analysis_result['analysis'])
        
        # 残り使用回数情報を含めて返却
        updated_usage_check = check_usage_limit(user_id)
        analysis_result['usage_info'] = {
            'remaining': updated_usage_check.get('remaining', -1),
            'user_type': updated_usage_check.get('user_type', 'free'),
            'message': updated_usage_check.get('message', '')
        }
        
        # メインレスポンス作成
        response = {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(analysis_result)
        }
        
        # Phase 6.9.6: 軽量同期ログ保存（50ms以内、フロントエンド影響最小）
        try:
            save_analysis_log(event, context, analysis_result, start_time, None, user_info)
        except Exception as log_error:
            print(f"Log save failed (ignored): {str(log_error)[:200]}")
        
        return response
        
    except Exception as e:
        print(f"Error in image analysis: {str(e)}")
        
        # メインエラーレスポンス作成
        error_response = {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
        
        # Phase 6.9.6: エラー時も軽量同期ログ保存
        try:
            if 'user_info' not in locals():
                user_info = {'user_id': 'unknown', 'email': 'unknown@unknown.com'}
            if 'start_time' not in locals():
                start_time = time.time()
            save_analysis_log(event, context, None, start_time, e, user_info)
        except Exception as log_error:
            print(f"Error log save failed (ignored): {str(log_error)[:200]}")
        
        return error_response


def get_user_from_token(event):
    """
    Cognitoトークンからユーザー情報を取得
    """
    try:
        # Authorization ヘッダーから JWT トークン取得
        auth_header = event.get('headers', {}).get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None
        
        access_token = auth_header.split(' ')[1]
        
        # CognitoでJWTトークンを検証してユーザー情報取得
        response = cognito_client.get_user(AccessToken=access_token)
        
        # ユーザー属性から情報抽出
        user_attributes = {attr['Name']: attr['Value'] for attr in response['UserAttributes']}
        
        user_info = {
            'user_id': response['Username'],  # CognitoのUsernameを user_id として使用
            'email': user_attributes.get('email', ''),
            'display_name': user_attributes.get('name', user_attributes.get('given_name', '')),
            'auth_provider': 'cognito'
        }
        
        return user_info
        
    except cognito_client.exceptions.NotAuthorizedException:
        print("Token is invalid or expired")
        return None
    except Exception as e:
        print(f"Error getting user from token: {str(e)}")
        return None


def analyze_image_with_gemini_rest(image_data, language='ja', analysis_type='store'):
    """
    REST APIでGemini APIを呼び出す（依存関係なし）
    """
    try:
        api_key = os.environ.get('GOOGLE_GEMINI_API_KEY')
        if not api_key or api_key == 'test':
            return generate_enhanced_mock_analysis(language, analysis_type)
        
        # Base64画像データをクリーン化
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        # 分析タイプ別プロンプト選択
        if analysis_type == 'menu':
            tourism_prompts = get_menu_analysis_prompts()
        else:
            tourism_prompts = get_store_tourism_prompts()
        
        # 分析タイプ別の要約指示を追加（一時的にOFF）
        base_prompt = tourism_prompts.get(language, tourism_prompts['ja'])
        
        # 要約指示機能を一時的に無効化
        # if analysis_type == 'menu':
        #     summary_instruction = get_menu_summary_instructions()
        # else:
        #     summary_instruction = get_store_summary_instructions()
        
        # 中国語の場合は特別強化（こちらは有効のまま）
        if language == 'zh':
            prompt = f"请用简体中文回答。{base_prompt}请确保回答完全使用简体中文。"
        elif language == 'zh-tw':
            prompt = f"請用繁體中文回答。{base_prompt}請確保回答完全使用繁體中文。"
        else:
            prompt = base_prompt
        
        # デバッグログ
        print(f"Analysis type: {analysis_type}, Language: {language}")
        print(f"Available languages in prompts: {list(tourism_prompts.keys())}")
        # print(f"Available languages in summary: {list(summary_instruction.keys())}")  # 要約指示機能OFF
        print(f"Selected base prompt starts with: {base_prompt[:100]}...")
        
        # === 分析タイプによるAPI分岐 ===
        if analysis_type == 'menu':
            # メニュー翻訳の場合は従来のAPIを使用（Search不要）
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
            
            # 中国語の場合は特別な設定を追加
            generation_config = {
                "temperature": 0.7,
                "topP": 0.8,
                "topK": 40,
                "maxOutputTokens": 2048,
            }
            
            # 中国語（簡体・繁体）を強制するための追加設定
            if language in ['zh', 'zh-tw']:
                generation_config["candidateCount"] = 1
                generation_config["stopSequences"] = []
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_data
                            }
                        }
                    ]
                }],
                "generationConfig": generation_config
            }
            
            # タイムアウトは標準の30秒
            timeout_seconds = 30
            model_name = 'gemini-2.0-flash-exp'
            search_enhanced = False
            
        else:  # analysis_type == 'store' または その他
            # 店舗・観光地分析の場合はSearch as a toolを使用
            url = f"https://generativelanguage.googleapis.com/v1alpha/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
            
            # 中国語の場合は特別な設定を追加
            generation_config = {
                "temperature": 0.7,
                "topP": 0.8,
                "topK": 40,
                "maxOutputTokens": 3000,  # 検索結果を含むため増量
            }
            
            # 中国語（簡体・繁体）を強制するための追加設定
            if language in ['zh', 'zh-tw']:
                generation_config["candidateCount"] = 1
                generation_config["stopSequences"] = []
            
            # プロンプトにWeb検索を活用する指示を追加
            search_enhanced_prompt = prompt + "\n\n必要に応じてWeb検索を活用し、店舗の営業時間、価格、最新情報を含めて回答してください。"
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": search_enhanced_prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_data
                            }
                        }
                    ]
                }],
                "tools": [{
                    "google_search": {}  # Search as a toolを有効化
                }],
                "generationConfig": generation_config
            }
            
            # タイムアウトは60秒（検索時間を考慮）
            timeout_seconds = 60
            model_name = 'gemini-2.0-flash-exp-with-search'
            search_enhanced = True
        # === 分析タイプによるAPI分岐終了 ===
        
        # HTTP リクエスト送信
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        # タイムアウトを分析タイプに応じて設定
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        # [DEBUG] レスポンス構造の確認
        print(f"=== GEMINI API RESPONSE DEBUG ===")
        print(f"Full response keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        if 'candidates' in result:
            print(f"Candidates count: {len(result['candidates'])}")
            if result['candidates']:
                candidate = result['candidates'][0]
                print(f"First candidate keys: {list(candidate.keys()) if isinstance(candidate, dict) else 'Not a dict'}")
                if 'content' in candidate:
                    print(f"Content keys: {list(candidate['content'].keys()) if isinstance(candidate['content'], dict) else 'No content dict'}")
                    if 'parts' in candidate['content']:
                        print(f"Parts count: {len(candidate['content']['parts'])}")
                        for i, part in enumerate(candidate['content']['parts']):
                            print(f"Part {i} keys: {list(part.keys()) if isinstance(part, dict) else 'Not a dict'}")
                            if 'text' in part:
                                print(f"Part {i} text preview: {part['text'][:100]}...")
        print(f"=== END DEBUG ===")
        
        # レスポンス解析
        if 'candidates' in result and result['candidates']:
            candidate = result['candidates'][0]
            analysis_text = ""
            
            # レスポンス構造を解析（Search as a toolの場合は複数partsの可能性）
            if 'content' in candidate and 'parts' in candidate['content']:
                parts = candidate['content']['parts']
                
                # Search as a toolを使用した場合（複数parts）
                if search_enhanced and len(parts) > 1:
                    # 複数partsがある場合は全て結合
                    for i, part in enumerate(parts):
                        if 'text' in part:
                            # パート間に改行を追加
                            if i > 0:
                                analysis_text += "\n\n"
                            analysis_text += part['text']
                else:
                    # 単一partの場合（通常のレスポンス）
                    for part in parts:
                        if 'text' in part:
                            analysis_text += part['text']
            
            # 解析テキストが取得できた場合
            if analysis_text:
                return {
                    'analysis': analysis_text,
                    'language': language,
                    'timestamp': get_jst_isoformat(),
                    'model': model_name,  # 分析タイプに応じたモデル名
                    'status': 'success',
                    'search_enhanced': search_enhanced  # 分析タイプに応じたフラグ
                }
            else:
                print("No text found in response parts, falling back to mock")
                return generate_enhanced_mock_analysis(language, analysis_type)
        else:
            return generate_enhanced_mock_analysis(language, analysis_type)
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"HTTP Error {e.code}: {error_body}")
        # 検索機能が使えない場合は通常のAPIにフォールバック [FALLBACK_LOGIC]
        if "v1alpha" in url and e.code in [400, 403, 404]:
            print("Search feature may not be available. Consider fallback to standard API.")
        return generate_enhanced_mock_analysis(language, analysis_type)
        
    except Exception as e:
        print(f"Gemini API error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return generate_enhanced_mock_analysis(language, analysis_type)


def update_image_with_analysis(image_id, analysis_result):
    """
    画像に解析結果を追加保存
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table_name = f"{os.environ.get('PROJECT_NAME', 'ai-tourism-poc')}-images-{os.environ.get('STAGE', 'dev')}"
        table = dynamodb.Table(table_name)
        
        # 返答文の先頭200文字を保存
        analysis_summary = analysis_result[:200] if analysis_result else ""
        response_truncated = len(analysis_result) > 200 if analysis_result else False
        
        table.update_item(
            Key={'image_id': image_id},
            UpdateExpression="SET analysis_summary = :summary, response_truncated = :truncated, #status = :status, analyzed_at = :analyzed_at",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':summary': analysis_summary,
                ':truncated': response_truncated,
                ':status': 'analyzed',
                ':analyzed_at': get_jst_isoformat()
            }
        )
        print(f"Successfully updated analysis for image_id: {image_id}")
        return True
    except Exception as e:
        print(f"Failed to update image analysis: {str(e)}")
        return False


def generate_enhanced_mock_analysis(language='ja', analysis_type='store'):
    """
    強化されたモック解析（Gemini API使用不可時）
    """
    mock_responses = {
        'ja': """🏔️ 観光AI解析結果 (実画像解析版)は現在メンテナンス中です。詳細は問い合わせフォームよりお願いします。""",

        'ko': """⚠️ 시스템 오류가 발생했습니다

현재 AI 분석 서비스가 일시적으로 이용할 수 없습니다.

**대처 방법:**
• 잠시 후 다시 시도해 주세요
• 네트워크 연결 상태를 확인해 주세요
• 문제가 지속되면 고객 지원팀에 문의해 주세요

이용에 불편을 드려 죄송합니다.""",

        'zh': """⚠️ 系统出现错误

AI分析服务暂时无法使用。

**解决方法：**
• 请稍后再试
• 检查网络连接状态
• 如问题持续，请联系客服

给您带来不便，深表歉意。""",

        'zh-tw': """🏔️ 觀光AI分析結果（實際圖像分析）目前正在維護中。詳情請透過諮詢表單聯絡我們。""",

        'en': """🏔️ Tourism AI Analysis (Real Image Analysis) is currently under maintenance. Please contact us through the inquiry form for details."""
    }

    analysis_text = mock_responses.get(language, mock_responses['ja'])

    return {
        'analysis': analysis_text,
        'language': language,
        'timestamp': get_jst_isoformat(),
        'model': 'tourism-ai-enhanced',
        'status': 'success'
    }


def get_store_tourism_prompts():
    """店舗・観光施設分析用プロンプト"""
    return {
        'ja': """あなたは地元の観光ガイドです。この画像を詳しく分析し、その地域の魅力を最大限に伝える観光ガイドとして800文字以内で回答してください。

**重要: 回答は必ずMarkdown形式で出力してください。見出しは##、太字は**、リストは-を使用してください。**

🏔️ **観光AI解析** 🏔️

**重要な分析指示:**
1. まず画像に写っている要素（建物、看板、人物、料理、風景など）を具体的に特定してください
2. 看板や文字が見える場合は、それを正確に読み取ってください
3. 建築様式、装飾、雰囲気から場所のタイプを推測してください
4. 店舗や場所の情報を提供する際は、以下のルールに従ってください：
   - 確実に分かる情報（看板の文字など）と推測を明確に区別する
   - 場所が特定できない場合は「場所は特定できません」と明記
   - 住所や詳細情報は「推測」「可能性」という言葉を必ず使用
5. 存在が確認できない情報は提供せず、「詳細は不明です」と回答
6. URLは絶対に創作せず、実在が100%確実な場合のみ掲載してください
7. 画像に映る看板は複数ある場合があるので、総合的に判断してください
8. 回答の初めから場所・エリアで開始して、はい分かりましたというような文章は入れないでください

**重要**: 存在しない情報を創作してはいけません。不明な点は「不明」と答えてください。

**📍 場所・エリア特定**
- 画像から読み取れる具体的な店名・施設名を明記
- 具体的な地区・エリアを特定
- 最寄り駅との位置関係
- 主要駅・空港からのアクセス情報
- 具体的な住所（判明している場合）

**🗣️ 言語サポート**
- 英語対応の可否とレベル
- 中国語・韓国語対応状況
- 翻訳アプリで見せるべき重要フレーズ

**💰 料金・アクセス情報**
- 入場料・価格帯：（画像から推測できる場合は現地通貨で表示）
- 料理の価格帯：（メニューが見える場合は具体的に）
- 追加料金：（ガイド・写真撮影・特別メニューなど）
- アクセス方法：（交通手段・所要時間）
- 営業時間：（看板等から読み取れる場合）
- 定休日：（判明している場合）
- 周辺の見どころ：（徒歩圏内の観光スポット）

**❄️ 季節別の準備**
- 現在の気温と適切な服装
- 路面状況と転倒防止対策
- 季節特有の注意点

**🌟 おすすめポイント**
- この場所・料理の特徴的な魅力
- 地元民からの評判
- 観光客に人気の理由
- 撮影スポットとしての価値

**⚠️ 注意事項**
- 混雑時間帯
- 予約の必要性
- 服装規定（あれば）
- 外国語対応状況
""",

        'ko': """당신은 지역 관광 가이드입니다. 이 이미지를 자세히 분석하고 그 지역의 매력을 최대한 전달하는 관광 가이드로서 800자 이내로 답변해주세요.

**중요: 반드시 Markdown 형식으로 답변해주세요. 제목은 ##, 굵은 글씨는 **, 목록은 -를 사용해주세요.**

🏔️ **관광 AI 분석** 🏔️

**중요한 분석 지시사항:**
1. 먼저 이미지에 보이는 요소(건물, 간판, 사람, 요리, 풍경 등)를 구체적으로 파악해주세요
2. 간판이나 문자가 보이면 그것을 정확히 읽어주세요
3. 건축 양식, 장식, 분위기로부터 장소의 타입을 추측해주세요
4. 점포나 장소의 정보를 제공할 때는 다음 규칙을 따라주세요:
   - 확실히 알 수 있는 정보(간판 문자 등)와 추측을 명확히 구별
   - 장소를 특정할 수 없는 경우 "장소를 특정할 수 없습니다"라고 명기
   - 주소나 상세 정보는 "추측" "가능성"이라는 단어를 반드시 사용
5. 존재를 확인할 수 없는 정보는 제공하지 말고 "상세 정보는 불명확합니다"라고 답변
6. URL은 절대로 창작하지 말고, 실재가 100% 확실한 경우에만 게재해주세요
7. 이미지에 나타나는 간판은 여러 개 있을 수 있으므로 종합적으로 판단해주세요.
8. 답변은 처음부터 장소・지역으로 시작하고, '네 알겠습니다'와 같은 문장은 넣지 마세요.

**중요**: 존재하지 않는 정보를 창작해서는 안 됩니다. 불명확한 점은 "불명확"이라고 답변해주세요.

**📍 위치・지역 특정**
- 이미지에서 읽을 수 있는 구체적인 점포명・시설명을 명기
- 구체적인 지구・지역 특정
- 가장 가까운 역과의 위치 관계
- 주요 역・공항에서의 접근 정보
- 구체적인 주소 (판명된 경우)

**🗣️ 언어 서포트**
- 영어 대응 가능 여부와 레벨
- 중국어・한국어 대응 상황
- 번역 앱으로 보여줄 중요한 프레이즈

**💰 요금・접근 정보**
- 입장료・가격대: (이미지에서 추측 가능한 경우 현지 통화로 표시)
- 요리 가격대: (메뉴가 보이는 경우 구체적으로)
- 추가요금: (가이드・사진촬영・특별메뉴 등)
- 접근방법: (교통수단・소요시간)
- 영업시간: (간판 등에서 읽을 수 있는 경우)
- 정기휴일: (판명된 경우)
- 주변 볼거리: (도보권 내 관광지)

**❄️ 계절별 준비사항**
- 현재 기온과 적절한 복장
- 노면 상황과 낙상 방지 대책
- 계절 특유의 주의점

**🌟 추천 포인트**
- 이 장소・요리의 특징적인 매력
- 현지인들의 평판
- 관광객에게 인기 있는 이유
- 촬영 스팟으로서의 가치

**⚠️ 주의사항**
- 혼잡 시간대
- 예약의 필요성
- 복장 규정 (있는 경우)
- 외국어 대응 상황

진정한 지역의 매력을 체험하고 잊을 수 없는 여행 추억을 만들어보세요!""",

        'zh': """您是地元旅游向导。请详细分析这张图像，作为旅游向导最大程度地传达该地区的魅力，请在800字以内回答。

**重要：请务必使用Markdown格式回答。标题使用##，粗体使用**，列表使用-。**

🏔️ **旅游AI分析** 🏔️

**重要分析指示：**
1. 首先请具体识别图像中显示的元素（建筑、招牌、人物、料理、风景等）
2. 如果能看到招牌或文字，请准确地读取它们
3. 从建筑风格、装饰、氛围推测场所的类型
4. 提供店铺或场所信息时，请遵循以下规则：
   - 明确区分确实可知的信息（招牌文字等）和推测
   - 如果无法特定场所，请明确说明"无法特定场所"
   - 地址或详细信息必须使用"推测""可能"等词汇
5. 无法确认存在的信息不要提供，请回答"详细信息不明"
6. 绝对不要创作URL，只有在100%确定实际存在时才提供
7. 图像中可能有多个招牌，请综合判断。
8. 请从场所・区域开始回答，不要加入"好的我明白了"之类的开场白。

**重要**：不得创作不存在的信息。不明确的内容请回答"不明确"。

**📍 地点・区域特定**
- 明确记载从图像中可读取的具体店名・设施名
- 特定具体地区・区域
- 与最近车站的位置关系
- 从主要车站・机场的交通信息
- 具体地址（如果能确定）

**🗣️ 语言支持**
- 英语应对可否及水平
- 中文・韩语应对状况
- 使用翻译APP时应展示的重要短语

**💰 费用・交通信息**
- 门票・价格区间：（如果能从图像推测，请用当地货币显示具体费用）
- 料理价格区间：（如果能看到菜单请具体说明）
- 附加费用：（导游・拍照・特别菜单等）
- 交通方式：（交通工具・所需时间）
- 营业时间：（如果能从招牌等读取）
- 定休日：（如果能确定）
- 周边景点：（步行范围内的观光景点）

**❄️ 季节性准备**
- 当前气温和适合的服装
- 路面状况和防滑对策
- 季节特有的注意事项

**🌟 推荐要点**
- 此地点・料理的特色魅力
- 当地人的评价
- 受游客欢迎的理由
- 作为拍照地点的价值

**⚠️ 注意事项**
- 拥挤时间段
- 预约的必要性
- 着装规定（如有）
- 外语应对状况

为您传达该地区的真正魅力，帮助您创造难忘的旅行回忆！""",

        'zh-tw': """您是地元旅遊向導。請詳細分析這張圖像，作為旅遊向導最大程度地傳達該地區的魅力，請在800字以內回答。

**重要：請務必使用Markdown格式回答。標題使用##，粗體使用**，列表使用-。**

🏔️ **旅遊AI分析** 🏔️

**重要分析指示：**
1. 首先請具體識別圖像中顯示的元素（建築、招牌、人物、料理、風景等）
2. 如果能看到招牌或文字，請準確地讀取它們
3. 從建築風格、裝飾、氛圍推測場所的類型
4. 提供店鋪或場所資訊時，請遵循以下規則：
   - 明確區分確實可知的資訊（招牌文字等）和推測
   - 如果無法特定場所，請明確說明「無法特定場所」
   - 地址或詳細資訊必須使用「推測」「可能」等詞彙
5. 無法確認存在的資訊不要提供，請回答「詳細資訊不明」
6. 絕對不要創作URL，只有在100%確定實際存在時才提供
7. 圖像中可能有多個招牌，請綜合判斷。
8. 請從場所・區域開始回答，不要加入「好的我明白了」之類的開場白。

**重要**：不得創作不存在的資訊。不明確的內容請回答「不明確」。

**📍 地點・區域特定**
- 明確記載從圖像中可讀取的具體店名・設施名
- 特定具體地區・區域
- 與最近車站的位置關係
- 從主要車站・機場的交通資訊
- 具體地址（如果能確定）

**🗣️ 語言支援**
- 英語應對可否及水準
- 中文・韓語應對狀況
- 使用翻譯APP時應展示的重要短語

**💰 費用・交通資訊**
- 門票・價格區間：（如果能從圖像推測，請用當地貨幣顯示具體費用）
- 料理價格區間：（如果能看到菜單請具體說明）
- 附加費用：（導遊・拍照・特別菜單等）
- 交通方式：（交通工具・所需時間）
- 營業時間：（如果能從招牌等讀取）
- 定休日：（如果能確定）
- 周邊景點：（步行範圍內的觀光景點）

**❄️ 季節性準備**
- 當前氣溫和適合的服裝
- 路面狀況和防滑對策
- 季節特有的注意事項

**🌟 推薦要點**
- 此地點・料理的特色魅力
- 當地人的評價
- 受遊客歡迎的理由
- 作為拍照地點的價值

**⚠️ 注意事項**
- 擁擠時間段
- 預約的必要性
- 著裝規定（如有）
- 外語應對狀況

為您傳達該地區的真正魅力，幫助您創造難忘的旅行回憶！""",

        'en': """You are a local tourism expert. Analyze this image in detail and provide comprehensive tourism guidance showcasing local attractions within 800 characters.

**Important: Please answer in Markdown format. Use ## for headings, ** for bold text, and - for lists.**

🏔️ **TOURISM AI ANALYSIS** 🏔️

**Important Analysis Instructions:**
1. First, specifically identify elements shown in the image (buildings, signs, people, food, scenery, etc.)
2. If signs or text are visible, read them accurately
3. Infer the type of location from architectural style, decorations, and atmosphere
4. When providing information about stores or locations, follow these rules:
   - Clearly distinguish between certain information (sign text, etc.) and speculation
   - If location cannot be identified, clearly state "Location cannot be determined"
   - For addresses or detailed information, always use words like "possibly" or "likely"
5. Do not provide information that cannot be confirmed to exist, answer "Details are unclear"
6. Never create URLs, only include them when 100% certain they exist
7. There may be multiple signs in the image, so please make a comprehensive judgment.
8. Start your response directly with the location/area, and do not include phrases like "Yes, I understand" at the beginning.

**Important**: Do not create non-existent information. Answer "unclear" for uncertain points.

**📍 Location & Area Identification**
- Clearly state specific store names/facility names readable from the image
- Identify specific districts/areas in the location
- Nearest subway stations (Nanboku, Tozai, Toho Lines) and location relationships
- Access from major transportation hubs
- Specific address (if determinable)

**🗣️ Language Support**
- English support availability and level
- Chinese/Korean language support status
- Important phrases to show using translation apps

**💰 Fee & Access Information**
- Admission fees/price range: (if inferable from image, show specific fees in local currency)
- Food price range: (if menu is visible, provide specifics)
- Additional charges: (guide, photography, special menus, etc.)
- Access methods: (transportation, travel time)
- Operating hours: (if readable from signs, etc.)
- Regular holidays: (if determinable)
- Nearby attractions: (tourist spots within walking distance)

**❄️ Seasonal Preparations**
- Current temperature and appropriate clothing
- Road conditions and slip prevention measures
- Season-specific precautions

**🌟 Recommended Points**
- Distinctive attractions of this location/cuisine
- Local reputation
- Reasons for tourist popularity
- Value as a photo spot

**⚠️ Important Notes**
- Crowded time periods
- Reservation necessity
- Dress codes (if any)
- Foreign language support status

Experience authentic local culture and create unforgettable travel memories!"""
    }


def get_menu_analysis_prompts():
    """看板・メニュー分析用プロンプト"""
    return {
        'ja': """あなたは地元の良識ある方で、海外の観光客を助けようとしています。この画像の看板・メニュー・文字情報を詳しく解析し、海外の観光客にも分かりやすく説明してください。

**重要: 回答は必ずMarkdown形式で出力してください。見出しは##、太字は**、リストは-を使用してください。**

🍜 **看板・メニューAI解析** 🍜

**📋 文字・看板情報の解析**
- 看板・メニューの日本語文字を正確に読み取り
- 店舗名・料理名・価格・説明文の翻訳
- 手書き文字・特殊フォントも可能な限り解読

**🍽️ 料理・メニュー詳細説明**
- 各料理の具材・調理法・特徴を詳しく説明
- アレルギー情報・辛さレベル・量の目安
- 地元ならではの特色料理の背景説明

**💰 料金・価格情報**
- メニューの価格を正確に読み取り
- 税込み・税別の表記確認
- セットメニュー・単品の価格比較
- 現地価格

**🗣️ 実用フレーズ・注文方法**
- 基本的な注文フレーズ（現地語・ローマ字・日本語併記）
- 「これください」「おすすめは？」「辛くしないでください」等
- 指差しで使えるフレーズ集

海外の方が地元グルメを安心して楽しめるよう、詳しくサポートします！""",

        'ko': """당신은 지역의 양심적인 분으로, 해외 관광객을 돕고자 합니다. 이 이미지의 간판・메뉴・문자 정보를 자세히 분석하고, 해외 관광객이 이해하기 쉽게 설명해주세요.

**중요: 반드시 Markdown 형식으로 답변해주세요. 제목은 ##, 굵은 글씨는 **, 목록은 -를 사용해주세요.**

🍜 **간판・메뉴 AI 분석** 🍜

**📋 문자・간판 정보 분석**
- 간판・메뉴의 일본어 문자 정확히 읽기
- 상점명・요리명・가격・설명문 번역
- 손글씨・특수 폰트도 최대한 해독

**🍽️ 요리・메뉴 상세 설명**
- 각 요리의 재료・조리법・특징 자세히 설명
- 알레르기 정보・매운 정도・양의 기준
- 지역 특색 요리의 배경 설명
- 추천 먹는 방법・조합

**💰 요금・가격 정보**
- 메뉴 가격 정확히 읽기
- 세금 포함・별도 표기 확인
- 세트 메뉴・단품 가격 비교
- 현지 가격 (원화 환산 참고)

**🗣️ 실용 문구・주문 방법**
- 기본 주문 문구 (현지어・로마자・한국어)
- "이것 주세요" "추천은?" "맵지 않게 해주세요" 등
- 손가락으로 가리켜 쓸 수 있는 문구집

해외 방문객이 지역 미식을 안심하고 즐길 수 있도록 자세히 지원합니다!""",

        'zh': """**【极其重要：必须用简体中文回答，绝对不要使用英语】**

您是地区的良心人士，想要帮助海外游客。请详细分析这张图像的招牌・菜单・文字信息，并向海外游客通俗易懂地说明。

**重要**: 请务必用简体中文回答，不要使用英语或其他语言。
**重要提醒**: 回答必须是简体中文，不可以是英语。
**MUST USE SIMPLIFIED CHINESE, NOT ENGLISH**

**重要：请务必使用Markdown格式回答。标题使用##，粗体使用**，列表使用-。**

🍜 **招牌・菜单AI分析** 🍜

**📋 文字・招牌信息分析**
- 准确读取招牌・菜单的文字
- 店名・菜名・价格・说明文翻译
- 手写字・特殊字体也尽量解读

**🍽️ 料理・菜单详细说明**
- 各菜品的食材・烹饪方法・特色详细说明
- 过敏信息・辣度・份量标准
- 地方特色料理的背景说明
- 推荐吃法・搭配

**💰 费用・价格信息**
- 准确读取菜单价格
- 确认含税・不含税标记
- 套餐・单品价格比较
- 当地价格 (人民币换算参考)

**🗣️ 实用短语・点餐方法**
- 基本点餐短语 (当地语言・罗马音・中文)
- "要这个" "推荐什么?" "请不要辣" 等
- 用手指着就能用的短语集

帮助海外游客安心享受地方美食，提供详细支持！

**【重要提醒：请确保您的回答完全使用简体中文，不要混入英语】**""",

        'zh-tw': """【極其重要：必須用繁體中文回答，絕對不要使用英語】

您是地區的良心人士，想要幫助海外遊客。請詳細分析這張圖像的招牌・菜單・文字資訊，並向海外遊客通俗易懂地說明。

**重要**: 請務必用繁體中文回答，不要使用英語或其他語言。
**重要提醒**: 回答必須是繁體中文，不可以是英語。
**MUST USE TRADITIONAL CHINESE, NOT ENGLISH**

**重要：請務必使用Markdown格式回答。標題使用##，粗體使用**，列表使用-。**

🍜 **招牌・菜單AI分析** 🍜

**📋 文字・招牌資訊分析**
- 準確讀取招牌・菜單的文字
- 店名・菜名・價格・說明文翻譯
- 手寫字・特殊字體也盡量解讀

**🍽️ 料理・菜單詳細說明**
- 各菜品的食材・烹飪方法・特色詳細說明
- 過敏資訊・辣度・份量標準
- 地方特色料理的背景說明
- 推薦吃法・搭配

**💰 費用・價格資訊**
- 準確讀取菜單價格
- 確認含稅・不含稅標記
- 套餐・單品價格比較
- 當地價格 (台幣換算參考)

**🗣️ 實用短語・點餐方法**
- 基本點餐短語 (當地語言・羅馬音・中文)
- 「要這個」「推薦什麼？」「請不要辣」等
- 用手指著就能用的短語集

幫助海外遊客安心享受當地美食，提供詳細支持！

**【重要提醒：請確保您的回答完全使用繁體中文，不要混入英語】**""",

        'en': """You are a conscientious local person who wants to help overseas tourists. Please analyze the signboard, menu, and text information in this image in detail, explaining it clearly for overseas tourists.

**Important: Please answer in Markdown format. Use ## for headings, ** for bold text, and - for lists.**

🍜 **SIGNBOARD & MENU AI ANALYSIS** 🍜

**📋 Text & Signboard Information Analysis**
- Accurately read characters and text on signs and menus
- Translation of store names, dish names, prices, and descriptions
- Decode handwritten text and special fonts as much as possible

**🍽️ Cuisine & Menu Detailed Explanation**
- Detailed explanation of ingredients, cooking methods, and characteristics of each dish
- Allergy information, spiciness level, portion size guidelines
- Background explanation of local and regional specialty dishes
- Recommended ways to eat and combinations

**💰 Fee & Price Information**
- Accurately read menu prices
- Check tax-inclusive/exclusive notation
- Set menu vs. single item price comparison
- Local prices (with USD conversion reference)

**🗣️ Practical Phrases & Ordering Methods**
- Basic ordering phrases (local language, romanization, English)
- "I'll have this", "What do you recommend?", "Not spicy please", etc.
- Phrase collection that can be used by pointing

Providing detailed support so overseas visitors can enjoy local gourmet with confidence!"""
    }


def get_store_summary_instructions():
    """店舗・観光地分析用要約指示"""
    return {
        'ja': "\n\n**重要**: 上記の分析内容を600文字以内で要約してください。\n\n**出力形式**:\n1. **📍場所・エリア**: 具体的な場所を特定\n2. **💡検索候補**: 不明な場合は類似スポット名を3つ提示\n\n特に場所が不明確な場合は、画像の特徴から推測できる候補地を具体的に提示してください。",
        'ko': "\n\n**중요**: 위 분석 내용을 600자 이내로 요약해주세요.\n\n**출력 형식**:\n1. **📍장소・지역**: 구체적 장소 특정\n2. **💡검색 후보**: 불명확한 경우 유사 스팟명 3개 제시\n\n특히 장소가 불명확한 경우, 이미지 특징에서 추측 가능한 후보지를 구체적으로 제시해주세요.",
        'zh': "\n\n**重要**: 请在600字内总结上述分析内容。\n\n**输出格式**:\n1. **📍场所・区域**: 具体场所特定\n2. **💡搜索候选**: 不明确时提供3个类似景点名\n\n特别是场所不明确时，请根据图像特征推测具体候选地点。",
        'zh-tw': "\n\n**重要**: 請在600字內總結上述分析內容。\n\n**輸出格式**:\n1. **📍場所・區域**: 具體場所特定\n2. **💡搜尋候選**: 不明確時提供3個類似景點名\n\n特別是場所不明確時，請根據圖像特徵推測具體候選地點。",
        'en': "\n\n**Important**: Summarize the above analysis within 600 characters.\n\n**Output Format**:\n1. **📍Location・Area**: Identify specific places\n2. **💡Search Candidates**: Provide 3 similar spot names if unclear\n\nEspecially when location is unclear, please suggest specific candidate locations based on image features."
    }


def get_menu_summary_instructions():
    """看板・メニュー分析用要約指示"""
    return {
        'ja': "\n\n**重要**: 上記の分析内容を600文字以内で要約してください。\n\n**出力形式**:\n1. **📋文字情報**: 看板・メニューから読み取った日本語文字と翻訳\n2. **🍽️料理詳細**: 各料理の具材・調理法・特徴・おすすめ\n3. **💰価格情報**: メニュー価格・税込/別・セット料金・お得情報\n4. **🗣️実用フレーズ**: 基本注文フレーズ・指差し会話・役立つ表現\n\n特に海外の方が安心して注文できるよう、具体的で実用的な情報を中心にまとめてください。",
        'ko': "\n\n**중요**: 위 분석 내용을 600자 이내로 요약해주세요.\n\n**출력 형식**:\n1. **📋문자정보**: 간판・메뉴에서 읽은 일본어 문자와 번역\n2. **🍽️요리상세**: 각 요리의 재료・조리법・특징・추천\n3. **💰가격정보**: 메뉴 가격・세금포함/별도・세트요금・할인정보\n4. **🗣️실용문구**: 기본 주문 문구・손가락 대화・유용한 표현\n\n특히 해외 방문객이 안심하고 주문할 수 있도록 구체적이고 실용적인 정보를 중심으로 정리해주세요.",
        'zh': "\n\n**重要**: 请在600字内总结上述分析内容。**必须用简体中文回答。**\n\n**输出格式**:\n1. **📋文字信息**: 招牌・菜单读取的日语文字和翻译\n2. **🍽️料理详情**: 各菜品的食材・烹饪法・特色・推荐\n3. **💰价格信息**: 菜单价格・含税/不含税・套餐费用・优惠信息\n4. **🗣️实用短语**: 基本点餐短语・手指对话・有用表达\n\n特别要让海外游客能够安心点餐，请以具体实用的信息为中心进行整理。**请务必使用简体中文回答，不要使用英语。**",
        'zh-tw': "\n\n**重要**: 請在600字內總結上述分析內容。**必須用繁體中文回答。**\n\n**輸出格式**:\n1. **📋文字資訊**: 招牌・菜單讀取的日語文字和翻譯\n2. **🍽️料理詳情**: 各菜品的食材・烹飪法・特色・推薦\n3. **💰價格資訊**: 菜單價格・含稅/不含稅・套餐費用・優惠資訊\n4. **🗣️實用短語**: 基本點餐短語・手指對話・有用表達\n\n特別要讓海外遊客能夠安心點餐，請以具體實用的資訊為中心進行整理。**請務必使用繁體中文回答，不要使用英語。**",
        'en': "\n\n**Important**: Summarize the above analysis within 600 characters.\n\n**Output Format**:\n1. **📋Text Information**: Japanese text read from signs/menus and translation\n2. **🍽️Cuisine Details**: Ingredients, cooking methods, characteristics, recommendations for each dish\n3. **💰Price Information**: Menu prices, tax inclusive/exclusive, set meal costs, discount info\n4. **🗣️Practical Phrases**: Basic ordering phrases, pointing conversation, useful expressions\n\nFocus on specific and practical information to help overseas visitors order with confidence."
    }


# ========== Phase 6.9.6: 解析ログ機能 ==========


def save_analysis_log(event, context, result, start_time, error, user_info):
    """
    解析ログをDynamoDBに軽量同期保存（50ms以内目標）
    """
    try:
        # Lambda環境のため、signalタイムアウトは使用しない（バックグラウンドスレッドで動作しないため）
        
        # 処理時間計算（safe）
        try:
            processing_time_ms = int((time.time() - start_time) * 1000)
        except:
            processing_time_ms = 0
        
        # ログID生成（safe）
        try:
            log_id = generate_sequential_id()
        except:
            log_id = f"ERR_{int(time.time() * 1000)}"
        
        # 基本情報収集（safe）
        try:
            request_context = event.get('requestContext', {})
            identity = request_context.get('identity', {})
            headers = event.get('headers', {})
            body = json.loads(event.get('body', '{}'))
        except:
            request_context = {}
            identity = {}
            headers = {}
            body = {}
        
        # 分析タイプのマッピング（safe）
        try:
            analysis_type_mapping = {
                'store': 1,  # 店舗・観光地分析
                'menu': 2    # 看板・メニュー翻訳
            }
            raw_analysis_type = body.get('type', 'store')
            bunseki_type = analysis_type_mapping.get(raw_analysis_type, 1)
        except:
            bunseki_type = 1
        
        # 結果サマリー（safe）
        try:
            kekka_summary = ""
            if result and 'analysis' in result:
                kekka_summary = str(result['analysis'])[:200]
        except:
            kekka_summary = ""
        
        # 画像情報（safe）
        try:
            image_data = body.get('image', '')
            gazo_size_kb = len(str(image_data).encode('utf-8')) // 1024 if image_data else 0
            gazo_format = detect_image_format(image_data)
        except:
            gazo_size_kb = 0
            gazo_format = 'unknown'
        
        # JST時刻（safe）
        try:
            jst_now = get_jst_now()
            ttl_timestamp = int((datetime.utcnow() + timedelta(days=365)).timestamp())
        except:
            jst_now = datetime.utcnow() + timedelta(hours=9)
            ttl_timestamp = int((datetime.utcnow() + timedelta(days=365)).timestamp())
        
        # ログエントリ作成（safe）
        log_entry = {
            'log_id': log_id,
            'timestamp': jst_now.isoformat() + '+09:00',
            'bunseki_type': bunseki_type,
            'kekka_summary': kekka_summary,
            'gazo_url': str(body.get('s3Url', ''))[:500],  # URL長制限
            'user_email': str(user_info.get('email', 'unknown@unknown.com'))[:100],
            
            # 監査情報（safe）
            'user_id': str(user_info.get('user_id', 'unknown'))[:100],
            'session_id': str(headers.get('x-session-id', 'unknown'))[:100],
            'request_id': str(request_context.get('requestId', 'unknown'))[:100],
            'ip_address': str(identity.get('sourceIp', 'unknown'))[:100],
            'user_agent': str(headers.get('User-Agent', ''))[:100],
            
            # 技術情報（safe）
            'lambda_function': str(getattr(context, 'function_name', 'unknown'))[:100],
            'ai_model': str(result.get('model', 'gemini-2.0-flash') if result else 'unknown')[:100],
            'processing_time_ms': processing_time_ms,
            'gazo_size_kb': gazo_size_kb,
            'gazo_format': gazo_format,
            
            # プラン情報（safe）
            'user_plan': 'free',
            'monthly_usage_count': 0,
            'is_over_limit': False,
            
            # 言語・地域情報（safe）
            'selected_language': str(body.get('language', 'ja'))[:10],
            'client_timezone': str(headers.get('x-timezone', 'Asia/Tokyo'))[:50],
            
            # エラー情報（safe）
            'error_occurred': error is not None,
            'error_message': str(error)[:500] if error else '',
            
            # システム情報（safe）
            'api_version': 'v1',
            'client_app_version': str(headers.get('x-app-version', '1.2'))[:20],
            'created_at_jst': jst_now.isoformat() + '+09:00',
            'ttl_timestamp': ttl_timestamp
        }
        
        # DynamoDB保存（safe）
        try:
            dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
            table_name = f"{os.environ.get('PROJECT_NAME', 'ai-tourism-poc')}-analyze-logs-{os.environ.get('STAGE', 'dev')}"
            table = dynamodb.Table(table_name)
            table.put_item(Item=log_entry)
            print(f"Analysis log saved: {log_id}")
        except Exception as db_error:
            print(f"DynamoDB save failed (ignored): {str(db_error)[:200]}")
        
    except Exception as save_error:
        print(f"Log save error (ignored): {str(save_error)[:200]}")


def generate_sequential_id():
    """
    軽量シーケンシャルID生成（20ms以内目標）
    """
    try:
        # 軽量DynamoDB接続
        dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
        table_name = f"{os.environ.get('PROJECT_NAME', 'ai-tourism-poc')}-sequence-counter-{os.environ.get('STAGE', 'dev')}"
        counter_table = dynamodb.Table(table_name)
        
        # 高速カウンター更新
        response = counter_table.update_item(
            Key={'counter_name': 'analyze_log'},
            UpdateExpression='ADD current_value :inc',
            ExpressionAttributeValues={':inc': 1},
            ReturnValues='UPDATED_NEW'
        )
        
        sequence = int(response['Attributes']['current_value'])
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:-3]  # ミリ秒まで
        
        return f"{sequence:03d}_{timestamp}"
        
    except Exception as e:
        print(f"Sequential ID generation error (using fallback): {str(e)[:100]}")
        # フォールバック: ランダムタイムスタンプベースID
        try:
            import random
            random_suffix = random.randint(100, 999)
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:-3]
            return f"FB{random_suffix}_{timestamp}"
        except:
            # 最終フォールバック
            import time
            return f"ERR_{int(time.time() * 1000)}"


def detect_image_format(image_data):
    """
    画像形式検出（完全保護付き）
    """
    try:
        if not image_data or len(str(image_data)) < 10:
            return 'unknown'
        
        # base64デコードしてヘッダー確認（安全に）
        import base64
        
        # data URL形式の場合は分割
        if str(image_data).startswith('data:image'):
            try:
                image_data = str(image_data).split(',')[1]
            except:
                return 'unknown'
        
        # base64デコード（先頭100文字のみ・安全に）
        try:
            decoded = base64.b64decode(str(image_data)[:200])  # 先頭200文字のみ
        except:
            return 'unknown'
        
        # ヘッダー確認
        if len(decoded) < 4:
            return 'unknown'
            
        if decoded[:3] == b'\xff\xd8\xff':
            return 'JPEG'
        elif decoded[:4] == b'\x89PNG':
            return 'PNG'
        elif decoded[:3] == b'GIF':
            return 'GIF'
        elif decoded[:4] in [b'RIFF', b'WEBP']:
            return 'WEBP'
        else:
            return 'unknown'
            
    except Exception as detect_error:
        print(f"Image format detection error (ignored): {str(detect_error)[:100]}")
        return 'unknown'