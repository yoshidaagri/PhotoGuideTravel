import json
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
    シンプルな画像解析関数（パッケージ依存なし）
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
        language = body.get('language', 'ja')
        
        if not image_data:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Image data is required'})
            }
        
        # モック解析結果（実際のGemini APIは後で実装）
        analysis_result = generate_mock_analysis(language)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(analysis_result)
        }
        
    except Exception as e:
        print(f"Error in image analysis: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
            },
            'body': json.dumps({'error': str(e)})
        }


def generate_mock_analysis(language='ja'):
    """
    観光地のモック解析結果
    """
    if language == 'ja':
        analysis_text = """🏔️ 観光AI解析結果

**場所の特定**: この画像は観光地の典型的な風景を示しています。

**主要な観光名所**:
• 繁華街・ショッピングエリア
• 中心部の公園・イベント会場
• 桜の名所・自然公園
• 地元名物料理の名店

**地元文化・グルメ**:
🍜 地元の名物ラーメン
🥩 地域の名物肉料理
🦀 新鮮な海鮮料理
🍰 地元の銘菓・スイーツ

**季節体験**:
❄️ 冬: 雪まつり、ウィンタースポーツ
🌸 春: 桜の名所、温暖な気候
☀️ 夏: ビアガーデン、避暑地
🍂 秋: 紅葉、秋の味覚

**アクセス情報**:
🚇 地下鉄・公共交通機関
🚶‍♂️ 主要駅から徒歩圏内

**地元おすすめ**:
• 商店街でショッピング
• 市場で新鮮な海鮮
• 公園でアート体験
• 温泉でリラックス

この地域の魅力を存分にお楽しみください！"""
    else:
        analysis_text = """🏔️ Tourism AI Analysis

**Location Analysis**: This image shows typical scenery from this tourist destination.

**Major Attractions**:
• Entertainment district
• Central park - Main event venue
• Nature park - Famous cherry blossom spot
• Local cuisine restaurants

**Local Culture**:
🍜 Regional ramen specialties
🥩 Local meat dishes
🦀 Fresh seafood bowls
🍰 Regional confections

**Seasonal Experiences**:
❄️ Winter: Snow festivals, skiing
🌸 Spring: Cherry blossoms in parks
☀️ Summer: Beer gardens, cool climate
🍂 Autumn: Fall foliage, local cuisine

**Getting Around**:
🚇 Local subway and public transport
🚶‍♂️ Walking distance from major stations

**Local Recommendations**:
• Shopping at local shopping streets
• Fresh seafood at local markets
• Art experiences in parks
• Relax at hot springs

Enjoy the full charm of this destination!"""
    
    return {
        'analysis': analysis_text,
        'language': language,
        'timestamp': get_jst_isoformat(),
        'model': 'tourism-ai-mock',
        'status': 'success'
    }