# Phase 6.6 Search: Gemini 2.0「Search as a tool」による観光AI解析精度向上（最小実装版）

## 📚 概要

### 背景
- 位置情報による精度向上案から方針転換
- Gemini 2.0の「Search as a tool」機能により、Web検索を活用した最新情報の取得が可能に
- 既存のGemini API呼び出し部分の最小限の修正で実現

### 実装方針
- **最小限の変更**: `analyze_image_with_gemini_rest`関数のみ修正
- **即座に戻せる設計**: 既存コードをコメントアウトで保持
- **ON/OFF不要**: 常時Search機能を使用（APIキーが有料版の場合のみ動作）

### 期待される効果
1. **最新情報の提供**: 営業時間、定休日、価格等のリアルタイム情報
2. **詳細情報の補強**: 公式サイト、レビューサイトからの情報取得
3. **誤認識の修正**: Web検索により正しい店舗情報を確認

## ⚠️ 前提条件と制約

### 必須要件
- **有料版APIキー**: Search as a toolの利用には有料版のGoogle API Keyが必要
- **API Version**: `v1alpha`の指定が必要
- **モデル**: `gemini-2.0-flash-exp`の使用

### コスト影響
```yaml
追加コスト:
  - Search付きAPI呼び出し: 通常の約2-3倍の料金
  - 月間想定: $10-30追加（利用量による）
  
コスト制御:
  - Search機能のON/OFF切り替え
  - 1日あたりの検索回数制限
  - キャッシュによる重複検索の回避
```

## 🔧 最小限の実装計画

### 修正ファイル
- `backend/functions/image-analysis/handler_gemini.py` のみ

### 修正内容: analyze_image_with_gemini_rest関数の変更

```python
def analyze_image_with_gemini_rest(image_data, language='ja', analysis_type='store', location_context=None):
    """
    REST APIでGemini APIを呼び出す（Search as a tool対応版）
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
        
        # === SEARCH AS A TOOL 対応開始 ===
        # 既存のコードをコメントアウト [ORIGINAL_API_CALL_START]
        """
        # Gemini APIリクエスト
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-latest:generateContent?key={api_key}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            'contents': [{
                'parts': [
                    {'text': base_prompt},
                    {
                        'inline_data': {
                            'mime_type': 'image/jpeg',
                            'data': image_data
                        }
                    }
                ]
            }],
            'generationConfig': {
                'temperature': 0.7,
                'topK': 40,
                'topP': 0.95,
                'maxOutputTokens': 2048,
            }
        }
        """
        # [ORIGINAL_API_CALL_END]
        
        # Search as a tool 対応の新しいAPI呼び出し [SEARCH_API_CALL_START]
        # v1alpha APIエンドポイントを使用
        url = f"https://generativelanguage.googleapis.com/v1alpha/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # プロンプトにWeb検索を活用する指示を追加
        search_enhanced_prompt = base_prompt + "\n\n必要に応じてWeb検索を活用し、店舗の営業時間、価格、最新情報を含めて回答してください。"
        
        payload = {
            'contents': [{
                'parts': [
                    {'text': search_enhanced_prompt},
                    {
                        'inline_data': {
                            'mime_type': 'image/jpeg',
                            'data': image_data
                        }
                    }
                ]
            }],
            'tools': [{
                'google_search': {}  # Search as a toolを有効化
            }],
            'generationConfig': {
                'temperature': 0.7,
                'topK': 40,
                'topP': 0.95,
                'maxOutputTokens': 3000,  # 検索結果を含むため増量
            }
        }
        # [SEARCH_API_CALL_END]
        # === SEARCH AS A TOOL 対応終了 ===
        
        # API呼び出し実行
        req = urllib.request.Request(url, 
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        # タイムアウトを増やす（検索時間を考慮） [TIMEOUT_CHANGE]
        # with urllib.request.urlopen(req, timeout=30) as response:  # 元: 30秒
        with urllib.request.urlopen(req, timeout=60) as response:  # 新: 60秒
            response_data = response.read().decode('utf-8')
            result = json.loads(response_data)
        
        # レスポンス処理
        if 'candidates' in result and result['candidates']:
            candidate = result['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                analysis_text = ""
                for part in candidate['content']['parts']:
                    if 'text' in part:
                        analysis_text += part['text']
                
                if analysis_text:
                    return {
                        'analysis': analysis_text,
                        'language': language,
                        'timestamp': get_jst_isoformat(),
                        'model': 'gemini-2.0-flash-exp-with-search',  # モデル名を更新 [MODEL_NAME_CHANGE]
                        'status': 'success',
                        # Search使用フラグを追加 [SEARCH_FLAG_ADD]
                        'search_enhanced': True
                    }
        
        # エラー時の処理
        return {
            'analysis': 'エラーが発生しました。もう一度お試しください。',
            'language': language,
            'timestamp': get_jst_isoformat(),
            'model': 'gemini-2.0-flash-exp',
            'status': 'error',
            'error': 'No valid response from API'
        }
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"HTTP Error {e.code}: {error_body}")
        # 検索機能が使えない場合は通常のAPIにフォールバック [FALLBACK_LOGIC]
        if "v1alpha" in url and e.code in [400, 403, 404]:
            print("Falling back to standard API without search...")
            # 再帰呼び出しを避けるため、直接標準APIを呼び出すロジックをここに記述
            # （実装は省略）
        return {
            'analysis': f'APIエラーが発生しました: {e.code}',
            'language': language,
            'timestamp': get_jst_isoformat(),
            'model': 'error',
            'status': 'error',
            'error': f'HTTP {e.code}: {error_body}'
        }
        
    except Exception as e:
        print(f"Error in Gemini API call: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        return {
            'analysis': 'エラーが発生しました。もう一度お試しください。',
            'language': language,
            'timestamp': get_jst_isoformat(),
            'model': 'error',
            'status': 'error',
            'error': str(e)
        }
```

## 📝 変更箇所まとめ

### 変更内容
1. **APIエンドポイント変更**: 
   - `v1beta` → `v1alpha`
   - モデル: `gemini-2.0-flash-latest` → `gemini-2.0-flash-exp`

2. **Search as a tool追加**:
   - payloadに `'tools': [{'google_search': {}}]` を追加
   - プロンプトに検索活用の指示を追加

3. **その他の調整**:
   - `maxOutputTokens`: 2048 → 3000（検索結果用）
   - タイムアウト: 30秒 → 60秒
   - レスポンスに `search_enhanced: true` フラグ追加

### タグ一覧（元に戻す際の参照用）
- `[ORIGINAL_API_CALL_START]` ～ `[ORIGINAL_API_CALL_END]`: 元のAPI呼び出しコード
- `[SEARCH_API_CALL_START]` ～ `[SEARCH_API_CALL_END]`: 新しいSearch対応コード
- `[TIMEOUT_CHANGE]`: タイムアウト変更箇所
- `[MODEL_NAME_CHANGE]`: モデル名変更箇所
- `[SEARCH_FLAG_ADD]`: Search使用フラグ追加箇所
- `[FALLBACK_LOGIC]`: フォールバック処理

## 🚀 実装手順

### 1. 環境変数の確認
```bash
# 有料版APIキーが設定されているか確認
grep GOOGLE_GEMINI_API_KEY backend/.env
```

### 2. コード修正の適用
上記の`analyze_image_with_gemini_rest`関数の修正を`handler_gemini.py`に適用

### 3. デプロイ
```bash
cd backend
set -a && source .env && set +a && npx serverless deploy --stage dev
```

### 4. 動作確認
- テスト画像で解析を実行
- CloudWatch Logsでエラーを確認
- Search機能が動作しているか確認

## 📝 元に戻す方法

1. タグを参考にコメントアウトされた部分を復元
2. 新しいコードを削除またはコメントアウト
3. タイムアウトを30秒に戻す
4. 再デプロイ

## 🚨 注意事項

- **有料APIキー必須**: 無料版では動作しません
- **コスト増加**: 通常のAPI呼び出しより高額
- **レスポンス時間**: 検索により遅くなる可能性

## 🔍 想定される改善例

### Before（通常の画像解析）
```
この画像には飲食店の看板が見えます。
ラーメン店のようです。
詳細な情報は画像からは読み取れません。
```

### After（Search as a tool使用）
```
【店舗情報】
店名: 麺屋 武蔵 新宿本店
住所: 東京都新宿区西新宿7-2-6
営業時間: 11:00-23:00（日曜は22:00まで）
定休日: 無休

【メニュー情報】
- 特製つけ麺: ¥1,200
- 濃厚魚介豚骨ラーメン: ¥1,000
- チャーシュー丼セット: +¥400

【アクセス】
新宿駅西口から徒歩5分

【最新情報】
2024年1月より全席禁煙
キャッシュレス決済対応（PayPay、クレジットカード可）

【口コミ評価】
Google: 4.2/5.0 (523件)
食べログ: 3.58/5.0
```

この改善により、観光客により実用的で詳細な情報を提供できるようになります。

## 📋 実装チェックリスト

- [x] 有料版Google API Keyの確認
- [x] handler_gemini.pyのバックアップ作成
- [x] コード修正の適用
- [x] ローカルテスト
- [x] AWSへのデプロイ
- [x] 動作確認
- [ ] CloudWatch Logsでエラー監視
- [ ] コスト監視設定

---

## 🎉 実装結果（2025年8月14日）

### 実装完了内容

#### 1. バックアップ作成
```bash
# 実行日時: 2025-08-14 04:43:15
cp handler_gemini.py handler_gemini.py.backup.20250814_044315
```

#### 2. コード変更の適用
以下の変更を`analyze_image_with_gemini_rest`関数に適用：

- ✅ **APIエンドポイント変更**: 
  - `https://generativelanguage.googleapis.com/v1beta/models/` 
  - → `https://generativelanguage.googleapis.com/v1alpha/models/`
  
- ✅ **モデル名変更**: 
  - `gemini-2.0-flash-latest` → `gemini-2.0-flash-exp`
  
- ✅ **Search as a tool追加**:
  ```python
  "tools": [{
      "google_search": {}  # Search as a toolを有効化
  }]
  ```
  
- ✅ **タイムアウト延長**: 
  - デフォルト → 60秒
  
- ✅ **プロンプト強化**:
  ```python
  search_enhanced_prompt = prompt + "\n\n必要に応じてWeb検索を活用し、店舗の営業時間、価格、最新情報を含めて回答してください。"
  ```

- ✅ **レスポンス拡張**:
  ```python
  'model': 'gemini-2.0-flash-exp-with-search',
  'search_enhanced': True
  ```

#### 3. エラーハンドリング強化
```python
except urllib.error.HTTPError as e:
    error_body = e.read().decode('utf-8')
    print(f"HTTP Error {e.code}: {error_body}")
    if "v1alpha" in url and e.code in [400, 403, 404]:
        print("Search feature may not be available. Consider fallback to standard API.")
```

### デプロイ情報

#### GitHubコミット
```bash
# コミットID: ed59c30
# コミットメッセージ: feat: Implement Gemini 2.0 Search as a tool for enhanced tourism analysis
# Push完了: 2025-08-14 04:45:00
```

#### AWS Lambda デプロイ
```
実行時刻: 2025-08-14 04:45:30
ステージ: dev
リージョン: ap-northeast-1
デプロイ時間: 47秒

エンドポイント:
- POST https://f4n095fm2j.execute-api.ap-northeast-1.amazonaws.com/dev/analyze
```

### 動作確認URL
- **本番環境**: https://d22ztxm5q1c726.cloudfront.net/tourism-guide.html

### タグ一覧（ロールバック用）
実装したコードには以下のタグを付与：
- `[ORIGINAL_API_CALL_START]` / `[ORIGINAL_API_CALL_END]`: 元のAPI呼び出しコード
- `[SEARCH_API_CALL_START]` / `[SEARCH_API_CALL_END]`: 新しいSearch対応コード
- `[TIMEOUT_CHANGE]`: タイムアウト変更箇所
- `[MODEL_NAME_CHANGE]`: モデル名変更箇所
- `[SEARCH_FLAG_ADD]`: Search使用フラグ追加箇所
- `[FALLBACK_LOGIC]`: フォールバック処理

### 動作確認結果（2025年8月14日）

#### ✅ 実装成功確認
- **フロントエンド表示**: 正常に動作、解析結果が完全に表示される
- **Search機能**: 店舗検索が正常に実行され、詳細情報が取得できている
- **レスポンス内容**: 
  - 店舗の詳細情報（営業時間、定休日、メニュー等）が含まれる
  - Web検索による最新情報が反映されている
  - 多言語対応も正常に動作

#### CloudWatchログ確認
```
Parts count: 2
Part 0: 基本的な画像解析結果
Part 1: Search as a toolによる詳細な店舗情報
```

Search as a toolが正常に動作し、画像解析と合わせて詳細な観光情報を提供できることを確認しました。

### 次のステップ
1. **ログ監視**: CloudWatch Logsでエラー発生状況を継続的に確認
2. **コスト監視**: API使用量とコストの追跡開始
3. **効果測定**: Search有無での解析結果の比較
4. **ユーザーフィードバック**: 実際の利用者からの反応を収集

### ロールバック手順
問題が発生した場合：
```bash
# 1. バックアップから復元
cd /Users/manabu/python/Multimodal_Japan/backend/functions/image-analysis
cp handler_gemini.py.backup.20250814_044315 handler_gemini.py

# 2. 再デプロイ
cd ../../
set -a && source .env && set +a && npx serverless deploy --stage dev
```