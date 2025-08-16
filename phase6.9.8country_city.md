# Phase 6.9.8 国名・都市名入力機能追加
## 観光AI解析精度向上のための地域指定機能

**作成日**: 2025年8月16日  
**Phase**: 6.9.8 (Phase 6.9.7完了後の機能拡張)  
**目的**: AI解析精度向上のための地域コンテキスト追加

---

## 🎯 機能概要

### **追加機能**
- 国名(country)・都市名(city)入力欄をUI追加
- ユーザーごとの地域設定保存・編集機能
- AI解析時の地域コンテキスト自動追加

### **効果**
- AI解析精度の向上（地域特有の店舗・観光地情報）
- ユーザー体験向上（個人に最適化された解析結果）
- 地域別分析データ収集

---

## 📋 詳細仕様

### **1. UI追加仕様**
```html
配置場所: 
  解析言語を選択 (language-section)
  ↓
  【新規】国名・都市名入力 (location-section) ← 追加
  ↓
  解析タイプを選択 (analysis-type-section)

入力項目:
  - 国名 (country): テキスト入力欄
  - 都市名 (city): テキスト入力欄
  - 保存ボタン・編集ボタン
```

### **2. DynamoDB拡張仕様**
```yaml
テーブル: ai-tourism-poc-users-dev
追加カラム:
  - country: String (国名)
  - city: String (都市名)
  - location_updated_at: String (地域設定更新日時)

既存データ影響: なし（新規カラムのため）
```

### **3. AI解析プロンプト拡張仕様**
```python
プロンプト先頭追加ロジック:
  if country and city:
      prompt = f"私は{country}の{city}の情報を知りたい。" + original_prompt
  elif country:
      prompt = f"私は{country}のことを尋ねている。" + original_prompt  
  elif city:
      prompt = f"私は{city}の情報を知りたい。" + original_prompt
  else:
      prompt = original_prompt  # 変更なし
```

---

## 🛠️ 実装計画（調査結果基づく修正版）

### **Phase 1: 安全な準備・バックアップ (30分)**
```yaml
git操作:
  1. feature/phase-6-9-8-location-input ブランチ作成
  2. 現在の状態をコミット
  3. 改修対象8ファイルのバックアップ作成

バックアップ対象:
  - frontend/index.html, css/styles.css, js/main.js, js/auth.js, js/translations.js
  - backend/functions/auth/handler.py
  - backend/functions/image-analysis/handler_gemini.py
  - backend/serverless.yml
```

### **Phase 2: バックエンド実装 (1.5-2時間)**
```yaml
優先順位: バックエンドAPIを先に実装（フロントエンドのテスト用）

2.1: auth/handler.py (45分)
  - handle_update_location()関数追加
  - handle_get_user_info()にcountry/city返却追加
  - main()にパス分岐'update-location'追加

2.2: serverless.yml (15分)  
  - functions.auth.events にPUTエンドポイント追加
  - デプロイ・動作確認

2.3: handler_gemini.py (45分)
  - get_user_location()関数追加
  - build_context_prompt()関数追加  
  - line 393修正: プロンプト構築変更
  - ユーザートークンからuser_id取得ロジック追加
```

### **Phase 3: フロントエンド実装 (2-2.5時間)**
```yaml
3.1: UI基盤 (60分)
  - index.html: location-section追加 (lines 94-95間)
  - styles.css: レスポンシブスタイル追加
  - translations.js: 5言語テキスト追加

3.2: JavaScript機能 (90分)
  - main.js: saveLocationSettings(), API呼び出し実装
  - auth.js: updateUserInfoDisplay()拡張, loadUserLocationSettings()追加
  
3.3: UI統合テスト (30分)
  - 国名・都市名入力→保存→表示の一連動作確認
  - レスポンシブデザイン確認
```

### **Phase 4: AI解析統合・全体テスト (1時間)**  
```yaml
4.1: AI解析プロンプト確認 (30分)
  - 地域設定→AI解析→プロンプト反映確認
  - 各言語でのプロンプト動作確認

4.2: 全機能統合テスト (30分)
  - 既存機能（認証・決済・画像解析）動作確認
  - 新機能と既存機能の連携確認
  - エラーハンドリング確認
```

---

## 📂 詳細影響範囲分析結果

### **🔍 現在のシステム調査結果**

#### **DynamoDB現状**
```yaml
ai-tourism-poc-users-dev テーブル:
  AttributeDefinitions: user_id (String) のみ
  実際保存データ: 
    - user_id, email, display_name, auth_provider
    - user_type, premium_expiry, monthly_analysis_count
    - total_analysis_count, preferred_language
    - created_at, updated_at, last_login_at

追加予定属性:
  - country: String (国名)
  - city: String (都市名) 
  - location_updated_at: String (地域設定更新日時)

影響: DynamoDBはNoSQLのため新属性追加は既存データに影響なし
```

#### **現在のAPIエンドポイント**
```yaml
影響あり:
  - GET /auth/user-info: country/city返却対応必要
  
新規追加:
  - PUT /auth/location: 地域設定保存用

影響なし:
  - /auth/check-usage, /auth/increment-usage
  - /auth/verify-token, /auth/login, /auth/signup
  - /analyze (プロンプト修正のみ)
```

#### **AI解析プロンプト構築**
```python
# handler_gemini.py line 393 修正箇所
現在: base_prompt = tourism_prompts.get(language, tourism_prompts['ja'])

修正後: 
def build_context_prompt(user_id, language, analysis_type):
    base_prompt = tourism_prompts.get(language, tourism_prompts['ja'])
    
    # ユーザーの地域設定取得
    user_location = get_user_location(user_id)
    country = user_location.get('country', '')
    city = user_location.get('city', '')
    
    # 地域コンテキスト追加
    if country and city:
        context = f"私は{country}の{city}の情報を知りたい。"
    elif country:
        context = f"私は{country}のことを尋ねている。"
    elif city:
        context = f"私は{city}の情報を知りたい。"
    else:
        context = ""
    
    return context + base_prompt
```

### **📂 改修対象ファイル一覧（修正版）**

#### **フロントエンド (5ファイル)**
```yaml
1. frontend/index.html
   - location-section追加 (lines 94-95間)
   - 国名・都市名入力欄UI
   
2. frontend/css/styles.css  
   - .location-section スタイル追加
   - レスポンシブデザイン対応
   
3. frontend/js/main.js
   - saveLocationSettings()関数追加
   - API呼び出し: PUT /auth/location
   
4. frontend/js/auth.js
   - updateUserInfoDisplay()にcountry/city表示追加
   - loadUserLocationSettings()追加
   
5. frontend/js/translations.js
   - locationSection関連テキスト（5言語）追加
```

#### **バックエンド (3ファイル + DB)**
```yaml
1. backend/functions/auth/handler.py
   - handle_update_location()関数追加
   - handle_get_user_info()でcountry/city返却
   - main()にパス分岐追加: 'update-location'
   
2. backend/functions/image-analysis/handler_gemini.py  
   - get_user_location()関数追加（DynamoDB読み取り）
   - build_context_prompt()関数追加
   - line 393修正: プロンプト構築ロジック変更
   
3. backend/serverless.yml
   - functions.auth.events に PUT エンドポイント追加
   - DynamoDB iamRoleStatements確認（変更不要）

4. DynamoDB (NoSQL - スキーマ変更不要)
   - 新属性追加: country, city, location_updated_at
   - 既存データ影響: なし
   - マイグレーション: 不要
```

---

## 🚨 リスク管理・ロールバック計画

### **事前バックアップ必須ファイル（修正版）**
```bash
# 改修前バックアップ作成（全8ファイル）
cp frontend/index.html frontend/index.html.backup
cp frontend/css/styles.css frontend/css/styles.css.backup  
cp frontend/js/main.js frontend/js/main.js.backup
cp frontend/js/auth.js frontend/js/auth.js.backup
cp frontend/js/translations.js frontend/js/translations.js.backup
cp backend/functions/auth/handler.py backend/functions/auth/handler.py.backup
cp backend/functions/image-analysis/handler_gemini.py backend/functions/image-analysis/handler_gemini.py.backup
cp backend/serverless.yml backend/serverless.yml.backup
```

### **緊急ロールバック手順**
```bash
# 1コマンドで全ファイル復元
git checkout HEAD~1 -- frontend/index.html frontend/css/styles.css frontend/js/main.js frontend/js/auth.js frontend/js/translations.js backend/functions/auth/handler.py backend/functions/image-analysis/handler_gemini.py

# または個別復元
mv frontend/index.html.backup frontend/index.html
mv frontend/css/styles.css.backup frontend/css/styles.css
# ... (他ファイルも同様)
```

### **テスト失敗時の対応**
```yaml
Level 1: UI表示問題
  - CSS調整・HTML修正
  
Level 2: JavaScript動作問題  
  - console.logデバッグ
  - 段階的機能無効化
  
Level 3: バックエンドAPI問題
  - Lambda関数ロールバック
  - DynamoDBスキーマ確認
  
Level 4: 全体動作不良
  - 緊急ロールバック実行
  - バックアップファイル復元
```

---

## 🎯 成功指標（詳細版）

### **機能テスト**
- [ ] 国名・都市名入力欄表示確認（5言語）
- [ ] PUT /auth/location API動作確認（curl/Postmanテスト）
- [ ] DynamoDBへのcountry/city保存確認（AWS Console確認）
- [ ] GET /auth/user-info でcountry/city返却確認
- [ ] AI解析時プロンプト先頭への地域コンテキスト追加確認
- [ ] 既存認証・決済機能の動作確認（リグレッションテスト）

### **品質テスト**
- [ ] レスポンシブデザイン確認（768px, 480px breakpoint）
- [ ] 空値・null入力のエラーハンドリング確認
- [ ] 長い地名入力時の表示確認
- [ ] serverless deploy成功確認
- [ ] CloudWatch Logsエラー確認

### **AI解析精度テスト**
- [ ] 国名のみ指定: "私は日本のことを尋ねている。" プロンプト確認
- [ ] 都市名のみ指定: "私は札幌の情報を知りたい。" プロンプト確認  
- [ ] 国名・都市名両方: "私は日本の札幌の情報を知りたい。" プロンプト確認
- [ ] 未指定時: 従来通りのプロンプト動作確認

---

## 💡 実装時の注意点

### **既存ロジックへの影響最小化**
- プロンプト修正は文字列結合のみ
- DynamoDB新規カラムは既存データ影響なし
- JavaScript関数は新規追加、既存関数は最小限修正

### **多言語対応**
- 5言語すべてでUI翻訳追加
- 国名・都市名入力は各言語で自由入力
- エラーメッセージも多言語対応

### **パフォーマンス考慮**
- 地域設定保存はユーザー操作時のみ
- AI解析での文字列結合負荷は最小限
- DynamoDB読み書きは最小限に抑制

---

**Phase 6.9.8で地域コンテキスト機能を追加し、AI解析精度の大幅向上を実現！**