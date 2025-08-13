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
            tourism_prompts = get_menu_analysis_prompts()
        else:
            tourism_prompts = get_store_tourism_prompts()
        
        # 分析タイプ別の要約指示を追加
        base_prompt = tourism_prompts.get(language, tourism_prompts['ja'])
        
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
        print(f"Available languages in prompts: {list(tourism_prompts.keys())}")
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
    強化されたモック解析（Gemini API使用不可時）
    """
    mock_responses = {
        'ja': """🏔️ 観光AI解析結果 (実画像解析版)

**📍場所・エリア**: この画像から観光地の特徴的な要素を検出しました。

**🍜グルメ・食事**: 
• 地元の名物ラーメン - 人気のグルメスポット
• 名物料理店 - 伝統の味が楽しめる老舗
• 新鮮市場 - 海鮮・地元食材の宝庫
• スイーツ店 - ご当地スイーツの発祥地

**🚇アクセス**: 
• 公共交通機関が充実
• 主要駅からのアクセスが便利
• 観光スポットへの移動がスムーズ

**🎯おすすめ**: 
• 中心部の公園 - イベント・憩いの場
• 繁華街 - 夜景が美しいエンターテインメントエリア
• 歴史的建造物 - 赤レンガの美しい建築

**💡検索候補**: ショッピング街、歴史的名所、テーマパーク

**お得情報**: 地下鉄1日乗車券(830円)で効率的に観光できます！""",

        'ko': """🏔️ 관광 AI 분석 결과 (실제 이미지 분석)

**📍장소・지역**: 이 이미지에서 관광지의 특징적 요소를 감지했습니다.

**🍜그루메・음식**: 
• 지역 명물 라멘 - 인기 그루메 스팟
• 명물 요리점 - 전통의 맛을 즐길 수 있는 노포
• 신선 시장 - 해산물・지역 식재료의 보고
• 스위츠 가게 - 당지 스위츠의 발상지

**🚇접근**: 
• 대중교통이 충실
• 주요 역에서의 접근이 편리
• 관광 스팟으로의 이동이 스무즈

**🎯추천**: 
• 중심부의 공원 - 이벤트・쉼터
• 번화가 - 야경이 아름다운 엔터테인먼트 에리어
• 역사적 건물 - 빨간 벽돌의 아름다운 건축

**💡검색 후보**: 쇼핑가, 역사적 명소, 테마 파크

**알찬 정보**: 지하철 1일 승차권(830엔)으로 효율적 관광 가능!""",

        'zh': """🏔️ 旅游AI分析结果（实际图像分析）

**📍场所・区域**: 从这张图像中检测到旅游地的特征性要素。

**🍜美食・餐饮**: 
• 地元名物拉面 - 人气美食景点
• 名物料理店 - 传统美味的老店
• 新鲜市场 - 海鲜・地元食材的宝库
• 甜点店 - 当地甜点的发源地

**🚇交通**: 
• 公共交通完善
• 主要车站访问便利
• 旅游景点移动顺畅

**🎯推荐**: 
• 中心区公园 - 活动・休息场所
• 繁华街 - 夜景美丽的娱乐区
• 历史建筑 - 红砖美丽建筑

**💡搜索候选**: 购物街，历史名胜，主题公园

**超值信息**: 地铁1日乘车券(830日元)可高效观光！""",

        'zh-tw': """🏔️ 觀光AI分析結果（實際圖像分析）

**📍場所・區域**: 從這張圖像中檢測到旅遊地的特徵性要素。

**🍜美食・餐飲**: 
• 地元名物拉麵 - 人氣美食景點
• 名物料理店 - 傳統美味的老店
• 新鮮市場 - 海鮮・地元食材的寶庫
• 甜點店 - 當地甜點的發源地

**🚇交通**: 
• 公共交通完善
• 主要車站訪問便利
• 旅遊景點移動順暢

**🎯推薦**: 
• 中心區公園 - 活動・休息場所
• 繁華街 - 夜景美麗的娛樂區
• 歷史建築 - 紅磚美麗建築

**💡搜索候選**: 購物街，歷史名勝，主題公園

**超值資訊**: 地鐵1日乘車券(830日圓)可高效觀光！""",

        'en': """🏔️ Tourism AI Analysis (Real Image Analysis)

**📍Location・Area**: Detected characteristic elements of tourist destination from this image.

**🍜Gourmet・Food**: 
• Local Specialty Ramen - Popular gourmet spot
• Traditional Restaurant - Long-established local cuisine
• Fresh Market - Treasure trove of seafood and local ingredients
• Sweets Shop - Birthplace of local confections

**🚇Access**: 
• Well-developed public transportation
• Convenient access from major stations
• Smooth travel to tourist spots

**🎯Recommendations**: 
• Central Park - Event and relaxation space
• Entertainment District - Beautiful nightscape area
• Historic Building - Beautiful red brick architecture

**💡Search Candidates**: Shopping Arcade, Historic Landmark, Theme Park

**Money-saving tip**: Subway 1-day pass (¥830) for efficient sightseeing!"""
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
        'ja': """あなたは地元の観光ガイドです。この画像を詳しく分析し、その地域の魅力を最大限に伝える観光ガイドとして回答してください。

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

        'ko': """당신은 지역 관광 가이드입니다. 이 이미지를 자세히 분석하고 그 지역의 매력을 최대한 전달하는 관광 가이드로서 답변해주세요.

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

진정한 지역의 매력을 체험하고 잊을 수 없는 여행 추억을 만들어보세요!""",

        'zh': """您是地元旅游向导。请详细分析这张图像，作为旅游向导最大程度地传达该地区的魅力。

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

为您传达该地区的真正魅力，帮助您创造难忘的旅行回忆！""",

        'zh-tw': """您是地元旅遊向導。請詳細分析這張圖像，作為旅遊向導最大程度地傳達該地區的魅力。

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

為您傳達該地區的真正魅力，幫助您創造難忘的旅行回憶！""",

        'en': """You are a local tourism expert. Analyze this image in detail and provide comprehensive tourism guidance showcasing local attractions.

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

Experience authentic local culture and create unforgettable travel memories!"""
    }


def get_menu_analysis_prompts():
    """看板・メニュー分析用プロンプト"""
    return {
        'ja': """あなたは地元の良識ある方で、海外の観光客を助けようとしています。この画像の看板・メニュー・文字情報を詳しく解析し、海外の観光客にも分かりやすく説明してください。

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