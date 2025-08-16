# 🎭 Tourism Analyzer E2E Tests (Playwright)

観光アナライザーのフロントエンドE2Eテスト自動化

## 📋 テスト概要

### カバレッジ対象
- ✅ **Google認証フロー**: login.html → tourism-guide.html認証完了
- ✅ **UI状態管理**: 認証前後のUI表示切り替え
- ✅ **localStorage管理**: 認証トークン・ユーザー情報の保存・削除
- ✅ **エラーハンドリング**: 認証失敗時の適切なエラー表示
- ✅ **レスポンシブ対応**: モバイル・デスクトップ表示確認

### テスト環境
- **対象URL**: https://d22ztxm5q1c726.cloudfront.net
- **ブラウザ**: Chrome, Firefox, Safari, Mobile Chrome, Mobile Safari
- **テストフレームワーク**: Playwright + TypeScript

## 🚀 セットアップ・実行方法

### 1. 依存関係インストール
```bash
cd frontend/e2e
npm install
npx playwright install
```

### 2. テスト実行
```bash
# 全テスト実行
npm test

# 認証フローのみテスト
npm run test:auth

# ヘッドレスモードで実行
npm run test:headless

# デバッグモードで実行
npm run test:debug
```

### 3. レポート確認
```bash
# テスト結果レポート表示
npm run report
```

## 📁 ファイル構成

```
frontend/e2e/
├── tests/
│   └── auth.spec.ts              # Google認証フローテスト
├── playwright.config.ts          # Playwright設定
├── package.json                  # 依存関係
├── README.md                     # このファイル
├── playwright-report/            # テストレポート (自動生成)
└── test-results/                 # テスト結果 (自動生成)
```

## 🎯 テストシナリオ詳細

### auth.spec.ts - Google認証フロー
1. **login.html基本表示確認**
   - ページタイトル・メインコンテンツ表示
   - 戻るリンク表示確認

2. **Google Identity Services初期化**
   - スクリプト読み込み確認
   - 初期化ログ確認

3. **Google認証ボタン表示**
   - サインインボタン表示確認
   - ローディング状態管理確認

4. **テストモード認証フロー**
   - API呼び出しモック
   - 認証成功シミュレーション
   - tourism-guide.htmlリダイレクト確認
   - localStorage認証情報保存確認

5. **認証後UI状態確認**
   - 認証済みUI表示確認
   - ログインセクション非表示確認

6. **ログアウト機能**
   - localStorage削除確認
   - ログインセクション再表示確認

7. **エラーハンドリング**
   - 認証失敗時エラー表示確認
   - 再試行ボタン表示確認

8. **モバイル表示対応**
   - レスポンシブデザイン確認
   - モバイルビューポート対応確認

## 🔧 設定詳細

### playwright.config.ts
- **baseURL**: https://d22ztxm5q1c726.cloudfront.net
- **timeout**: 30秒
- **retries**: CI環境で2回
- **screenshot/video**: 失敗時のみ
- **並列実行**: CI環境以外で有効

### テストデータ
- **テスト用ユーザー**: yoshidaagri@gmail.com
- **テスト用トークン**: test_token_yoshidaagri
- **API Mock**: /dev/auth/google-signin

## ⚡ CI/CD統合

### GitHub Actions統合例
```yaml
- name: Run E2E Tests
  run: |
    cd frontend/e2e
    npm ci
    npx playwright install --with-deps
    npm test
```

### 品質ゲート
- **テスト成功率**: 100% (全テスト成功必須)
- **レスポンス時間**: 5秒以内
- **エラー率**: 0% (エラーハンドリングテスト除く)

## 🚨 重要な注意事項

1. **本番環境テスト**: CloudFront本番URLでテスト実行
2. **テストモード使用**: 実際のGoogle認証は使わずAPIモックを使用
3. **localStorageクリア**: 各テスト前に認証状態をクリア
4. **ネットワーク待機**: Google Identity Services読み込み待機必須
5. **レスポンシブ確認**: モバイル・デスクトップ両方でテスト

## 📊 テスト結果の見方

### 成功例
```
✓ login.htmlの基本表示確認 (2.3s)
✓ Google Identity Services初期化確認 (1.8s)
✓ Google認証ボタン表示確認 (3.1s)
✓ テストモード認証フロー完全テスト (4.2s)
✓ 認証後のUI状態確認 (2.1s)
✓ ログアウト機能確認 (1.9s)
✓ 認証エラーハンドリング確認 (2.5s)
✓ モバイル表示対応確認 (1.7s)
```

### 失敗時の対応
1. playwright-report/index.html でエラー詳細確認
2. スクリーンショット・動画で問題箇所特定
3. コンソールログで JavaScript エラー確認
4. 必要に応じてテストコード・実装コード修正

## 🎯 今後の拡張予定

- **画像解析フローテスト**: image-analysis.spec.ts
- **決済フローテスト**: payment.spec.ts
- **UI レスポンシブテスト**: ui-responsive.spec.ts
- **パフォーマンステスト**: 画像読み込み・API レスポンス時間
- **アクセシビリティテスト**: WCAG 2.1 準拠確認