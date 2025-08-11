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
    札幌特化のモック解析結果
    """
    if language == 'ja':
        analysis_text = """🏔️ 札幌観光AI解析結果

**札幌内の場所**: この画像は札幌市内の典型的な風景を示しています。

**札幌の名所との関連**:
• すすきの繁華街 - 北海道最大の歓楽街
• 大通公園 - 札幌雪まつりのメイン会場
• 円山公園 - 桜の名所として有名
• サッポロビール園 - ジンギスカンで有名

**道民文化・グルメ**:
🍜 札幌ラーメン - 味噌ラーメン発祥の地
🥩 ジンギスカン - 北海道のソウルフード
🦀 海鮮丼 - 新鮮な北海道産海産物
🍰 六花亭・ルタオ - 札幌銘菓

**季節体験**:
❄️ 冬: さっぽろ雪まつり、スキー場
🌸 春: 円山公園の桜、暖かな気候
☀️ 夏: ビアガーデン、涼しい気候
🍂 秋: 紅葉、北海道グルメ

**アクセス情報**:
🚇 札幌市営地下鉄（南北線・東西線・東豊線）
🚶‍♂️ JR札幌駅から徒歩圏内の主要スポット

**地元おすすめ**:
• 狸小路商店街でショッピング
• 札幌場外市場で海鮮グルメ
• モエレ沼公園でアート体験
• 定山渓温泉でリラックス

札幌の魅力を存分にお楽しみください！"""
    else:
        analysis_text = """🏔️ Sapporo Tourism AI Analysis

**Location in Sapporo**: This image shows typical scenery from Sapporo city.

**Sapporo Attractions**:
• Susukino - Hokkaido's largest entertainment district
• Odori Park - Main venue for Sapporo Snow Festival
• Maruyama Park - Famous cherry blossom spot
• Sapporo Beer Garden - Famous for Genghis Khan

**Local Hokkaido Culture**:
🍜 Sapporo Ramen - Birthplace of miso ramen
🥩 Genghis Khan - Hokkaido soul food
🦀 Seafood bowls - Fresh Hokkaido seafood
🍰 Rokkatei & LeTAO - Sapporo confections

**Seasonal Experiences**:
❄️ Winter: Sapporo Snow Festival, skiing
🌸 Spring: Cherry blossoms at Maruyama Park
☀️ Summer: Beer gardens, cool climate
🍂 Autumn: Fall foliage, Hokkaido cuisine

**Getting Around**:
🚇 Sapporo Municipal Subway (Nanboku, Tozai, Toho lines)
🚶‍♂️ Walking distance from JR Sapporo Station

**Local Recommendations**:
• Shopping at Tanuki-koji Shopping Street
• Seafood at Sapporo Jogai Market
• Art experience at Moerenuma Park
• Relax at Jozankei Onsen

Enjoy the full charm of Sapporo!"""
    
    return {
        'analysis': analysis_text,
        'language': language,
        'timestamp': get_jst_isoformat(),
        'model': 'sapporo-tourism-ai-mock',
        'status': 'success'
    }