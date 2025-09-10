# Phase 7.6: 観光地診断高速化 - Gemini API最適化と画像前処理

**計画日**: 2025年9月2日  
**目的**: 観光地診断の処理時間を50%短縮（3.6-8.1秒 → 2.0-4.0秒）  
**背景**: 観光地での通信環境を考慮し、診断速度の向上が収益化の鍵となる

## 🎯 Phase 7.6の目標

### 現状分析
```yaml
現在の処理時間内訳:
  - 画像アップロード（S3）: 1-2秒
  - Lambda起動: 0.5-1秒（コールドスタート）
  - Gemini API呼び出し: 2-5秒 ← 最大のボトルネック
  - DynamoDB保存: 0.1秒
  合計: 3.6-8.1秒
```

### 改善目標
- **総処理時間**: 2.0-4.0秒（50%短縮）
- **ユーザー体験**: 4秒以内完了率 80%以上
- **コスト**: 現状維持または削減

## 🚀 実装計画

### 1️⃣ Gemini API呼び出し最適化


#### A. アウトプット制限によるパフォーマンス最適化（レスポンス時間 -40%）

**現状分析**:
```python
# 現在のプロンプト（handler_gemini.py）
current_prompt = """あなたは地元の観光ガイドです。この画像を詳しく分析し、その地域の魅力を最大限に伝える観光ガイドとして800文字以内で回答してください。
**重要: 回答は必ずMarkdown形式で出力してください。見出しは##、太字は**、リストは-を使用してください。**
🏔️ **観光AI解析** 🏔️
[... 詳細な分析指示 ...]"""

# 現在の設定
current_config = {
    "maxOutputTokens": 2048,  # ← ボトルネック
    "temperature": 0.7,
    "topP": 0.8,
    "topK": 40
}
```

**❌ 問題点**:
- プロンプトで「800文字以内」と指示しているが、実際は2048トークン（約1500-2000文字）まで生成可能
- 出力トークン数が多いほどGemini APIレスポンス時間が長くなる
- プロンプト簡略化は解析精度劣化のリスクが高い

**✅ 改善案**:
```python
def build_output_optimized_config(analysis_type, language):
    """出力制限による高速化設定"""
    
    if analysis_type == 'menu':
        # メニュー翻訳: 構造化データ重視
        return {
            "maxOutputTokens": 1024,  # 半減
            "temperature": 0.3,      # 精度重視
            "topP": 0.9,
            "topK": 40,
            "stopSequences": ["---", "参考:", "URL:"]  # 不要情報停止
        }
    else:
        # 観光地解析: 簡潔な情報提供
        return {
            "maxOutputTokens": 1024,  # 半分に削減
            "temperature": 0.7,
            "topP": 0.8, 
            "topK": 40,
            "stopSequences": ["URL:", "参考文献", "詳細は公式"]
        }

```

**期待効果**:
```yaml
パフォーマンス改善:
  - メニュー翻訳: 3-5秒 → 1.5-2.5秒 (50%短縮)
  - 観光地解析: 4-8秒 → 2-4秒 (50%短縮)
  - Token使用量: 70%削減
  - API課金: 70%削減

品質保持:
  - プロンプトの分析指示は100%保持
  - 出力の簡潔性向上（ユーザー体験改善）
  - 必要な情報は確実に含む
```

#### B. 高速化重視のモデル・タイムアウト設定

```python
def select_performance_optimized_model(analysis_type):
    """パフォーマンス最適化されたモデル選択（精度は維持）"""
    
    # 現在の実装: gemini-2.0-flash-exp を統一使用
    base_model = 'gemini-2.0-flash-exp'
    
    if analysis_type == 'menu':
        # メニュー翻訳: 最高速化設定
        return {
            'model': base_model,
            'timeout': 15,  # 短縮（現在30秒）
            'maxOutputTokens': 256,  # 大幅削減
            'temperature': 0.3,  # 安定性重視
            'stopSequences': ["---", "参考:", "URL:", "※"]
        }
    else:
        # 観光地解析: 高速・高精度バランス
        return {
            'model': base_model,
            'timeout': 25,  # 短縮（現在30秒）
            'maxOutputTokens': 512,  # 半分に削減
            'temperature': 0.7,  # 創造性維持
            'stopSequences': ["URL:", "参考文献", "詳細は公式", "※"]
        }

def implement_timeout_optimization():
    """段階的タイムアウト実装"""
    
    # 段階的レスポンス
    timeouts = {
        'quick_response': 10,    # 基本情報のみ
        'standard_response': 20, # 通常の詳細情報
        'detailed_response': 30  # 最大情報（フォールバック）
    }
    
    return {
        'strategy': 'progressive_timeout',
        'fallback_enabled': True,
        'user_notification': True  # 処理状況をユーザーに通知
    }
```

**改善効果**:
```yaml
モデル統一の利点:
  - Gemini 2.0 Flash: 最新・高性能を維持
  - 複雑な分岐ロジック不要
  - 予測可能なレスポンス時間

タイムアウト短縮:
  - メニュー翻訳: 30秒 → 15秒
  - 観光地解析: 30秒 → 25秒
  - エラー率低下（早期タイムアウト検出）

出力トークン削減:
  - API応答時間: 50%短縮
  - 課金コスト: 70%削減
  - ユーザビリティ向上（簡潔な回答）
```

### 2️⃣ 画像前処理最適化

#### A. クライアント側圧縮（アップロード時間 -70%）

```javascript
// frontend/js/image_optimizer.js

// browser-image-compression を CDN から読み込み
// <script src="https://cdn.jsdelivr.net/npm/browser-image-compression@2.0.2/dist/browser-image-compression.min.js"></script>

async function optimizeImageForUpload(file) {
    const options = {
        maxSizeMB: 0.5,              // 500KB以下に圧縮
        maxWidthOrHeight: 1024,       // 最大1024px
        useWebWorker: true,           // Web Workerで非同期処理
        fileType: 'image/jpeg',       // JPEG形式に統一
        quality: 0.8,                 // 品質80%
        alwaysKeepResolution: false   // 必要に応じてリサイズ
    };
    
    try {
        console.log(`圧縮前: ${(file.size / 1024 / 1024).toFixed(2)}MB`);
        const compressedFile = await imageCompression(file, options);
        console.log(`圧縮後: ${(compressedFile.size / 1024 / 1024).toFixed(2)}MB`);
        
        // 圧縮率を表示
        const compressionRate = ((1 - compressedFile.size / file.size) * 100).toFixed(1);
        showCompressionInfo(`画像を${compressionRate}%圧縮しました`);
        
        return compressedFile;
    } catch (error) {
        console.error('画像圧縮エラー:', error);
        return file; // 圧縮失敗時は元のファイルを返す
    }
}

// 画像アップロード関数の修正
async function uploadImage() {
    const fileInput = document.getElementById('imageInput');
    const file = fileInput.files[0];
    
    if (!file) return;
    
    // 圧縮処理
    showLoadingMessage('画像を最適化中...');
    const optimizedFile = await optimizeImageForUpload(file);
    
    // Base64変換
    const reader = new FileReader();
    reader.onload = async function(e) {
        const base64Image = e.target.result;
        
        // アップロード処理
        await sendToAPI(base64Image);
    };
    reader.readAsDataURL(optimizedFile);
}
```

#### B. Lambda Layer での Sharp 導入

```yaml
# serverless.yml に追加
layers:
  sharp:
    path: layers/sharp
    name: ${self:service}-sharp-layer-${self:provider.stage}
    description: Sharp image processing library
    compatibleRuntimes:
      - python3.11
    retain: false

functions:
  imageAnalysis:
    handler: functions/image-analysis/handler_gemini_optimized.main
    layers:
      - {Ref: SharpLambdaLayer}
```

```python
# Lambda Layer 作成スクリプト
# scripts/create_sharp_layer.sh
#!/bin/bash

mkdir -p layers/sharp/python/lib/python3.11/site-packages
cd layers/sharp

# Sharp-python のインストール
pip install pillow-simd -t python/lib/python3.11/site-packages/

# Layer ZIP作成
zip -r sharp-layer.zip python/

echo "Sharp Layer created successfully"
```

```python
# backend/functions/image-analysis/image_processor.py
from PIL import Image
import io
import base64

def optimize_image_server_side(image_base64):
    """サーバー側での追加画像最適化"""
    
    # Base64デコード
    if image_base64.startswith('data:image'):
        image_base64 = image_base64.split(',')[1]
    
    image_data = base64.b64decode(image_base64)
    
    # Pillowで画像を開く
    img = Image.open(io.BytesIO(image_data))
    
    # EXIF情報に基づいて自動回転
    img = auto_rotate_image(img)
    
    # 最適なサイズにリサイズ
    if img.width > 1024 or img.height > 1024:
        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    
    # RGB変換（RGBA画像の場合）
    if img.mode in ('RGBA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    
    # JPEG形式で保存
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=85, optimize=True)
    
    # Base64エンコード
    optimized_base64 = base64.b64encode(output.getvalue()).decode()
    
    return optimized_base64, output.tell()
```

#### C. 画像形式の最適化

```python
def get_optimal_image_format(user_agent, accept_header):
    """ブラウザサポートに基づく最適形式選択"""
    
    # Accept ヘッダーをチェック
    if 'image/avif' in accept_header:
        return 'avif'  # 最高圧縮率
    elif 'image/webp' in accept_header:
        return 'webp'  # 高圧縮率
    else:
        return 'jpeg'  # 互換性重視
```

### 3️⃣ インテリジェントキャッシュ戦略

#### A. 画像ハッシュによるキャッシュ

```python
# backend/functions/image-analysis/cache_manager.py
import hashlib
from datetime import datetime, timedelta
import imagehash
from PIL import Image

class AnalysisCacheManager:
    def __init__(self, dynamodb_resource):
        self.dynamodb = dynamodb_resource
        self.cache_table = self.dynamodb.Table('ai-tourism-analysis-cache')
    
    def get_image_hash(self, image_base64):
        """画像の知覚的ハッシュを生成（類似画像も検出）"""
        
        # Base64をPIL Imageに変換
        image_data = base64.b64decode(image_base64.split(',')[1] 
                                     if ',' in image_base64 else image_base64)
        img = Image.open(io.BytesIO(image_data))
        
        # 知覚的ハッシュ（pHash）を使用
        phash = str(imagehash.phash(img))
        
        # 通常のハッシュも併用（完全一致用）
        sha_hash = hashlib.sha256(image_data).hexdigest()[:16]
        
        return {
            'phash': phash,
            'sha_hash': sha_hash
        }
    
    def check_cache(self, image_hash, language, analysis_type):
        """キャッシュ確認（0.1秒で返却）"""
        
        try:
            # 完全一致を優先
            response = self.cache_table.get_item(
                Key={
                    'hash_id': f"{image_hash['sha_hash']}_{language}_{analysis_type}"
                }
            )
            
            if 'Item' in response:
                item = response['Item']
                # 有効期限チェック
                if datetime.fromisoformat(item['expiry']) > datetime.now():
                    return {
                        'hit': True,
                        'result': item['analysis_result'],
                        'cache_type': 'exact'
                    }
            
            # 類似画像検索（pHash）
            similar_results = self.find_similar_cached(
                image_hash['phash'], 
                language, 
                analysis_type
            )
            
            if similar_results:
                return {
                    'hit': True,
                    'result': similar_results[0]['analysis_result'],
                    'cache_type': 'similar'
                }
            
            return {'hit': False}
            
        except Exception as e:
            print(f"Cache check error: {e}")
            return {'hit': False}
    
    def save_to_cache(self, image_hash, language, analysis_type, result, ttl_hours=24):
        """解析結果をキャッシュに保存"""
        
        try:
            self.cache_table.put_item(
                Item={
                    'hash_id': f"{image_hash['sha_hash']}_{language}_{analysis_type}",
                    'phash': image_hash['phash'],
                    'language': language,
                    'analysis_type': analysis_type,
                    'analysis_result': result,
                    'created_at': datetime.now().isoformat(),
                    'expiry': (datetime.now() + timedelta(hours=ttl_hours)).isoformat(),
                    'hit_count': 0
                }
            )
        except Exception as e:
            print(f"Cache save error: {e}")
```

#### B. 人気観光地の事前解析

```python
# backend/functions/scheduled/popular_spots_preanalyzer.py
import json
from datetime import datetime

# 人気観光地リスト（地域別）
POPULAR_SPOTS = {
    'hokkaido': [
        {'name': '札幌時計台', 'image': 's3://sample-images/sapporo-clock.jpg'},
        {'name': '函館山夜景', 'image': 's3://sample-images/hakodate-night.jpg'},
        {'name': '小樽運河', 'image': 's3://sample-images/otaru-canal.jpg'},
        {'name': '富良野ラベンダー畑', 'image': 's3://sample-images/furano-lavender.jpg'},
        {'name': '旭山動物園', 'image': 's3://sample-images/asahiyama-zoo.jpg'}
    ],
    'tokyo': [
        {'name': '東京タワー', 'image': 's3://sample-images/tokyo-tower.jpg'},
        {'name': '浅草寺', 'image': 's3://sample-images/sensoji.jpg'},
        {'name': 'スカイツリー', 'image': 's3://sample-images/skytree.jpg'}
    ],
    'kyoto': [
        {'name': '金閣寺', 'image': 's3://sample-images/kinkakuji.jpg'},
        {'name': '清水寺', 'image': 's3://sample-images/kiyomizudera.jpg'},
        {'name': '伏見稲荷', 'image': 's3://sample-images/fushimi-inari.jpg'}
    ]
}

def handler(event, context):
    """定期実行される人気スポット事前解析（深夜2時実行）"""
    
    cache_manager = AnalysisCacheManager(boto3.resource('dynamodb'))
    languages = ['ja', 'en', 'zh-CN', 'zh-TW', 'ko']
    
    results = []
    
    for region, spots in POPULAR_SPOTS.items():
        for spot in spots:
            # S3から画像を取得
            image_data = get_image_from_s3(spot['image'])
            
            for language in languages:
                # 事前解析実行
                analysis_result = analyze_with_gemini_rest(
                    image_data, 
                    language, 
                    'store'
                )
                
                # キャッシュに保存（48時間）
                image_hash = cache_manager.get_image_hash(image_data)
                cache_manager.save_to_cache(
                    image_hash,
                    language,
                    'store',
                    analysis_result,
                    ttl_hours=48
                )
                
                results.append({
                    'spot': spot['name'],
                    'language': language,
                    'cached_at': datetime.now().isoformat()
                })
    
    # 実行結果をログ保存
    print(f"Pre-analyzed {len(results)} spot-language combinations")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Pre-analyzed {len(results)} combinations',
            'results': results
        })
    }
```

### 4️⃣ 実装スケジュール

```yaml
Week 1（即効性の高い改善）:
  Day 1-2: プロンプト最適化
    - 各言語のプロンプト短縮
    - JSON形式の簡素化
    - テスト実装
  
  Day 3-4: クライアント側画像圧縮
    - browser-image-compression導入
    - UI/UX改善（圧縮状況表示）
    - モバイルテスト
  
  Day 5: 効果測定
    - CloudWatch メトリクス設定
    - A/Bテスト開始

Week 2（インフラ改善）:
  Day 1-2: Lambda Layer準備
    - Sharpライブラリ導入
    - Pillow-SIMD導入
    - デプロイスクリプト作成
  
  Day 3-4: 並列処理実装
    - asyncio導入
    - エラーハンドリング強化
    - タイムアウト設定
  
  Day 5: DynamoDBキャッシュ
    - テーブル作成
    - TTL設定
    - GSI設計

Week 3（高度な最適化）:
  Day 1-2: 画像ハッシュキャッシュ
    - pHash実装
    - 類似画像検索
    - キャッシュヒット率測定
  
  Day 3-4: 人気観光地事前解析
    - Lambda定期実行設定
    - サンプル画像準備
    - 多言語対応
  
  Day 5: 総合テスト
    - パフォーマンステスト
    - 負荷テスト
    - 本番デプロイ準備
```

### 5️⃣ パフォーマンス目標と計測

#### 計測方法

```python
# CloudWatch カスタムメトリクス
def log_performance_metrics(metrics):
    cloudwatch = boto3.client('cloudwatch')
    
    cloudwatch.put_metric_data(
        Namespace='TourismAnalyzer/Performance',
        MetricData=[
            {
                'MetricName': 'TotalProcessingTime',
                'Value': metrics['total_time'],
                'Unit': 'Milliseconds'
            },
            {
                'MetricName': 'GeminiAPITime',
                'Value': metrics['api_time'],
                'Unit': 'Milliseconds'
            },
            {
                'MetricName': 'CacheHitRate',
                'Value': metrics['cache_hit_rate'],
                'Unit': 'Percent'
            }
        ]
    )
```

#### 目標値

| 指標 | 現在 | Week1後 | Week2後 | Week3後（最終） |
|------|------|---------|---------|----------------|
| 画像アップロード | 1-2秒 | 0.3-0.6秒 | 0.3-0.6秒 | 0.3-0.6秒 |
| Lambda起動 | 0.5-1秒 | 0.5-1秒 | 0.2-0.4秒 | 0.2-0.4秒 |
| Gemini API | 2-5秒 | 1.8-4秒 | 1.5-3秒 | 1.2-2.5秒 |
| キャッシュヒット | 0% | 0% | 5% | 20% |
| **合計** | **3.6-8.1秒** | **2.6-5.6秒** | **2.0-4.0秒** | **1.7-3.5秒** |

### 6️⃣ コスト影響分析

```yaml
追加コスト:
  Lambda Layer:
    - ストレージ: $0（250MB以下無料）
    - 実行時メモリ: +64MB（無料枠内）
  
  DynamoDBキャッシュ:
    - ストレージ: $0.25/月（1GB想定）
    - 読み取り: $0（無料枠内）
    - 書き込み: $0（無料枠内）
  
  CloudWatch:
    - カスタムメトリクス: $0.30/月（10メトリクス）
  
  EventBridge:
    - 定期実行: $0（月100万イベント無料）

削減効果:
  S3転送量:
    - 現在: 2MB × 10,000 = 20GB/月（$1.8）
    - 改善後: 0.5MB × 10,000 = 5GB/月（$0.45）
    - 削減: $1.35/月
  
  Lambda実行時間:
    - 現在: 5秒 × 10,000 = 50,000秒
    - 改善後: 2.5秒 × 8,000 = 20,000秒（キャッシュ20%）
    - 削減: 60%（無料枠維持）
  
  Gemini API:
    - 現在: 10,000コール
    - 改善後: 8,000コール（キャッシュ20%）
    - 削減: 20%

月間純削減: 約$0.8/月
ROI: 3ヶ月で実装コスト回収
```

### 7️⃣ リスクと対策

```yaml
リスク:
  1. 並列処理でのレート制限:
     対策: Gemini APIのレート制限監視、バックオフ実装
  
  2. キャッシュの古い情報:
     対策: TTL 24-48時間、人気スポットは定期更新
  
  3. 画像圧縮での品質劣化:
     対策: 品質80%維持、ユーザー設定可能
  
  4. Lambda Layerサイズ:
     対策: 必要最小限のライブラリのみ、定期的な棚卸し

ロールバック計画:
  - Feature Flag で段階的有効化
  - 旧バージョンとの並行稼働
  - CloudWatch アラームで自動ロールバック
```

### 8️⃣ 成功指標（KPI）

```yaml
技術指標:
  - p50レスポンスタイム: < 2.5秒
  - p95レスポンスタイム: < 4.0秒
  - キャッシュヒット率: > 20%
  - エラー率: < 0.1%
  - Lambda同時実行数: < 10

ユーザー体験:
  - 診断完了率: > 95%（現在85%）
  - 離脱率: < 15%（現在25%）
  - ユーザー満足度: > 4.5/5.0
  - リピート率: > 40%

ビジネス指標:
  - 有料プラン転換率: > 12%（現在8%）
  - 月間アクティブユーザー: > 3,000（現在2,000）
  - 月間解析数: > 15,000（現在10,000）
  - インフラコスト: < $50/月維持
```

## 📝 実装チェックリスト

- [ ] プロンプト最適化実装
- [ ] クライアント側画像圧縮導入
- [ ] Lambda Layer作成・デプロイ
- [ ] 並列処理API実装
- [ ] DynamoDBキャッシュテーブル作成
- [ ] 画像ハッシュ機能実装
- [ ] 人気スポット事前解析バッチ
- [ ] CloudWatchダッシュボード作成
- [ ] A/Bテスト設定
- [ ] ドキュメント更新

---

## 📄 文書修正履歴

**2025年9月7日 - A. プロンプト最適化の改善**
- ❌ **修正前**: 「プロンプト最適化（トークン数 -40%）」
  - プロンプト簡略化による精度劣化リスク
  - 現状プロンプトとの比較なし
- ✅ **修正後**: 「アウトプット制限によるパフォーマンス最適化」
  - プロンプト品質100%維持
  - maxOutputTokens大幅削減（2048 → 256/512）
  - 実装コードベースの現状分析追加
  - stopSequences活用で不要出力停止

**修正理由**: ユーザー指摘により、プロンプト簡略化は性能劣化リスクが高く、アウトプット制限の方が効果的であることが判明。実装に基づく正確な改善案に修正。

---

*Phase 7.6: 観光地診断高速化により、ユーザー体験を劇的に改善し、収益化を加速させる*