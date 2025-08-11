# 観光アナライザー - 札幌特化AI観光ガイド

## 🏔️ 概要
観光アナライザーは、札幌に特化したAI画像解析観光サービスです。Google Gemini 2.0 Flashを活用し、札幌の店舗・観光地・料理画像から詳細な地元情報と多言語説明を提供します。

**🌐 稼働中サービス**: https://d22ztxm5q1c726.cloudfront.net/sapporo-mvp.html

## 🎯 主要機能（2025年8月11日現在）

### ✅ 完全実装済み機能
- **🤖 二重AI解析システム**: 店舗観光分析 + 看板メニュー翻訳
- **🌐 完全多言語UI**: 日本語・韓国語・中国語（簡体字・繁体字）・英語対応
- **🔐 3way認証システム**: Google OAuth・メール認証・緊急ログイン
- **💾 データ統合**: S3画像保存 + DynamoDB完全連携
- **📱 モバイル最適化**: レスポンシブPWA設計
- **🎨 美麗UI**: カスタムアニメーション・グラデーション

### 🚧 実装中機能
- **💳 課金システム**: Square決済（¥980/¥1,980プラン）
- **🚫 使用制限**: 無料5回/月制限システム

### 📍 札幌特化対応エリア
- すすきの・大通・札幌駅周辺
- ラーメン横丁・成吉思汗・海鮮市場
- 雪まつり・時計台・大通公園

## 🏗️ 技術スタック（本番稼働中）

### フロントエンド
- **React PWA**: モバイル最適化・オフライン対応
- **CloudFront**: 高速CDN配信（SSL/TLS完全対応）
- **S3**: 静的ホスティング
- **カスタムCSS**: アニメーション・グラデーション・レスポンシブ

### バックエンド
- **AWS Lambda** (Python 3.11): サーバーレス関数
- **API Gateway**: RESTful API・CORS対応
- **DynamoDB**: NoSQLデータベース（PAY_PER_REQUEST）
- **S3**: 画像ストレージ・ライフサイクル管理

### 認証・セキュリティ
- **Amazon Cognito**: OAuth 2.0・JWT認証
- **Google OAuth**: カスタムUI統合
- **IAM**: 最小権限アクセス制御

### AI・解析
- **Google Gemini 2.0 Flash**: 最新画像解析API
- **多言語翻訳**: リアルタイム5言語対応

## 📁 プロジェクト構造（実際のファイル配置）
```
Multimodal_Japan/
├── backend/                    # ✅ サーバーレスバックエンド（本番稼働中）
│   ├── functions/              # Lambda関数群
│   │   ├── auth/              # ✅ 認証機能（Cognito + 3way認証）
│   │   ├── image-analysis/    # ✅ AI画像解析（Gemini 2.0 Flash）
│   │   ├── payment/           # 🚧 決済処理（Square統合準備中）
│   │   └── user-management/   # ✅ ユーザー管理（DynamoDB連携）
│   ├── tests/                 # ✅ テストスイート（86テスト関数）
│   └── serverless.yml         # ✅ AWS本番環境設定
├── frontend/                   # ✅ PWA（CloudFront配信中）
│   ├── sapporo-mvp.html       # ✅ メインアプリケーション
│   ├── css/styles.css         # ✅ カスタムスタイル
│   └── cognito-*.css         # ✅ Cognito UI カスタマイゼーション
├── CLAUDE.md                  # 📋 プロジェクト設計・Phase管理
├── README.md                  # 📖 本ドキュメント
└── history*.md               # 📝 開発履歴（Git除外）
```

## 🚀 現在の開発フェーズ（Phase 6.2完了）

### ✅ 完了済みPhase
- **Phase 1-3**: AWS環境・GitHub連携完了
- **Phase 4-5**: サーバーレス基盤・AI解析実装完了  
- **Phase 5.5**: MVP完全版（予定より早期完成）
- **Phase 6.1**: CloudFront・3way認証システム完了
- **Phase 6.2**: Google OAuth UI グラフィック強化完了

### 🚧 次期実装予定（Phase 6.5）
- Square Developer Account作成
- プレミアムプラン決済フロー（¥980/¥1,980）
- 月5回制限システム実装

## 🚀 開発環境セットアップ

### 前提条件
- macOS
- Node.js v18+ (推奨: v23.11.0)
- Python 3.11+ (推奨: 3.13.3)
- AWS CLI 2.0+
- Docker
- Terraform

### インストール
```bash
# リポジトリクローン
git clone https://github.com/yoshidaagri/PhotoGuideTravel.git
cd PhotoGuideTravel

# 環境変数設定
cp .env.example .env
# .envファイルを編集して実際の値を設定

# フロントエンド依存関係インストール
cd frontend
npm install

# バックエンド依存関係インストール  
cd ../backend
pip install -r requirements.txt

# ローカル開発環境起動
docker-compose up -d
```

### AWS設定
```bash
# AWSプロファイル設定
aws configure --profile ai-tourism-poc

# 環境変数設定
export AWS_PROFILE=ai-tourism-poc
export AWS_REGION=ap-northeast-1
```

## 🧪 テスト実行
```bash
# フロントエンドテスト
cd frontend
npm test

# バックエンドテスト
cd backend
python -m pytest

# 統合テスト
npm run test:integration
```

## 🚀 デプロイ（実際の運用環境）

### 本番環境（現在稼働中）
```bash
# バックエンドデプロイ（AWS Lambda）
cd backend
serverless deploy --stage dev --aws-profile ai-tourism-poc

# フロントエンドデプロイ（CloudFront）
aws s3 cp frontend/sapporo-mvp.html s3://ai-tourism-poc-frontend-dev/ --profile ai-tourism-poc
aws s3 cp frontend/css/styles.css s3://ai-tourism-poc-frontend-dev/css/ --profile ai-tourism-poc
aws cloudfront create-invalidation --distribution-id E38DCQ985NYREA --paths "/*" --profile ai-tourism-poc
```

### 環境情報
- **本番URL**: https://d22ztxm5q1c726.cloudfront.net/sapporo-mvp.html
- **CloudFront Distribution**: E38DCQ985NYREA
- **S3 Bucket**: ai-tourism-poc-frontend-dev
- **API Gateway**: ap-northeast-1リージョン
- **DynamoDB**: PAY_PER_REQUEST・無料枠内運用

## 📊 コスト管理（実績）
- **AWS無料枠完全活用**: 現在 $0-2/月で運用中
- **DynamoDB**: PAY_PER_REQUEST・永続無料枠内
- **Lambda**: 月間数千リクエスト・無料枠内
- **S3**: 画像30日自動削除・容量制御
- **CloudFront**: 12ヶ月無料枠活用中
- **緊急停止機能**: コスト上限 $25/月設定済み

## 🔒 セキュリティ（本番対応済み）
- **IAM**: 最小権限・プロファイル分離
- **Cognito**: OAuth 2.0・JWT認証
- **API Gateway**: CORS・レート制限設定
- **SSL/TLS**: CloudFront完全暗号化
- **データ保護**: S3暗号化・DynamoDB暗号化

## 🎯 収益化ロードマップ
### Phase 6.5（実装中）
- Square決済統合
- プレミアムプラン（¥980・¥1,980）
- 使用制限システム

### 目標
- **月1目標**: ¥13,800（50ユーザー・10人課金）
- **月3目標**: ¥55,000（200ユーザー・50人課金）
- **月6目標**: ¥130,000（500ユーザー・120人課金）

## 🤝 開発体制
- **個人開発**: MVP・収益化優先
- **AI支援**: Claude Code活用
- **学習重視**: AWS段階的習得

## 📄 ライセンス
個人開発・収益化プロジェクト - All Rights Reserved

## 📞 サポート・連絡
- **開発者**: Manabu Yoshida
- **GitHub**: yoshidaagri
- **現在状況**: Phase 6.2完了・Phase 6.5準備中

---
*🏔️ 札幌特化AI観光ガイド「観光アナライザー」*  
*Updated: 2025-08-11 - Phase 6.2 Google OAuth UI強化完了*