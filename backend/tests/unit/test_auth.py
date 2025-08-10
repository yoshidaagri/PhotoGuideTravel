"""
認証Lambda関数の単体テスト
"""
import json
import pytest
from unittest.mock import patch, Mock
import jwt
import hashlib
from datetime import datetime, timedelta

# テスト対象をインポート
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../functions/auth'))
from handler import (
    main, handle_register, handle_login, handle_verify_token,
    create_user, authenticate_user, generate_jwt_token, verify_jwt_token
)


class TestAuthHandler:
    """認証ハンドラーテストクラス"""
    
    def test_register_success(self, sample_context, mock_environment, create_test_tables):
        """ユーザー登録成功テスト"""
        event = {
            "httpMethod": "POST",
            "path": "/auth/register",
            "body": json.dumps({
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "name": "New User"
            })
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["email"] == "newuser@example.com"
        assert body["name"] == "New User"
        assert "userId" in body
        assert "token" in body
        assert body["message"] == "User registered successfully"

    def test_register_missing_fields(self, sample_context, mock_environment):
        """必須フィールド未入力テスト"""
        event = {
            "httpMethod": "POST",
            "path": "/auth/register",
            "body": json.dumps({
                "email": "test@example.com"
                # password missing
            })
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "Email and password are required" in body["error"]

    def test_register_duplicate_user(self, sample_context, mock_environment, create_test_tables, sample_user_data):
        """重複ユーザー登録テスト"""
        # 既存ユーザーを作成
        tables = create_test_tables
        tables['users'].put_item(Item=sample_user_data)
        
        event = {
            "httpMethod": "POST",
            "path": "/auth/register",
            "body": json.dumps({
                "email": "test@example.com",  # 既存ユーザーのメール
                "password": "NewPassword123!",
                "name": "Duplicate User"
            })
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 409
        body = json.loads(response["body"])
        assert "User already exists" in body["error"]

    def test_login_success(self, sample_context, mock_environment, create_test_tables):
        """ログイン成功テスト"""
        # ユーザーを事前に作成
        user_data = {
            "userId": "test-login-user",
            "email": "logintest@example.com",
            "passwordHash": hashlib.sha256("TestPassword123!".encode()).hexdigest(),
            "name": "Login Test User",
            "createdAt": datetime.now().isoformat(),
            "lastLogin": datetime.now().isoformat()
        }
        create_test_tables['users'].put_item(Item=user_data)
        
        event = {
            "httpMethod": "POST",
            "path": "/auth/login",
            "body": json.dumps({
                "email": "logintest@example.com",
                "password": "TestPassword123!"
            })
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["email"] == "logintest@example.com"
        assert body["userId"] == "test-login-user"
        assert "token" in body
        assert body["message"] == "Login successful"

    def test_login_invalid_credentials(self, sample_context, mock_environment, create_test_tables):
        """無効な認証情報テスト"""
        event = {
            "httpMethod": "POST",
            "path": "/auth/login",
            "body": json.dumps({
                "email": "nonexistent@example.com",
                "password": "WrongPassword"
            })
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert "Invalid credentials" in body["error"]

    def test_login_wrong_password(self, sample_context, mock_environment, create_test_tables):
        """パスワード間違いテスト"""
        # ユーザーを事前に作成
        user_data = {
            "userId": "test-wrong-pass-user",
            "email": "wrongpass@example.com",
            "passwordHash": hashlib.sha256("CorrectPassword123!".encode()).hexdigest(),
            "name": "Wrong Pass User",
            "createdAt": datetime.now().isoformat(),
            "lastLogin": datetime.now().isoformat()
        }
        create_test_tables['users'].put_item(Item=user_data)
        
        event = {
            "httpMethod": "POST",
            "path": "/auth/login",
            "body": json.dumps({
                "email": "wrongpass@example.com",
                "password": "WrongPassword123!"
            })
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert "Invalid credentials" in body["error"]

    def test_verify_token_success(self, sample_context, mock_environment):
        """トークン検証成功テスト"""
        # 有効なトークンを生成
        token = generate_jwt_token("test-user-verify", "verify@example.com")
        
        event = {
            "httpMethod": "GET",
            "path": "/auth/verify",
            "headers": {
                "Authorization": f"Bearer {token}"
            }
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["valid"] == True
        assert body["userId"] == "test-user-verify"
        assert body["email"] == "verify@example.com"

    def test_verify_token_missing_header(self, sample_context, mock_environment):
        """Authorizationヘッダー未提供テスト"""
        event = {
            "httpMethod": "GET",
            "path": "/auth/verify",
            "headers": {}
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert "Invalid authorization header" in body["error"]

    def test_verify_token_invalid_format(self, sample_context, mock_environment):
        """無効なAuthorizationヘッダー形式テスト"""
        event = {
            "httpMethod": "GET",
            "path": "/auth/verify",
            "headers": {
                "Authorization": "InvalidFormat token123"
            }
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert "Invalid authorization header" in body["error"]

    def test_verify_token_expired(self, sample_context, mock_environment):
        """期限切れトークンテスト"""
        # 期限切れトークンを手動生成
        payload = {
            'userId': 'test-user-expired',
            'email': 'expired@example.com',
            'exp': datetime.utcnow() - timedelta(hours=1),  # 1時間前に期限切れ
            'iat': datetime.utcnow() - timedelta(hours=2)
        }
        
        expired_token = jwt.encode(payload, 'test-jwt-secret', algorithm='HS256')
        
        event = {
            "httpMethod": "GET",
            "path": "/auth/verify",
            "headers": {
                "Authorization": f"Bearer {expired_token}"
            }
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert "Invalid or expired token" in body["error"]

    def test_options_request(self, sample_context, mock_environment):
        """OPTIONSリクエスト（CORS）テスト"""
        event = {
            "httpMethod": "OPTIONS"
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 200
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        assert "Access-Control-Allow-Methods" in response["headers"]

    def test_unknown_endpoint(self, sample_context, mock_environment):
        """存在しないエンドポイントテスト"""
        event = {
            "httpMethod": "GET",
            "path": "/auth/unknown"
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert "Endpoint not found" in body["error"]

    def test_jwt_token_generation_and_verification(self, mock_environment):
        """JWTトークン生成・検証テスト"""
        user_id = "test-jwt-user"
        email = "jwt@example.com"
        
        # トークン生成
        token = generate_jwt_token(user_id, email)
        assert isinstance(token, str)
        assert len(token) > 0
        
        # トークン検証
        payload = verify_jwt_token(token)
        assert payload is not None
        assert payload["userId"] == user_id
        assert payload["email"] == email
        assert "exp" in payload
        assert "iat" in payload

    def test_password_hashing(self, mock_environment, create_test_tables):
        """パスワードハッシュ化テスト"""
        email = "hashtest@example.com"
        password = "TestHashPassword123!"
        name = "Hash Test User"
        
        # ユーザー作成（パスワードがハッシュ化される）
        user_id = create_user(email, password, name)
        
        # ハッシュ化されたパスワードで認証成功
        user = authenticate_user(email, password)
        assert user is not None
        assert user["userId"] == user_id
        
        # 間違ったパスワードで認証失敗
        wrong_user = authenticate_user(email, "WrongPassword")
        assert wrong_user is None

    def test_user_creation_unique_id(self, mock_environment, create_test_tables):
        """ユーザーID一意性テスト"""
        email1 = "unique1@example.com"
        email2 = "unique2@example.com"
        password = "SamePassword123!"
        
        user_id1 = create_user(email1, password, "User 1")
        user_id2 = create_user(email2, password, "User 2")
        
        # 異なるユーザーIDが生成される
        assert user_id1 != user_id2
        assert len(user_id1) == 16  # SHA256の最初の16文字
        assert len(user_id2) == 16

    def test_last_login_update(self, mock_environment, create_test_tables):
        """最終ログイン時刻更新テスト"""
        # ユーザーを作成
        email = "lastlogin@example.com"
        password = "LastLoginTest123!"
        user_id = create_user(email, password, "Last Login User")
        
        # 最初のログイン時刻を取得
        user1 = authenticate_user(email, password)
        first_login = user1["lastLogin"]
        
        import time
        time.sleep(0.1)  # わずかに時間を空ける
        
        # 再ログイン
        user2 = authenticate_user(email, password)
        second_login = user2["lastLogin"]
        
        # ログイン時刻が更新される
        assert second_login >= first_login

    def test_invalid_json_handling(self, sample_context, mock_environment):
        """無効なJSON処理テスト"""
        event = {
            "httpMethod": "POST",
            "path": "/auth/register",
            "body": "invalid json string"
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body