# Phase 7.8.1: 有料プラン期間変更計画

## 変更概要
有料プランの期間を以下のように変更します：
- **7日間プラン** → **3日間プラン**（価格は¥980のまま）
- **20日間プラン** → **7日間プラン**（価格は¥1,980のまま）

## 変更対象ファイル一覧

### 1. メインランディングページ
- **ファイル**: `/frontend/lp.html`
- **変更箇所**:
  - HTML部分:
    - 276行目: `<h3 id="weekTitle">7日間プラン</h3>` → `<h3 id="weekTitle">3日間プラン</h3>`
    - 278行目: `<li id="weekPlan1">7日間無制限解析</li>` → `<li id="weekPlan1">3日間無制限解析</li>`
    - 282行目: `7日間プラン選択` → `3日間プラン選択`
    - 286行目: `<h3 id="monthTitle">20日間プラン</h3>` → `<h3 id="monthTitle">7日間プラン</h3>`
    - 289行目: `<li id="monthPlan1">20日間無制限解析</li>` → `<li id="monthPlan1">7日間無制限解析</li>`
    - 293行目: `20日間プラン選択` → `7日間プラン選択`
    - 328行目: FAQ内の `7日間プラン（¥980）または20日間プラン（¥1,980）` → `3日間プラン（¥980）または7日間プラン（¥1,980）`
  
  - JavaScript翻訳部分（日本語）:
    - 390行目: `weekTitle: "7日間プラン",` → `weekTitle: "3日間プラン",`
    - 391行目: `weekPlan1: "7日間無制限解析",` → `weekPlan1: "3日間無制限解析",`
    - 393行目: `weekPlanBtn: "7日間プラン選択",` → `weekPlanBtn: "3日間プラン選択",`
    - 394行目: `monthTitle: "20日間プラン",` → `monthTitle: "7日間プラン",`
    - 395行目: `monthPlan1: "20日間無制限解析",` → `monthPlan1: "7日間無制限解析",`
    - 397行目: `monthPlanBtn: "20日間プラン選択",` → `monthPlanBtn: "7日間プラン選択",`
    - 406行目: `faq4Answer: "...7日間プラン（¥980）または20日間プラン（¥1,980）..."` → `faq4Answer: "...3日間プラン（¥980）または7日間プラン（¥1,980）..."`
  
  - JavaScript翻訳部分（韓国語）:
    - 452行目: `weekTitle: "7일 플랜",` → `weekTitle: "3일 플랜",`
    - 453行目: `weekPlan1: "7일간 무제한 분석",` → `weekPlan1: "3일간 무제한 분석",`
    - 455行目: `weekPlanBtn: "7일 플랜 선택",` → `weekPlanBtn: "3일 플랜 선택",`
    - 456行目: `monthTitle: "20일 플랜",` → `monthTitle: "7일 플랜",`
    - 457行目: `monthPlan1: "20일간 무제한 분석",` → `monthPlan1: "7일간 무제한 분석",`
    - 459行目: `monthPlanBtn: "20일 플랜 선택",` → `monthPlanBtn: "7일 플랜 선택",`
  
  - JavaScript翻訳部分（中国語簡体字）:
    - 514行目: `weekTitle: "7天方案",` → `weekTitle: "3天方案",`
    - 515行目: `weekPlan1: "7天无限制分析",` → `weekPlan1: "3天无限制分析",`
    - 517行目: `weekPlanBtn: "选择7天方案",` → `weekPlanBtn: "选择3天方案",`
    - 518行目: `monthTitle: "20天方案",` → `monthTitle: "7天方案",`
    - 519行目: `monthPlan1: "20天无限制分析",` → `monthPlan1: "7天无限制分析",`
    - 521行目: `monthPlanBtn: "选择20天方案",` → `monthPlanBtn: "选择7天方案",`
  
  - JavaScript翻訳部分（中国語繁体字）:
    - 576行目: `weekTitle: "7天方案",` → `weekTitle: "3天方案",`
    - 577行目: `weekPlan1: "7天無限制分析",` → `weekPlan1: "3天無限制分析",`
    - 579行目: `weekPlanBtn: "選擇7天方案",` → `weekPlanBtn: "選擇3天方案",`
    - 580行目: `monthTitle: "20天方案",` → `monthTitle: "7天方案",`
    - 581行目: `monthPlan1: "20天無限制分析",` → `monthPlan1: "7天無限制分析",`
    - 583行目: `monthPlanBtn: "選擇20天方案",` → `monthPlanBtn: "選擇7天方案",`
  
  - JavaScript翻訳部分（英語）:
    - 638行目: `weekTitle: "7-Day Plan",` → `weekTitle: "3-Day Plan",`
    - 639行目: `weekPlan1: "Unlimited analysis for 7 days",` → `weekPlan1: "Unlimited analysis for 3 days",`
    - 641行目: `weekPlanBtn: "Select 7-Day Plan",` → `weekPlanBtn: "Select 3-Day Plan",`
    - 642行目: `monthTitle: "20-Day Plan",` → `monthTitle: "7-Day Plan",`
    - 643行目: `monthPlan1: "Unlimited analysis for 20 days",` → `monthPlan1: "Unlimited analysis for 7 days",`
    - 645行目: `monthPlanBtn: "Select 20-Day Plan",` → `monthPlanBtn: "Select 7-Day Plan",`

### 2. 日本語版ランディングページ
- **ファイル**: `/frontend/ja/index.html`
- **変更箇所**:
  - 316行目: `<h3>7日間プラン</h3>` → `<h3>3日間プラン</h3>`
  - 319行目: `<li>7日間無制限解析</li>` → `<li>3日間無制限解析</li>`
  - 323行目: `7日間プラン選択` → `3日間プラン選択`
  - 327行目: `<h3>20日間プラン</h3>` → `<h3>7日間プラン</h3>`
  - 330行目: `<li>20日間無制限解析</li>` → `<li>7日間無制限解析</li>`
  - 334行目: `20日間プラン選択` → `7日間プラン選択`
  - 369行目: FAQ内の `7日間プラン（¥980）または20日間プラン（¥1,980）` → `3日間プラン（¥980）または7日間プラン（¥1,980）`

### 3. 韓国語版ランディングページ
- **ファイル**: `/frontend/ko/index.html`
- **変更箇所**:
  - 316行目: `<h3>7일 플랜</h3>` → `<h3>3일 플랜</h3>`
  - 319行目: `<li>7일간 무제한 분석</li>` → `<li>3일간 무제한 분석</li>`
  - 323行目: `7일 플랜 선택` → `3일 플랜 선택`
  - 327行目: `<h3>20일 플랜</h3>` → `<h3>7일 플랜</h3>`
  - 330行目: `<li>20일간 무제한 분석</li>` → `<li>7일간 무제한 분석</li>`
  - 334行目: `20일 플랜 선택` → `7일 플랜 선택`

### 4. 中国語簡体字版ランディングページ
- **ファイル**: `/frontend/zh-cn/index.html`
- **変更箇所**:
  - 316行目: `<h3>7天方案</h3>` → `<h3>3天方案</h3>`
  - 319行目: `<li>7天无限制分析</li>` → `<li>3天无限制分析</li>`
  - 323行目: `选择7天方案` → `选择3天方案`
  - 327行目: `<h3>20天方案</h3>` → `<h3>7天方案</h3>`
  - 330行目: `<li>20天无限制分析</li>` → `<li>7天无限制分析</li>`
  - 334行目: `选择20天方案` → `选择7天方案`

### 5. 中国語繁体字版ランディングページ
- **ファイル**: `/frontend/zh-tw/index.html`
- **変更箇所**:
  - 322行目: `<h3>7天方案</h3>` → `<h3>3天方案</h3>`
  - 325行目: `<li>7天無限制分析</li>` → `<li>3天無限制分析</li>`
  - 329行目: `選擇7天方案` → `選擇3天方案`
  - 333行目: `<h3>20天方案</h3>` → `<h3>7天方案</h3>`
  - 336行目: `<li>20天無限制分析</li>` → `<li>7天無限制分析</li>`
  - 340行目: `選擇20天方案` → `選擇7天方案`

### 6. 英語版ランディングページ
- **ファイル**: `/frontend/en/index.html`
- **変更箇所**:
  - 317行目: `<h3>7-Day Plan</h3>` → `<h3>3-Day Plan</h3>`
  - 320行目: `<li>Unlimited analysis for 7 days</li>` → `<li>Unlimited analysis for 3 days</li>`
  - 324行目: `Select 7-Day Plan` → `Select 3-Day Plan`
  - 328行目: `<h3>20-Day Plan</h3>` → `<h3>7-Day Plan</h3>`
  - 331行目: `<li>Unlimited analysis for 20 days</li>` → `<li>Unlimited analysis for 7 days</li>`
  - 335行目: `Select 20-Day Plan` → `Select 7-Day Plan`

## 注意事項
- 価格（¥980、¥1,980）は変更しません
- 「人気プラン」の表示はそのまま3日間プランに適用されます
- 決済ページは既に変更済みとのことなので、今回の変更対象には含まれません

## 変更実施後の確認事項
1. 各言語版のページで表示が正しく変更されているか確認
2. JavaScriptの言語切り替え機能が正常に動作するか確認
3. FAQ内の記載も含めて、全ての箇所で期間が正しく変更されているか確認

## 実施時期
ユーザー様の確認後、即時実施予定