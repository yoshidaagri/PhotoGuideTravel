"""
API エンドポイント統合テスト
"""
import json
import pytest
from unittest.mock import patch, Mock
import requests
import base64

# 統合テスト用のベースURL（テスト環境）
BASE_URL = "https://test-api.photoguidetravel.com"


class TestAPIIntegration:
    """API統合テストクラス"""
    
    @pytest.fixture
    def test_user_credentials(self):
        """テスト用ユーザー認証情報"""
        return {
            "email": "integration-test@example.com",
            "password": "IntegrationTest123!",
            "name": "Integration Test User"
        }
    
    @pytest.fixture
    def authenticated_headers(self, test_user_credentials):
        """認証済みヘッダー"""
        # ユーザー登録
        register_data = test_user_credentials
        register_response = requests.post(
            f"{BASE_URL}/auth/register",
            json=register_data
        )
        
        if register_response.status_code == 201:
            token = register_response.json().get("token")
        else:
            # 既存ユーザーの場合はログイン
            login_response = requests.post(
                f"{BASE_URL}/auth/login",
                json={
                    "email": test_user_credentials["email"],
                    "password": test_user_credentials["password"]
                }
            )
            token = login_response.json().get("token")
        
        return {"Authorization": f"Bearer {token}"}
    
    def test_auth_flow_integration(self, test_user_credentials):
        """認証フロー統合テスト"""
        # 1. ユーザー登録
        register_response = requests.post(
            f"{BASE_URL}/auth/register",
            json=test_user_credentials
        )
        
        # 新規ユーザーまたは既存ユーザー
        assert register_response.status_code in [201, 409]
        
        # 2. ログイン
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": test_user_credentials["email"],
                "password": test_user_credentials["password"]
            }
        )
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "token" in login_data
        assert login_data["email"] == test_user_credentials["email"]
        
        # 3. トークン検証
        token = login_data["token"]
        verify_response = requests.get(
            f"{BASE_URL}/auth/verify",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data["valid"] == True
        assert verify_data["email"] == test_user_credentials["email"]
    
    def test_image_analysis_integration(self, authenticated_headers):
        """画像解析統合テスト"""
        # テスト画像データ（小さなPNG）
        test_image = base64.b64encode(b"fake_png_data").decode()
        
        analysis_data = {
            "image": f"data:image/png;base64,{test_image}",
            "language": "en",
            "userId": "integration-test-user"
        }
        
        response = requests.post(
            f"{BASE_URL}/analyze",
            json=analysis_data,
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        analysis_result = response.json()
        assert "analysis" in analysis_result
        assert analysis_result["language"] == "en"
        assert "timestamp" in analysis_result
    
    def test_payment_flow_integration(self, authenticated_headers):
        """決済フロー統合テスト"""
        # 1. PaymentIntent作成
        payment_data = {
            "amount": 1000,
            "currency": "jpy",
            "userId": "integration-test-user",
            "serviceType": "image_analysis"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/payment/create-payment-intent",
            json=payment_data,
            headers=authenticated_headers
        )
        
        assert create_response.status_code == 200
        create_result = create_response.json()
        assert "clientSecret" in create_result
        assert "paymentId" in create_result
        
        payment_id = create_result["paymentId"]
        
        # 2. 決済確認（テスト環境では成功をシミュレート）
        confirm_data = {
            "paymentIntentId": payment_id
        }
        
        confirm_response = requests.post(
            f"{BASE_URL}/payment/confirm-payment",
            json=confirm_data,
            headers=authenticated_headers
        )
        
        # テスト環境での結果を確認
        assert confirm_response.status_code in [200, 400]
        
        # 3. 決済履歴確認
        history_response = requests.get(
            f"{BASE_URL}/payment/history?userId=integration-test-user",
            headers=authenticated_headers
        )
        
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert "payments" in history_data
        assert isinstance(history_data["payments"], list)
    
    def test_user_management_integration(self, authenticated_headers):
        """ユーザー管理統合テスト"""
        user_id = "integration-test-user"
        
        # 1. ユーザー情報取得
        get_response = requests.get(
            f"{BASE_URL}/users/{user_id}",
            headers=authenticated_headers
        )
        
        if get_response.status_code == 200:
            user_data = get_response.json()
            assert "userId" in user_data
            assert "email" in user_data
            
            # 2. ユーザー情報更新
            update_data = {
                "name": "Updated Integration Test User"
            }
            
            update_response = requests.put(
                f"{BASE_URL}/users/{user_id}",
                json=update_data,
                headers=authenticated_headers
            )
            
            # 成功または権限エラー
            assert update_response.status_code in [200, 403]
            
            # 3. ユーザー統計情報取得
            stats_response = requests.get(
                f"{BASE_URL}/users/stats?userId={user_id}",
                headers=authenticated_headers
            )
            
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                assert "analysisCount" in stats_data
                assert "paymentCount" in stats_data
                assert "totalSpent" in stats_data
    
    def test_cors_headers_integration(self):
        """CORS ヘッダー統合テスト"""
        # OPTIONSリクエスト
        options_response = requests.options(f"{BASE_URL}/auth/login")
        
        assert options_response.status_code == 200
        headers = options_response.headers
        assert "Access-Control-Allow-Origin" in headers
        assert "Access-Control-Allow-Methods" in headers
        assert "Access-Control-Allow-Headers" in headers
    
    def test_error_handling_integration(self):
        """エラーハンドリング統合テスト"""
        # 1. 存在しないエンドポイント
        not_found_response = requests.get(f"{BASE_URL}/nonexistent")
        assert not_found_response.status_code == 404
        
        # 2. 不正なJSON
        invalid_json_response = requests.post(
            f"{BASE_URL}/auth/login",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert invalid_json_response.status_code in [400, 500]
        
        # 3. 認証なしでprotectedエンドポイント
        unauthorized_response = requests.get(f"{BASE_URL}/users/test-user")
        assert unauthorized_response.status_code in [401, 403]
    
    def test_complete_user_journey_integration(self, test_user_credentials):
        """完全なユーザージャーニー統合テスト"""
        # 1. ユーザー登録/ログイン
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": test_user_credentials["email"],
                "password": test_user_credentials["password"]
            }
        )
        
        if login_response.status_code != 200:
            # 新規登録
            register_response = requests.post(
                f"{BASE_URL}/auth/register",
                json=test_user_credentials
            )
            assert register_response.status_code == 201
            token = register_response.json()["token"]
        else:
            token = login_response.json()["token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. 画像解析実行
        test_image = base64.b64encode(b"journey_test_image").decode()
        analysis_response = requests.post(
            f"{BASE_URL}/analyze",
            json={
                "image": f"data:image/jpeg;base64,{test_image}",
                "language": "ja",
                "userId": "journey-test-user"
            },
            headers=headers
        )
        
        assert analysis_response.status_code == 200
        
        # 3. 決済処理
        payment_response = requests.post(
            f"{BASE_URL}/payment/create-payment-intent",
            json={
                "amount": 500,
                "currency": "jpy",
                "userId": "journey-test-user",
                "serviceType": "image_analysis"
            },
            headers=headers
        )
        
        assert payment_response.status_code == 200
        
        # 4. ユーザー統計確認
        stats_response = requests.get(
            f"{BASE_URL}/users/stats?userId=journey-test-user",
            headers=headers
        )
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            assert stats["analysisCount"] >= 0
            assert stats["totalSpent"] >= 0
    
    def test_rate_limiting_integration(self, authenticated_headers):
        """レート制限統合テスト"""
        # 短時間で多数のリクエストを送信
        responses = []
        
        for i in range(10):
            response = requests.get(
                f"{BASE_URL}/auth/verify",
                headers=authenticated_headers
            )
            responses.append(response.status_code)
        
        # 大部分のリクエストは成功するはず（レート制限があれば429が含まれる）
        success_count = sum(1 for status in responses if status == 200)
        assert success_count >= 5  # 半分以上は成功
    
    def test_data_persistence_integration(self, authenticated_headers):
        """データ永続化統合テスト"""
        # 1. データ作成
        test_image = base64.b64encode(b"persistence_test").decode()
        analysis_response = requests.post(
            f"{BASE_URL}/analyze",
            json={
                "image": f"data:image/png;base64,{test_image}",
                "language": "en",
                "userId": "persistence-test-user"
            },
            headers=authenticated_headers
        )
        
        assert analysis_response.status_code == 200
        
        # 2. 少し待ってからデータを確認
        import time
        time.sleep(1)
        
        stats_response = requests.get(
            f"{BASE_URL}/users/stats?userId=persistence-test-user",
            headers=authenticated_headers
        )
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            # 分析回数が増加していることを確認
            assert stats["analysisCount"] >= 1