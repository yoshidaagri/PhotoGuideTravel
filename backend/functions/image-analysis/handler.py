import json
import boto3
import base64
import os
from datetime import datetime
from decimal import Decimal
import google.generativeai as genai


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
        
        # リクエスト解析
        body = json.loads(event.get('body', '{}'))
        image_data = body.get('image')
        language = body.get('language', 'en')
        user_id = body.get('userId')
        
        if not image_data:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Image data is required'})
            }
        
        # Google Gemini API呼び出し
        analysis_result = analyze_image_with_gemini(image_data, language)
        
        # DynamoDB記録
        if user_id:
            save_analysis_log(user_id, analysis_result, image_data)
        
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