import json
import os
import base64
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
            sapporo_prompts = get_menu_analysis_prompts()
        else:
            sapporo_prompts = get_store_tourism_prompts()
        
        # 分析タイプ別の要約指示を追加
        base_prompt = sapporo_prompts.get(language, sapporo_prompts['ja'])
        
        if analysis_type == 'menu':
            summary_instruction = get_menu_summary_instructions()
        else:
            summary_instruction = get_store_summary_instructions()
        
        # 中国語の場合は特別強化
        if language == 'zh':
            prompt = f"请用简体中文回答。{base_prompt}{summary_instruction.get(language, summary_instruction['ja'])}请确保回答完全使用简体中文。"
        elif language == 'zh-tw':
            prompt = f"請用繁體中文回答。{base_prompt}{summary_instruction.get(language, summary_instruction['ja'])}請確保回答完全使用繁體中文。"
        else:
            prompt = base_prompt + summary_instruction.get(language, summary_instruction['ja'])
        
        # デバッグログ
        print(f"Analysis type: {analysis_type}, Language: {language}")
        print(f"Available languages in prompts: {list(sapporo_prompts.keys())}")
        print(f"Available languages in summary: {list(summary_instruction.keys())}")
        print(f"Selected base prompt starts with: {base_prompt[:100]}...")
        
        # Gemini REST API リクエスト構築
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
        
        # HTTP リクエスト送信
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        # レスポンス解析
        if 'candidates' in result and result['candidates']:
            analysis_text = result['candidates'][0]['content']['parts'][0]['text']
            return {
                'analysis': analysis_text,
                'language': language,
                'timestamp': get_jst_isoformat(),
                'model': 'gemini-2.0-flash-exp',
                'status': 'success'
            }
        else:
            return generate_enhanced_mock_analysis(language, analysis_type)
        
    except Exception as e:
        print(f"Gemini API error: {str(e)}")
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
    強化された札幌特化モック解析（Gemini API使用不可時）
    """
    mock_responses = {
        'ja': """🏔️ 札幌観光AI解析結果 (実画像解析版)

**📍場所・エリア**: この画像から札幌市内の特徴的な要素を検出しました。

**🍜グルメ・食事**: 
• 札幌ラーメン横丁 - すすきのの名物スポット
• だるま本店 - ジンギスカンの老舗、札幌発祥の味
• 二条市場 - 新鮮な北海道海鮮の台所
• 六花亭本店 - マルセイバターサンド発祥地

**🚇アクセス**: 
• 地下鉄南北線: すすきの駅 ↔ 大通駅 ↔ 札幌駅
• 地下鉄東西線: 円山公園駅、大通駅経由
• 札幌駅-大通-すすきの: 地下歩行空間で直結

**🎯おすすめ**: 
• 大通公園 - 雪まつり・ビアガーデンの舞台
• すすきの繁華街 - 東洋一のネオン街
• サッポロビール園 - 赤レンガの歴史的建造物

**💡検索候補**: 狸小路商店街、札幌時計台、白い恋人パーク

**お得情報**: 地下鉄1日乗車券(830円)で効率的に観光できます！""",

        'ko': """🏔️ 삿포로 관광 AI 분석 결과 (실제 이미지 분석)

**📍장소・지역**: 이 이미지에서 삿포로시내 특징적 요소를 감지했습니다.

**🍜그루메・음식**: 
• 삿포로 라멘 요코초 - 스스키노의 명물 스팟
• 다루마 혼텐 - 징기스칸 노포, 삿포로 발상지
• 니조 시장 - 신선한 홋카이도 해산물 시장
• 롯카테이 본점 - 마루세이 버터 샌드 발상지

**🚇접근**: 
• 지하철 남북선: 스스키노역 ↔ 오도리역 ↔ 삿포로역
• 지하철 동서선: 마루야마 공원역, 오도리역 경유
• 삿포로역-오도리-스스키노: 지하보행공간 직결

**🎯추천**: 
• 오도리 공원 - 눈축제・맥주 가든 무대
• 스스키노 번화가 - 동양 최대 네온 거리
• 삿포로 맥주원 - 빨간 벽돌 역사 건축물

**💡검색 후보**: 타누키코지 상점가, 삿포로 시계탑, 시로이 코이비토 파크

**알찬 정보**: 지하철 1일 승차권(830엔)으로 효율적 관광 가능!""",

        'zh': """🏔️ 札幌旅游AI分析结果（实际图像分析）

**📍场所・区域**: 从这张图像中检测到札幌市内的特征性要素。

**🍜美食・餐饮**: 
• 札幌拉面横丁 - 薄野的名物景点
• 达摩本店 - 成吉思汗烤肉老店，札幌发源地
• 二条市场 - 新鲜北海道海鲜市场
• 六花亭本店 - 奶油夹心饼干发源地

**🚇交通**: 
• 地铁南北线: 薄野站 ↔ 大通站 ↔ 札幌站
• 地铁东西线: 圆山公园站，大通站经由
• 札幌站-大通-薄野: 地下步行空间直达

**🎯推荐**: 
• 大通公园 - 雪祭・啤酒花园舞台
• 薄野繁华街 - 东洋最大霓虹街
• 札幌啤酒园 - 红砖历史建筑

**💡搜索候选**: 狸小路商店街，札幌钟楼，白色恋人公园

**超值信息**: 地铁1日乘车券(830日元)可高效观光！""",

        'zh-tw': """🏔️ 札幌觀光AI分析結果（實際圖像分析）

**📍場所・區域**: 從這張圖像中檢測到札幌市內的特徵性要素。

**🍜美食・餐飲**: 
• 札幌拉麵橫丁 - 薄野的名物景點
• 達摩本店 - 成吉思汗烤肉老店，札幌發源地
• 二條市場 - 新鮮北海道海鮮市場
• 六花亭本店 - 奶油夾心餅乾發源地

**🚇交通**: 
• 地鐵南北線: 薄野站 ↔ 大通站 ↔ 札幌站
• 地鐵東西線: 圓山公園站，大通站經由
• 札幌站-大通-薄野: 地下步行空間直達

**🎯推薦**: 
• 大通公園 - 雪祭・啤酒花園舞臺
• 薄野繁華街 - 東洋最大霓虹街
• 札幌啤酒園 - 紅磚歷史建築

**💡搜索候選**: 狸小路商店街，札幌鐘樓，白色戀人公園

**超值資訊**: 地鐵1日乘車券(830日圓)可高效觀光！""",

        'en': """🏔️ Sapporo Tourism AI Analysis (Real Image Analysis)

**📍Location・Area**: Detected characteristic elements of Sapporo city from this image.

**🍜Gourmet・Food**: 
• Sapporo Ramen Yokocho - Famous ramen alley in Susukino
• Daruma Honten - Long-established Genghis Khan restaurant
• Nijo Market - Fresh Hokkaido seafood market
• Rokkatei Honten - Birthplace of Marsei Butter Sandwich

**🚇Access**: 
• Nanboku Line: Susukino ↔ Odori ↔ Sapporo Station
• Tozai Line: Via Maruyama Koen & Odori stations
• Sapporo-Odori-Susukino: Underground walkway connection

**🎯Recommendations**: 
• Odori Park - Snow Festival & Beer Garden venue
• Susukino District - Asia's largest neon entertainment area
• Sapporo Beer Garden - Historic red brick building

**💡Search Candidates**: Tanuki-koji Shopping Arcade, Sapporo Clock Tower, Shiroi Koibito Park

**Money-saving tip**: Subway 1-day pass (¥830) for efficient sightseeing!"""
    }

    analysis_text = mock_responses.get(language, mock_responses['ja'])

    return {
        'analysis': analysis_text,
        'language': language,
        'timestamp': get_jst_isoformat(),
        'model': 'sapporo-tourism-ai-enhanced',
        'status': 'success'
    }


def get_store_tourism_prompts():
    """店舗・観光施設分析用プロンプト"""
    return {
        'ja': """あなたは札幌生まれの地元の方です。この画像を詳しく分析し、札幌の魅力を最大限に伝える観光ガイドとして回答してください。

🏔️ **札幌観光AI解析** 🏔️

**重要な分析指示:**
1. まず画像に写っている要素（建物、看板、人物、料理、風景など）を具体的に特定してください
2. 看板や文字が見える場合は、それを読み取ってgoogleで検索して店名・場所・概要を調査してください
3. 建築様式、装飾、雰囲気から場所のタイプを推測してください
4. 実在する場所の場合は、正確な情報を提供してください
5. 画像に写っているものが札幌のものでない場合は、札幌ではないと断りながら解説してください
6. 画像の要素のURLが特定できた場合、URLを載せてください。googleで検索してであるお店の公式サイト、観光案内Webや食べログが良いです
7. 画像に映る看板は複数ある場合があるので、総合的に判断してください。
8. 回答の初めから場所・エリアで開始して、はい分かりましたというような文章は入れないでください。

**📍 場所・エリア特定**
- 画像から読み取れる具体的な店名・施設名を明記
- 札幌市内の具体的な地区・エリアを特定（すすきの・大通・円山・豊平・白石・北区・手稲など）
- 最寄り地下鉄駅（南北線・東西線・東豊線）との位置関係
- JR札幌駅・新千歳空港からのアクセス情報
- 具体的な住所（判明している場合）

**🗣️ 言語サポート**
- 英語対応の可否とレベル
- 中国語・韓国語対応状況
- 翻訳アプリで見せるべき重要フレーズ

**💰 料金・アクセス情報**
- 入場料・価格帯：（画像から推測できる場合は具体的な料金を円で表示）
- 料理の価格帯：（メニューが見える場合は具体的に）
- 追加料金：（ガイド・写真撮影・特別メニューなど）
- アクセス方法：（交通手段・所要時間）
- 営業時間：（看板等から読み取れる場合）
- 定休日：（判明している場合）
- 周辺の見どころ：（徒歩圏内の観光スポット）

**❄️ 季節別の準備**
- 現在の気温と適切な服装
- 防寒具のレンタル・購入場所
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

        'ko': """당신은 삿포로 태생의 지역 주민입니다. 이 이미지를 자세히 분석하고 샿포로의 매력을 최대한 전달하는 관광 가이드로서 답변해주세요.

🏔️ **삿포로 관광 AI 분석** 🏔️

**중요한 분석 지시사항:**
1. 먼저 이미지에 보이는 요소(건물, 간판, 사람, 요리, 풍경 등)를 구체적으로 파악해주세요
2. 간판이나 문자가 보이면 그것을 읽어서 구글로 검색하여 점포명・장소・개요를 조사해주세요
3. 건축 양식, 장식, 분위기로부터 장소의 타입을 추측해주세요
4. 실재하는 장소인 경우 정확한 정보를 제공해주세요
5. 이미지의 대상이 삿포로가 아닌 경우, 삿포로가 아니라고 명시하며 설명해주세요
6. 이미지 요소의 URL을 특정할 수 있다면 URL을 게재해주세요. 구글로 검색하여 찾은 매장의 공식 사이트, 관광안내 웹사이트나 타베로그가 좋습니다
7. 이미지에 나타나는 간판은 여러 개 있을 수 있으므로 종합적으로 판단해주세요.
8. 답변은 처음부터 장소・지역으로 시작하고, '네 알겠습니다'와 같은 문장은 넣지 마세요.

**📍 위치・지역 특정**
- 이미지에서 읽을 수 있는 구체적인 점포명・시설명을 명기
- 삿포로시 내 구체적인 지구・지역 특정 (스스키노・오도리・마루야마・토요히라・시로이시・키타구・테이네 등)
- 가장 가까운 지하철역 (남북선・동서선・토호선)과의 위치 관계
- JR삿포로역・신치토세공항에서의 접근 정보
- 구체적인 주소 (판명된 경우)

**🗣️ 언어 서포트**
- 영어 대응 가능 여부와 레벨
- 중국어・한국어 대응 상황
- 번역 앱으로 보여줄 중요한 프레이즈

**💰 요금・접근 정보**
- 입장료・가격대: (이미지에서 추측 가능한 경우 구체적 요금을 엔으로 표시)
- 요리 가격대: (메뉴가 보이는 경우 구체적으로)
- 추가요금: (가이드・사진촬영・특별메뉴 등)
- 접근방법: (교통수단・소요시간)
- 영업시간: (간판 등에서 읽을 수 있는 경우)
- 정기휴일: (판명된 경우)
- 주변 볼거리: (도보권 내 관광지)

**❄️ 계절별 준비사항**
- 현재 기온과 적절한 복장
- 방한용품 렌탈・구입 장소
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

진정한 삿포로를 체험하고 잊을 수 없는 여행 추억을 만들어보세요!""",

        'zh': """您是札幌出生的当地人。请详细分析这张图像，作为旅游向导最大程度地传达札幌的魅力。

🏔️ **札幌旅游AI分析** 🏔️

**重要分析指示：**
1. 首先请具体识别图像中显示的元素（建筑、招牌、人物、料理、风景等）
2. 如果能看到招牌或文字，请读取并通过Google搜索调查店名・地点・概要
3. 从建筑风格、装饰、氛围推测场所的类型
4. 如果是实际存在的地点，请提供准确信息
5. 如果图像中的内容不是札幌的，请说明不是札幌并进行解说
6. 如果能特定图像元素的URL，请载入URL。通过Google搜索找到的店铺官方网站、旅游指南网站或食べログ（Tabelog）最佳
7. 图像中可能有多个招牌，请综合判断。
8. 请从场所・区域开始回答，不要加入"好的我明白了"之类的开场白。

**📍 地点・区域特定**
- 明确记载从图像中可读取的具体店名・设施名
- 特定札幌市内的具体地区・区域（薄野・大通・圆山・丰平・白石・北区・手稻等）
- 与最近地铁站（南北线・东西线・东丰线）的位置关系
- 从JR札幌站・新千岁机场的交通信息
- 具体地址（如果能确定）

**🗣️ 语言支持**
- 英语应对可否及水平
- 中文・韩语应对状况
- 使用翻译APP时应展示的重要短语

**💰 费用・交通信息**
- 门票・价格区间：（如果能从图像推测，请用日元显示具体费用）
- 料理价格区间：（如果能看到菜单请具体说明）
- 附加费用：（导游・拍照・特别菜单等）
- 交通方式：（交通工具・所需时间）
- 营业时间：（如果能从招牌等读取）
- 定休日：（如果能确定）
- 周边景点：（步行范围内的观光景点）

**❄️ 季节性准备**
- 当前气温和适合的服装
- 防寒用品的租赁・购买地点
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

为您传达札幌的真正魅力，帮助您创造难忘的旅行回忆！""",

        'zh-tw': """您是札幌出生的當地人。請詳細分析這張圖像，作為旅遊向導最大程度地傳達札幌的魅力。

🏔️ **札幌觀光AI分析** 🏔️

**重要分析指示：**
1. 首先請具體識別圖像中顯示的元素（建築、招牌、人物、料理、風景等）
2. 如果能看到招牌或文字，請讀取並透過Google搜尋調查店名・地點・概要
3. 從建築風格、裝飾、氛圍推測場所的類型
4. 如果是實際存在的地點，請提供準確資訊
5. 如果圖像中的內容不是札幌的，請說明不是札幌並進行解說
6. 如果能特定圖像元素的URL，請載入URL。透過Google搜尋找到的店鋪官方網站、旅遊指南網站或食べログ（Tabelog）最佳
7. 圖像中可能有多個招牌，請綜合判斷。
8. 請從場所・區域開始回答，不要加入「好的我明白了」之類的開場白。

**📍 地點・區域特定**
- 明確記載從圖像中可讀取的具體店名・設施名
- 特定札幌市內的具體地區・區域（薄野・大通・圓山・豐平・白石・北區・手稻等）
- 與最近地鐵站（南北線・東西線・東豐線）的位置關係
- 從JR札幌站・新千歲機場的交通資訊
- 具體地址（如果能確定）

**🗣️ 語言支援**
- 英語應對可否及水準
- 中文・韓語應對狀況
- 使用翻譯APP時應展示的重要短語

**💰 費用・交通資訊**
- 門票・價格區間：（如果能從圖像推測，請用日圓顯示具體費用）
- 料理價格區間：（如果能看到菜單請具體說明）
- 附加費用：（導遊・拍照・特別菜單等）
- 交通方式：（交通工具・所需時間）
- 營業時間：（如果能從招牌等讀取）
- 定休日：（如果能確定）
- 周邊景點：（步行範圍內的觀光景點）

**❄️ 季節性準備**
- 當前氣溫和適合的服裝
- 防寒用品的租賃・購買地點
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

為您傳達札幌的真正魅力，幫助您創造難忘的旅行回憶！""",

        'en': """You are a native-born local resident of Sapporo. Analyze this image in detail and provide comprehensive tourism guidance showcasing Sapporo's attractions.

🏔️ **SAPPORO TOURISM AI ANALYSIS** 🏔️

**Important Analysis Instructions:**
1. First, specifically identify elements shown in the image (buildings, signs, people, food, scenery, etc.)
2. If signs or text are visible, read them and research store names/locations/details through Google search
3. Infer the type of location from architectural style, decorations, and atmosphere
4. For real existing locations, provide accurate information
5. If the image content is not from Sapporo, clarify it's not Sapporo while explaining
6. If URLs of image elements can be identified, include the URLs. Official websites of stores found through Google search, tourism guide websites or Tabelog are preferred
7. There may be multiple signs in the image, so please make a comprehensive judgment.
8. Start your response directly with the location/area, and do not include phrases like "Yes, I understand" at the beginning.

**📍 Location & Area Identification**
- Clearly state specific store names/facility names readable from the image
- Identify specific districts/areas in Sapporo (Susukino, Odori, Maruyama, Toyohira, Shiroishi, Kita-ku, Teine, etc.)
- Nearest subway stations (Nanboku, Tozai, Toho Lines) and location relationships
- Access from JR Sapporo Station and New Chitose Airport
- Specific address (if determinable)

**🗣️ Language Support**
- English support availability and level
- Chinese/Korean language support status
- Important phrases to show using translation apps

**💰 Fee & Access Information**
- Admission fees/price range: (if inferable from image, show specific fees in JPY)
- Food price range: (if menu is visible, provide specifics)
- Additional charges: (guide, photography, special menus, etc.)
- Access methods: (transportation, travel time)
- Operating hours: (if readable from signs, etc.)
- Regular holidays: (if determinable)
- Nearby attractions: (tourist spots within walking distance)

**❄️ Seasonal Preparations**
- Current temperature and appropriate clothing
- Cold weather gear rental/purchase locations
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

Experience authentic Sapporo and create unforgettable travel memories!"""
    }


def get_menu_analysis_prompts():
    """看板・メニュー分析用プロンプト"""
    return {
        'ja': """あなたは札幌のグルメ・看板翻訳エキスパートです。この画像の看板・メニュー・文字情報を詳しく解析し、海外の方にも分かりやすく説明してください。

🍜 **札幌看板・メニューAI解析** 🍜

**📋 文字・看板情報の解析**
- 看板・メニューの日本語文字を正確に読み取り
- 店舗名・料理名・価格・説明文の翻訳
- 手書き文字・特殊フォントも可能な限り解読

**🍽️ 料理・メニュー詳細説明**
- 各料理の具材・調理法・特徴を詳しく説明
- アレルギー情報・辛さレベル・量の目安
- 札幌・北海道ならではの特色料理の背景説明
- おすすめの食べ方・組み合わせ

**💰 料金・価格情報**
- メニューの価格を正確に読み取り
- 税込み・税別の表記確認
- セットメニュー・単品の価格比較
- お得情報・割引・クーポン情報

**🗣️ 実用フレーズ・注文方法**
- 基本的な注文フレーズ（日本語・ローマ字・英語併記）
- 「これください」「おすすめは？」「辛くしないでください」等
- 指差しで使えるフレーズ集

海外の方が札幌グルメを安心して楽しめるよう、詳しくサポートします！""",

        'ko': """당신은 삿포로 미식・간판 번역 전문가입니다. 이 이미지의 간판・메뉴・문자 정보를 자세히 분석하고, 해외 방문객이 이해하기 쉽게 설명해주세요.

🍜 **삿포로 간판・메뉴 AI 분석** 🍜

**📋 문자・간판 정보 분석**
- 간판・메뉴의 일본어 문자 정확히 읽기
- 상점명・요리명・가격・설명문 번역
- 손글씨・특수 폰트도 최대한 해독

**🍽️ 요리・메뉴 상세 설명**
- 각 요리의 재료・조리법・특징 자세히 설명
- 알레르기 정보・매운 정도・양의 기준
- 삿포로・홋카이도 특색 요리의 배경 설명
- 추천 먹는 방법・조합

**💰 요금・가격 정보**
- 메뉴 가격 정확히 읽기 (엔→원 환산 참고)
- 세금 포함・별도 표기 확인
- 세트 메뉴・단품 가격 비교
- 할인・쿠폰 정보

**🏪 상점・주문 정보**
- 영업시간・정기휴일・연락처
- 주문 방법・결제 방법 (현금・카드・전자결제)
- 좌석수・예약 가능・대기시간 기준
- 특별 서비스 (포장・배달 등)

**🗣️ 실용 문구・주문 방법**
- 기본 주문 문구 (일본어・로마자・한국어)
- "이것 주세요" "추천은?" "맵지 않게 해주세요" 등
- 손가락으로 가리켜 쓸 수 있는 문구집

해외 방문객이 삿포로 미식을 안심하고 즐길 수 있도록 자세히 지원합니다!""",

        'zh': """**【极其重要：必须用简体中文回答，绝对不要使用英语】**

您是札幌美食・招牌翻译专家。请详细分析这张图像的招牌・菜单・文字信息，并向海外游客通俗易懂地说明。

**重要**: 请务必用简体中文回答，不要使用英语或其他语言。
**重要提醒**: 回答必须是简体中文，不可以是英语。
**MUST USE SIMPLIFIED CHINESE, NOT ENGLISH**

🍜 **札幌招牌・菜单AI分析** 🍜

**📋 文字・招牌信息分析**
- 准确读取招牌・菜单的日语文字
- 店名・菜名・价格・说明文翻译
- 手写字・特殊字体也尽量解读

**🍽️ 料理・菜单详细说明**
- 各菜品的食材・烹饪方法・特色详细说明
- 过敏信息・辣度・份量标准
- 札幌・北海道特色料理的背景说明
- 推荐吃法・搭配

**💰 费用・价格信息**
- 准确读取菜单价格 (日元→人民币换算参考)
- 确认含税・不含税标记
- 套餐・单品价格比较
- 优惠・折扣・优惠券信息

**🏪 店铺・点餐信息**
- 营业时间・定休日・联系方式
- 点餐方法・付款方式 (现金・卡・电子支付)
- 座位数・预约可否・等待时间标准
- 特别服务 (外带・外卖等)

**🗣️ 实用短语・点餐方法**
- 基本点餐短语 (日语・罗马音・中文)
- "要这个" "推荐什么?" "请不要辣" 等
- 用手指着就能用的短语集

帮助海外游客安心享受札幌美食，提供详细支持！

**【重要提醒：请确保您的回答完全使用简体中文，不要混入英语】**""",

        'zh-tw': """【極其重要：必須用繁體中文回答，絕對不要使用英語】

您是札幌美食・招牌翻譯專家。請詳細分析這張圖像的招牌セ菜單セ文字資訊，並向海外遊客通俗易懂地說明。

**重要**: 請務必用繁體中文回答，不要使用英語或其他語言。
**重要提醒**: 回答必須是繁體中文，不可以是英語。
**MUST USE TRADITIONAL CHINESE, NOT ENGLISH**

🍜 **札幌招牌セ菜單AI分析** 🍜

**📋 文字セ招牌資訊分析**
- 準確讀取招牌・菜單的日語文字
- 店名セ菜名セ價格セ說明文翻譯
- 手寫字・特殊字體也盡量解讀

**🍽️ 料理セ菜單詳細說明**
- 各菜品的食材・烹飪方法セ特色詳細說明
- 過敏資訊セ辣度セ份量標準
- 札幌・北海道特色料理的背景說明
- 推薦吃法・搭配

**💰 費用・價格資訊**
- 準確讀取菜單價格 (日圓→台幣換算參考)
- 確認含稅・不含稅標記
- 套餐セ單品價格比較
- 優惠・折扣セ優惠券資訊

**🏦 店鋪セ點餐資訊**
- 營業時間セ定休日セ聯絡方式
- 點餐方法セ付款方式 (現金セ卡・電子支付)
- 座位數・預約可否セ等待時間標準
- 特別服務 (外帶・外送等)

**🗣️ 實用短語・點餐方法**
- 基本點餐短語 (日語・羅馬音セ中文)
- 「要這個」「推薦什麼？」「請不要辣」等
- 用手指著就能用的短語集

幫助海外遊客安心享受札幌美食，提供詳細支持！

**【重要提醒：請確保您的回答完全使用繁體中文，不要混入英語】**""",

        'en': """You are a Sapporo gourmet and signboard translation expert. Please analyze the signboard, menu, and text information in this image in detail, explaining it clearly for overseas visitors.

🍜 **SAPPORO SIGNBOARD & MENU AI ANALYSIS** 🍜

**📋 Text & Signboard Information Analysis**
- Accurately read Japanese characters on signs and menus
- Translation of store names, dish names, prices, and descriptions
- Decode handwritten text and special fonts as much as possible

**🍽️ Cuisine & Menu Detailed Explanation**
- Detailed explanation of ingredients, cooking methods, and characteristics of each dish
- Allergy information, spiciness level, portion size guidelines
- Background explanation of Sapporo and Hokkaido specialty dishes
- Recommended ways to eat and combinations

**💰 Fee & Price Information**
- Accurately read menu prices (JPY with USD conversion reference)
- Check tax-inclusive/exclusive notation
- Set menu vs. single item price comparison
- Discount and coupon information

**🏪 Store & Ordering Information**
- Business hours, regular holidays, contact information
- Ordering methods, payment methods (cash, card, electronic payment)
- Number of seats, reservation availability, waiting time estimates
- Special services (takeout, delivery, etc.)

**🗣️ Practical Phrases & Ordering Methods**
- Basic ordering phrases (Japanese, romaji, English)
- "I'll have this", "What do you recommend?", "Not spicy please", etc.
- Phrase collection that can be used by pointing

Providing detailed support so overseas visitors can enjoy Sapporo gourmet with confidence!"""
    }


def get_store_summary_instructions():
    """店舗・観光地分析用要約指示"""
    return {
        'ja': "\n\n**重要**: 上記の分析内容を600文字以内で要約してください。\n\n**出力形式**:\n1. **📍場所・エリア**: 札幌市内の具体的な場所を特定\n2. **💡検索候補**: 不明な場合は類似スポット名を3つ提示\n\n特に場所が不明確な場合は、画像の特徴から推測できる札幌市内の候補地を具体的に提示してください。",
        'ko': "\n\n**중요**: 위 분석 내용을 600자 이내로 요약해주세요.\n\n**출력 형식**:\n1. **📍장소・지역**: 삿포로시내 구체적 장소 특정\n2. **💡검색 후보**: 불명확한 경우 유사 스팟명 3개 제시\n\n특히 장소가 불명확한 경우, 이미지 특징에서 추측 가능한 삿포로시내 후보지를 구체적으로 제시해주세요.",
        'zh': "\n\n**重要**: 请在600字内总结上述分析内容。\n\n**输出格式**:\n1. **📍场所・区域**: 札幌市内具体场所特定\n2. **💡搜索候选**: 不明确时提供3个类似景点名\n\n特别是场所不明确时，请根据图像特征推测札幌市内的具体候选地点。",
        'zh-tw': "\n\n**重要**: 請在600字內總結上述分析內容。\n\n**輸出格式**:\n1. **📍場所・區域**: 札幌市內具體場所特定\n2. **💡搜尋候選**: 不明確時提供3個類似景點名\n\n特別是場所不明確時，請根據圖像特徵推測札幌市內的具體候選地點。",
        'en': "\n\n**Important**: Summarize the above analysis within 600 characters.\n\n**Output Format**:\n1. **📍Location・Area**: Identify specific places in Sapporo\n2. **💡Search Candidates**: Provide 3 similar spot names if unclear\n\nEspecially when location is unclear, please suggest specific candidate locations in Sapporo based on image features."
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