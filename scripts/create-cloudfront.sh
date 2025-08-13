#!/bin/bash

# AWS CloudFront Distribution作成自動化スクリプト
# 使用方法: ./create-cloudfront.sh <bucket-name> <stage>

set -e

BUCKET_NAME=${1:-"ai-tourism-poc-frontend-dev"}
STAGE=${2:-"dev"}
REGION=${3:-"ap-northeast-1"}
PROFILE=${4:-"ai-tourism-poc"}

echo "🚀 CloudFront Distribution作成開始..."
echo "Bucket: $BUCKET_NAME"
echo "Stage: $STAGE"
echo "Region: $REGION"

# S3 Website エンドポイント確認
S3_WEBSITE_DOMAIN="${BUCKET_NAME}.s3-website-${REGION}.amazonaws.com"
echo "S3 Website Domain: $S3_WEBSITE_DOMAIN"

# CloudFront設定ファイル作成
CALLER_REF="ai-tourism-poc-$(date +%s)"
CONFIG_FILE="/tmp/cloudfront-${STAGE}-$(date +%s).json"

cat > $CONFIG_FILE << EOF
{
  "CallerReference": "$CALLER_REF",
  "Aliases": {
    "Quantity": 0,
    "Items": []
  },
  "DefaultRootObject": "tourism-guide.html",
  "Comment": "AI Tourism PoC Frontend Distribution ($STAGE)",
  "Enabled": true,
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "s3-origin",
        "DomainName": "$S3_WEBSITE_DOMAIN",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "http-only"
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "s3-origin",
    "ViewerProtocolPolicy": "redirect-to-https",
    "MinTTL": 0,
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {"Forward": "none"}
    },
    "TrustedSigners": {
      "Enabled": false,
      "Quantity": 0
    }
  },
  "PriceClass": "PriceClass_100"
}
EOF

echo "📄 設定ファイル作成完了: $CONFIG_FILE"

# CloudFront Distribution作成
echo "☁️ CloudFront Distribution作成中..."
RESULT=$(aws cloudfront create-distribution \
  --distribution-config file://$CONFIG_FILE \
  --profile $PROFILE \
  --output json)

DISTRIBUTION_ID=$(echo $RESULT | jq -r '.Distribution.Id')
DOMAIN_NAME=$(echo $RESULT | jq -r '.Distribution.DomainName')
STATUS=$(echo $RESULT | jq -r '.Distribution.Status')

echo "✅ CloudFront Distribution作成成功!"
echo "Distribution ID: $DISTRIBUTION_ID"
echo "Domain Name: $DOMAIN_NAME"
echo "Status: $STATUS"
echo ""
echo "🌐 HTTPS URL: https://$DOMAIN_NAME"
echo "📋 配信完了まで15-20分程度お待ちください"

# 設定ファイル削除
rm -f $CONFIG_FILE

# 結果をJSONで出力（スクリプト連携用）
echo ""
echo "=== JSON OUTPUT ==="
echo $RESULT | jq '{distributionId: .Distribution.Id, domainName: .Distribution.DomainName, status: .Distribution.Status, httpsUrl: ("https://" + .Distribution.DomainName)}'