# 観光アナライザー - AI観光ガイド

## 🏔️ 概要
観光アナライザーは、AI画像解析を活用した観光サービスです。Google Gemini 2.0 Flashを活用し、店舗・観光地・料理画像から詳細な地元情報と多言語説明を提供します。

**🌐 稼働中サービス**: https://anatri.net/index.html  
**🎨 ランディングページ**: https://anatri.net/lp.html

## 🎯 主要機能（2025年8月31日現在）

### ✅ 完全実装済み機能
- **🤖 二重AI解析システム**: 店舗観光分析 + 看板メニュー翻訳
- **🌐 完全多言語UI**: 日本語・韓国語・中国語（簡体字・繁体字）・英語対応
- **🔐 3way認証システム**: Google OAuth・メール認証・緊急ログイン
- **💾 データ統合**: S3画像保存 + DynamoDB完全連携
- **📱 モバイル最適化**: レスポンシブPWA設計
- **🎨 美麗UI**: カスタムアニメーション・グラデーション・ランダム背景画像
- **🖼️ ランダム背景システム**: ヒーローセクション・機能カードに旅行関連画像
- **📍 地域設定機能**: ユーザー国名・都市名設定（解析精度向上）
- **💳 Stripe決済システム**: プレミアムプラン（¥980/¥1,980）
- **🚫 使用制限**: 無料5回/月制限システム
- **🌐 カスタムドメイン**: anatri.net運用中

### ✨ 最近の機能追加・更新（2025年8月31日）
- **🖼️ ランダム背景システム**: ヒーローセクションに5種類の旅行画像をランダム表示
- **🎨 機能カード背景**: 画像解析・多言語・地域特化の各機能に専用背景画像
- **📱 UI統一化**: login.html言語選択ボタンをlp.htmlデザインに統一
- **🌐 文言国際化**: 「札幌・北海道特化」から「国・都市入力対応」に変更
- **⚡ 画像最適化**: 背景画像を3.9M→150KB以下に圧縮（読み込み速度改善）
- **🔧 anatri.netドメイン**: CloudFrontエイリアス設定・CSS相対パス修正

### 📍 対応機能
- 各地の観光地・名所解析
- 地元グルメ・名物料理解析
- イベント・シーズン情報提供

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

### 認証・セキュリティ・決済
- **Amazon Cognito**: OAuth 2.0・JWT認証
- **Google OAuth**: カスタムUI統合
- **Stripe**: 決済システム（プレミアムプラン）
- **IAM**: 最小権限アクセス制御

### AI・解析
- **Google Gemini 2.0 Flash**: 最新画像解析API
- **多言語翻訳**: リアルタイム5言語対応

## 📁 プロジェクト構造（実際のファイル配置）
```
Multimodal_Japan/
├── backend/                    # ✅ サーバーレスバックエンド（本番稼働中）
│   ├── functions/              # Lambda関数群
│   │   ├── auth/              # ✅ 認証機能（Cognito + 3way認証 + 地域設定）
│   │   ├── image-analysis/    # ✅ AI画像解析（Gemini 2.0 Flash）
│   │   ├── payment/           # ✅ Stripe決済処理（プレミアムプラン）
│   │   ├── admin-dashboard/   # ✅ 管理ダッシュボード（独立システム）
│   │   └── user-management/   # ✅ ユーザー管理（DynamoDB連携）
│   ├── tests/                 # ✅ テストスイート（86テスト関数）
│   └── serverless.yml         # ✅ AWS本番環境設定
├── frontend/                   # ✅ PWA（CloudFront配信中）
│   ├── tourism-guide.html     # ✅ メインアプリケーション
│   ├── css/styles.css         # ✅ カスタムスタイル
│   └── cognito-*.css         # ✅ Cognito UI カスタマイゼーション
├── CLAUDE.md                  # 📋 プロジェクト設計・Phase管理
├── README.md                  # 📖 本ドキュメント
└── history*.md               # 📝 開発履歴（Git除外）
```

## 🚀 現在の開発フェーズ（Phase 7.5完了）

### ✅ 完了済みPhase
- **Phase 1-3**: AWS環境・GitHub連携完了
- **Phase 4-5**: サーバーレス基盤・AI解析実装完了  
- **Phase 5.5**: MVP完全版（予定より早期完成）
- **Phase 6.1**: CloudFront・3way認証システム完了
- **Phase 6.2**: Google OAuth UI グラフィック強化完了
- **Phase 6.5-6.8**: Stripe決済システム・プレミアムプラン実装完了
- **Phase 6.9**: 地域設定機能・管理ダッシュボード実装完了
- **Phase 6.9.8**: 地域設定バグ修正・認証処理最適化完了
- **Phase 7.3**: ランダム背景システム・UI/UX強化・anatri.netドメイン対応完了
- **Phase 7.4**: ユーザー体験向上・パフォーマンス最適化完了
- **Phase 7.5**: AI解析機能強化・観光情報充実化完了

### 🎨 Phase 7.3の主要実装内容
- **ヒーローセクション**: 5種類の旅行画像ランダム表示システム
- **機能カード**: 各機能に専用背景画像（01.picture.png, 02.earth.png, 03.japan.png）
- **UI統一化**: 全ページで言語選択ボタンデザイン統一
- **文言国際化**: 地域特化から汎用的表現に変更（全5言語対応）
- **パフォーマンス最適化**: 画像圧縮・読み込み速度向上
- **ドメイン対応**: anatri.net本格運用開始・CloudFrontエイリアス設定

### 📱 Phase 7.4の主要実装内容
- **モバイルファースト最適化**: スマートフォン操作性の大幅改善
- **画像圧縮自動化**: アップロード時の自動最適化システム導入
- **プログレッシブ画像読み込み**: 低解像度から高解像度への段階的表示
- **オフライン対応強化**: Service Workerによるキャッシュ戦略最適化
- **アクセシビリティ向上**: WCAG 2.1 AA準拠の実装
- **ローディング体験改善**: スケルトンスクリーン・プレースホルダー実装

### 🤖 Phase 7.5の主要実装内容
- **AI解析精度向上**: Gemini 2.0 Flashの最新機能活用
- **観光情報データベース連携**: 各地の詳細観光情報自動取得
- **営業時間・定休日表示**: リアルタイム営業情報の提供
- **混雑状況予測**: 時間帯別の混雑度AI予測機能
- **おすすめルート生成**: 複数観光地の最適ルート自動作成
- **天気情報統合**: 観光地の天気予報・服装アドバイス機能

### 🌱 次期実装予定（Phase 8.0）：社会貢献プログラム「観光地を守る」

#### 🎯 Phase 8の理念
観光アナライザーは単なる利便性向上ツールではなく、**観光地が抱える問題解決に貢献するサービス**を目指します。
観光による恩恵を受けるだけでなく、**売上の一部を観光地の課題解決に還元**することで、持続可能な観光業界の発展に貢献します。

#### 📊 売上還元プログラム
- **寄付割合**: 月間売上の5%を観光地支援基金として積立
- **寄付先選定**: ユーザー投票により毎月の支援先を決定
- **透明性確保**: 寄付実績・使途を管理ダッシュボードで公開
- **活動報告**: 支援先からの活動報告をアプリ内で共有

#### 🌿 重点支援分野
1. **環境保護活動**
   - オーバーツーリズム対策支援
   - 自然環境保全プロジェクト
   - ゴミ削減・リサイクル推進活動
   - カーボンオフセットプログラム

2. **文化財保護・伝統継承**
   - 歴史的建造物の修復支援
   - 伝統工芸・芸能の後継者育成
   - 地域文化のデジタルアーカイブ化
   - 消滅危機言語の保存活動

3. **地域コミュニティ支援**
   - 観光公害に悩む住民への支援
   - 地元商店街の活性化プロジェクト
   - 観光教育プログラムの実施
   - 災害復興支援

4. **持続可能な観光インフラ**
   - エコツーリズム推進
   - バリアフリー観光施設の整備
   - 地産地消レストランの支援
   - 公共交通機関の利用促進

#### 🤝 パートナーシップ構築
- **地方自治体連携**: 観光課・環境課との協働プロジェクト
- **NPO/NGO協力**: 環境保護団体・文化保存団体との連携
- **地元企業協賛**: CSR活動としての共同支援
- **観光協会提携**: 課題の早期発見・解決策の共同開発

#### 📱 アプリ内機能拡張
- **社会貢献ダッシュボード**: 寄付実績・インパクトの可視化
- **支援先投票システム**: ユーザー参加型の寄付先選定
- **ボランティアマッチング**: 現地活動への参加機会提供
- **エコポイント制度**: 環境配慮行動へのインセンティブ

#### 🎯 成果目標（Phase 8完了時）
- 月間寄付額：10万円以上
- 支援プロジェクト：5件以上
- パートナー団体：10団体以上
- ユーザー認知度：利用者の80%が社会貢献活動を認知

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
aws s3 cp frontend/index.html s3://ai-tourism-poc-frontend-dev/ --profile ai-tourism-poc
aws s3 cp frontend/css/styles.css s3://ai-tourism-poc-frontend-dev/css/ --profile ai-tourism-poc
aws s3 cp frontend/js/auth.js s3://ai-tourism-poc-frontend-dev/js/ --profile ai-tourism-poc
aws s3 cp frontend/js/main.js s3://ai-tourism-poc-frontend-dev/js/ --profile ai-tourism-poc
aws cloudfront create-invalidation --distribution-id E38DCQ985NYREA --paths "/*" --profile ai-tourism-poc
```

### 環境情報
- **本番URL**: https://anatri.net/index.html
- **ランディングページ**: https://anatri.net/lp.html  
- **管理ダッシュボード**: https://anatri.net/admin.html
- **CloudFront Distribution**: E38DCQ985NYREA
- **カスタムドメイン**: anatri.net（CloudFrontエイリアス設定済み）
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
### ✅ 完了済み（Phase 6.5-6.8）
- Stripe決済統合
- プレミアムプラン（¥980・¥1,980）
- 使用制限システム（無料5回/月）
- 地域設定機能（解析精度向上）

### 🚧 現在実装中（Phase 6.9.9）
- 管理ダッシュボード拡張
- ユーザー行動分析
- 収益・KPI監視

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
- **現在状況**: Phase 7.5完了・Phase 8.0計画中

---
*🏔️ AI観光ガイド「観光アナライザー」- 観光地の課題解決に貢献するサービス*  
*Updated: 2025-09-02 - Phase 7.5 AI解析機能強化・観光情報充実化完了*