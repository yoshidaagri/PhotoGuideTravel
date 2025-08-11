#!/bin/bash

# Cognito OAuth設定更新スクリプト
# 使用方法: ./update-cognito-oauth.sh <cloudfront-domain>

set -e

CLOUDFRONT_DOMAIN=${1}
USER_POOL_ID="ap-northeast-1_Nk2U9t00f"
CLIENT_ID="2tctru78c2epl4mbhrt8asd55e"
PROFILE="ai-tourism-poc"
REGION="ap-northeast-1"

if [ -z "$CLOUDFRONT_DOMAIN" ]; then
    echo "❌ エラー: CloudFrontドメインが指定されていません"
    echo "使用方法: $0 <cloudfront-domain>"
    echo "例: $0 d22ztxm5q1c726.cloudfront.net"
    exit 1
fi

HTTPS_URL="https://$CLOUDFRONT_DOMAIN"
CALLBACK_URL="$HTTPS_URL/"
LOGOUT_URL="$HTTPS_URL/"

echo "🚀 Cognito OAuth設定更新開始..."
echo "CloudFront Domain: $CLOUDFRONT_DOMAIN"
echo "Callback URL: $CALLBACK_URL"
echo "Logout URL: $LOGOUT_URL"

# Cognito User Pool Clientの設定更新
echo "⚙️ Cognito User Pool Client設定更新中..."

aws cognito-idp update-user-pool-client \
    --user-pool-id $USER_POOL_ID \
    --client-id $CLIENT_ID \
    --allowed-o-auth-flows "code" \
    --allowed-o-auth-flows-user-pool-client \
    --allowed-o-auth-scopes "email" "openid" "profile" \
    --callback-urls "$CALLBACK_URL" \
    --logout-urls "$LOGOUT_URL" \
    --supported-identity-providers "COGNITO" "Google" \
    --profile $PROFILE \
    --region $REGION

echo "✅ Cognito OAuth設定更新完了!"

# 設定確認
echo "📋 更新後の設定を確認中..."
aws cognito-idp describe-user-pool-client \
    --user-pool-id $USER_POOL_ID \
    --client-id $CLIENT_ID \
    --profile $PROFILE \
    --region $REGION \
    --query 'UserPoolClient.{CallbackURLs: CallbackURLs, LogoutURLs: LogoutURLs, AllowedOAuthFlows: AllowedOAuthFlows, SupportedIdentityProviders: SupportedIdentityProviders}' \
    --output table

# OAuth URL生成
COGNITO_DOMAIN="ai-tourism-poc-frontend-dev"  # 実際のCognitoドメインに置き換え
OAUTH_URL="https://$COGNITO_DOMAIN.auth.$REGION.amazoncognito.com/login?client_id=$CLIENT_ID&response_type=code&scope=email+openid+profile&redirect_uri=$CALLBACK_URL"

echo ""
echo "🌐 Google OAuth URL:"
echo "$OAUTH_URL"
echo ""
echo "📝 この情報をフロントエンドに設定してください："
echo "- Callback URL: $CALLBACK_URL"
echo "- OAuth URL: $OAUTH_URL"