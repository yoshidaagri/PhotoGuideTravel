#!/bin/bash

# anatri.net Domain Registration and Route 53 Setup Script
# 実行日: 2025-01-18
# 目的: anatri.net ドメイン登録とRoute 53設定

set -e

# 設定変数
DOMAIN_NAME="anatri.net"
REGION="us-east-1"
PROFILE="ai-tourism-poc"
CLOUDFRONT_DISTRIBUTION_ID="E38DCQ985NYREA"

echo "🎯 anatri.net ドメイン登録プロセス開始..."
echo "========================================"

# 1. ドメイン可用性の再確認
echo "🔍 Step 1: ドメイン可用性確認..."
AVAILABILITY=$(aws route53domains check-domain-availability \
    --domain-name $DOMAIN_NAME \
    --region $REGION \
    --profile $PROFILE \
    --query 'Availability' \
    --output text)

if [ "$AVAILABILITY" != "AVAILABLE" ]; then
    echo "❌ エラー: $DOMAIN_NAME は利用できません"
    exit 1
fi

echo "✅ $DOMAIN_NAME は利用可能です"

# 2. ドメイン登録情報の準備
echo "📝 Step 2: ドメイン登録情報の準備..."
cat > /tmp/contact-details.json <<EOF
{
    "FirstName": "Tourism",
    "LastName": "Analyzer",
    "ContactType": "PERSON",
    "OrganizationName": "AI Tourism Analyzer",
    "AddressLine1": "Private",
    "City": "Tokyo",
    "State": "Tokyo",
    "CountryCode": "JP",
    "ZipCode": "100-0001",
    "PhoneNumber": "+81.0000000000",
    "Email": "noreply@anatri.net"
}
EOF

# 3. ドメイン登録（実際の登録は手動確認後に実行）
echo "⚠️  Step 3: ドメイン登録コマンド（手動実行用）"
echo "以下のコマンドを実行してドメインを登録してください："
echo ""
echo "aws route53domains register-domain \\"
echo "    --domain-name $DOMAIN_NAME \\"
echo "    --duration-in-years 1 \\"
echo "    --admin-contact file:///tmp/contact-details.json \\"
echo "    --registrant-contact file:///tmp/contact-details.json \\"
echo "    --tech-contact file:///tmp/contact-details.json \\"
echo "    --region $REGION \\"
echo "    --profile $PROFILE"
echo ""
echo "注意: 年間費用 $12 が発生します"
echo ""

# 4. Route 53 ホストゾーン作成スクリプト
echo "📋 Step 4: Route 53 ホストゾーン作成準備..."
cat > /tmp/create-hosted-zone.sh <<'SCRIPT'
#!/bin/bash
HOSTED_ZONE_ID=$(aws route53 create-hosted-zone \
    --name anatri.net \
    --caller-reference $(date +%s) \
    --hosted-zone-config Comment="AI Tourism Analyzer Production" \
    --profile ai-tourism-poc \
    --query 'HostedZone.Id' \
    --output text)

echo "✅ ホストゾーンID: $HOSTED_ZONE_ID"
echo "このIDを保存してください"
SCRIPT

chmod +x /tmp/create-hosted-zone.sh

# 5. SSL証明書リクエストスクリプト
echo "🔒 Step 5: SSL証明書リクエスト準備..."
cat > /tmp/request-certificate.sh <<'SCRIPT'
#!/bin/bash
CERT_ARN=$(aws acm request-certificate \
    --domain-name anatri.net \
    --validation-method DNS \
    --subject-alternative-names "*.anatri.net" \
    --region us-east-1 \
    --profile ai-tourism-poc \
    --query 'CertificateArn' \
    --output text)

echo "✅ 証明書ARN: $CERT_ARN"
echo "DNS検証が必要です"
SCRIPT

chmod +x /tmp/request-certificate.sh

# 6. CloudFront更新用設定ファイル
echo "☁️ Step 6: CloudFront更新設定準備..."
cat > /tmp/cloudfront-config.json <<EOF
{
    "Aliases": {
        "Quantity": 2,
        "Items": ["anatri.net", "www.anatri.net"]
    },
    "ViewerCertificate": {
        "ACMCertificateArn": "CERTIFICATE_ARN_HERE",
        "SSLSupportMethod": "sni-only",
        "MinimumProtocolVersion": "TLSv1.2_2021"
    }
}
EOF

# 7. DNS設定スクリプト
echo "🌐 Step 7: DNS設定スクリプト準備..."
cat > /tmp/setup-dns.sh <<'SCRIPT'
#!/bin/bash
# Route 53 Aレコード作成（CloudFrontエイリアス）

HOSTED_ZONE_ID="YOUR_HOSTED_ZONE_ID"
CLOUDFRONT_DOMAIN="d22ztxm5q1c726.cloudfront.net"

# anatri.net (apex)
aws route53 change-resource-record-sets \
    --hosted-zone-id $HOSTED_ZONE_ID \
    --change-batch '{
        "Changes": [{
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "anatri.net",
                "Type": "A",
                "AliasTarget": {
                    "HostedZoneId": "Z2FDTNDATAQYW2",
                    "DNSName": "d22ztxm5q1c726.cloudfront.net",
                    "EvaluateTargetHealth": false
                }
            }
        }]
    }' \
    --profile ai-tourism-poc

# www.anatri.net
aws route53 change-resource-record-sets \
    --hosted-zone-id $HOSTED_ZONE_ID \
    --change-batch '{
        "Changes": [{
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "www.anatri.net",
                "Type": "A",
                "AliasTarget": {
                    "HostedZoneId": "Z2FDTNDATAQYW2",
                    "DNSName": "d22ztxm5q1c726.cloudfront.net",
                    "EvaluateTargetHealth": false
                }
            }
        }]
    }' \
    --profile ai-tourism-poc
SCRIPT

chmod +x /tmp/setup-dns.sh

echo ""
echo "=================================="
echo "📋 実行手順サマリー"
echo "=================================="
echo "1. ドメイン登録（上記コマンド実行）"
echo "2. /tmp/create-hosted-zone.sh 実行"
echo "3. /tmp/request-certificate.sh 実行"
echo "4. DNS検証完了待ち（ACM）"
echo "5. CloudFront設定更新"
echo "6. /tmp/setup-dns.sh 実行"
echo ""
echo "📁 作成されたスクリプト:"
echo "   - /tmp/create-hosted-zone.sh"
echo "   - /tmp/request-certificate.sh"
echo "   - /tmp/setup-dns.sh"
echo "   - /tmp/cloudfront-config.json"
echo ""
echo "💰 年間コスト: $18（ドメイン$12 + Route53 $6）"
echo ""
echo "✨ anatri.net - AI観光アナライザーの新しいホーム！"