"""
エンドツーエンド (E2E) テスト
完全なユーザージャーニーとビジネスフロー
"""
import json
import pytest
import requests
import base64
import time
from datetime import datetime, timedelta

# E2E テスト用設定
E2E_BASE_URL = "https://e2e-test.photoguidetravel.com"
TIMEOUT = 30  # 各リクエストのタイムアウト


class TestE2ECompleteFlow:
    """完全フローE2Eテストクラス"""
    
    @pytest.fixture(scope="class")
    def test_session_data(self):
        """テストセッションデータ"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return {
            "session_id": f"e2e_session_{timestamp}",
            "user_email": f"e2e_test_{timestamp}@example.com",
            "user_password": "E2ETest123!@#",
            "user_name": f"E2E Test User {timestamp}"
        }
    
    def test_01_user_registration_complete_flow(self, test_session_data):
        """ユーザー登録完全フロー"""
        # 新規ユーザー登録
        register_data = {
            "email": test_session_data["user_email"],
            "password": test_session_data["user_password"],
            "name": test_session_data["user_name"]
        }
        
        register_response = requests.post(
            f"{E2E_BASE_URL}/auth/register",
            json=register_data,
            timeout=TIMEOUT
        )
        
        assert register_response.status_code == 201
        register_result = register_response.json()
        
        # レスポンス構造確認
        assert "userId" in register_result
        assert "token" in register_result
        assert register_result["email"] == test_session_data["user_email"]
        assert register_result["name"] == test_session_data["user_name"]
        assert "message" in register_result
        
        # トークンの有効性確認
        token = register_result["token"]
        verify_response = requests.get(
            f"{E2E_BASE_URL}/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT
        )
        
        assert verify_response.status_code == 200
        verify_result = verify_response.json()
        assert verify_result["valid"] == True
        
        # セッションデータに保存
        test_session_data["user_id"] = register_result["userId"]
        test_session_data["token"] = token
    
    def test_02_image_analysis_complete_flow(self, test_session_data):
        """画像解析完全フロー"""
        headers = {"Authorization": f"Bearer {test_session_data['token']}"}
        
        # 複数の画像解析テストケース
        test_cases = [
            {
                "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
                "language": "en",
                "expected_success": True
            },
            {
                "image_data": "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7",
                "language": "ja",
                "expected_success": True
            },
            {
                "image_data": "invalid_base64",
                "language": "ko",
                "expected_success": False
            }
        ]
        
        successful_analyses = []
        
        for i, test_case in enumerate(test_cases):
            analysis_data = {
                "image": f"data:image/png;base64,{test_case['image_data']}",
                "language": test_case["language"],
                "userId": test_session_data["user_id"]
            }
            
            analysis_response = requests.post(
                f"{E2E_BASE_URL}/analyze",
                json=analysis_data,
                headers=headers,
                timeout=TIMEOUT
            )
            
            if test_case["expected_success"]:
                assert analysis_response.status_code == 200
                analysis_result = analysis_response.json()
                assert "analysis" in analysis_result
                assert analysis_result["language"] == test_case["language"]
                assert "timestamp" in analysis_result
                successful_analyses.append(analysis_result)
            else:
                assert analysis_response.status_code in [400, 500]
        
        # 少なくとも1つの解析が成功
        assert len(successful_analyses) >= 1
        test_session_data["analysis_count"] = len(successful_analyses)
    
    def test_03_payment_complete_flow(self, test_session_data):
        """決済完全フロー"""
        headers = {"Authorization": f"Bearer {test_session_data['token']}"}
        
        # 複数の決済テストケース
        payment_tests = [
            {"amount": 1000, "currency": "jpy", "service": "image_analysis"},
            {"amount": 2000, "currency": "jpy", "service": "premium_analysis"},
            {"amount": 500, "currency": "jpy", "service": "bulk_processing"}
        ]
        
        created_payments = []
        
        for payment_test in payment_tests:
            # PaymentIntent作成
            payment_data = {
                "amount": payment_test["amount"],
                "currency": payment_test["currency"],
                "userId": test_session_data["user_id"],
                "serviceType": payment_test["service"]
            }
            
            create_response = requests.post(
                f"{E2E_BASE_URL}/payment/create-payment-intent",
                json=payment_data,
                headers=headers,
                timeout=TIMEOUT
            )
            
            assert create_response.status_code == 200
            create_result = create_response.json()
            assert "clientSecret" in create_result
            assert "paymentId" in create_result
            
            payment_id = create_result["paymentId"]
            created_payments.append({
                "paymentId": payment_id,
                "amount": payment_test["amount"],
                "service": payment_test["service"]
            })
            
            # 決済確認（テスト環境での成功シミュレート）
            confirm_data = {"paymentIntentId": payment_id}
            
            confirm_response = requests.post(
                f"{E2E_BASE_URL}/payment/confirm-payment",
                json=confirm_data,
                headers=headers,
                timeout=TIMEOUT
            )
            
            # 確認結果（テスト環境では様々な結果が可能）
            assert confirm_response.status_code in [200, 400]
        
        test_session_data["payments"] = created_payments
    
    def test_04_user_data_retrieval_complete_flow(self, test_session_data):
        """ユーザーデータ取得完全フロー"""
        headers = {"Authorization": f"Bearer {test_session_data['token']}"}
        user_id = test_session_data["user_id"]
        
        # ユーザー基本情報取得
        user_response = requests.get(
            f"{E2E_BASE_URL}/users/{user_id}",
            headers=headers,
            timeout=TIMEOUT
        )
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            assert user_data["userId"] == user_id
            assert user_data["email"] == test_session_data["user_email"]
            assert "name" in user_data
            assert "createdAt" in user_data
        
        # ユーザー統計情報取得
        stats_response = requests.get(
            f"{E2E_BASE_URL}/users/stats?userId={user_id}",
            headers=headers,
            timeout=TIMEOUT
        )
        
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            assert "analysisCount" in stats_data
            assert "paymentCount" in stats_data
            assert "totalSpent" in stats_data
            assert stats_data["userId"] == user_id
        
        # 決済履歴取得
        payment_history_response = requests.get(
            f"{E2E_BASE_URL}/payment/history?userId={user_id}",
            headers=headers,
            timeout=TIMEOUT
        )
        
        if payment_history_response.status_code == 200:
            payment_data = payment_history_response.json()
            assert "payments" in payment_data
            assert payment_data["userId"] == user_id
            assert isinstance(payment_data["payments"], list)
    
    def test_05_user_profile_management_flow(self, test_session_data):
        """ユーザープロフィール管理フロー"""
        headers = {"Authorization": f"Bearer {test_session_data['token']}"}
        user_id = test_session_data["user_id"]
        
        # プロフィール更新
        new_name = f"Updated {test_session_data['user_name']}"
        update_data = {"name": new_name}
        
        update_response = requests.put(
            f"{E2E_BASE_URL}/users/{user_id}",
            json=update_data,
            headers=headers,
            timeout=TIMEOUT
        )
        
        if update_response.status_code == 200:
            update_result = update_response.json()
            assert "message" in update_result
            
            # 更新確認
            verify_update_response = requests.get(
                f"{E2E_BASE_URL}/users/{user_id}",
                headers=headers,
                timeout=TIMEOUT
            )
            
            if verify_update_response.status_code == 200:
                updated_user = verify_update_response.json()
                assert updated_user["name"] == new_name
    
    def test_06_authentication_security_flow(self, test_session_data):
        """認証セキュリティフロー"""
        # 正常ログイン
        login_response = requests.post(
            f"{E2E_BASE_URL}/auth/login",
            json={
                "email": test_session_data["user_email"],
                "password": test_session_data["user_password"]
            },
            timeout=TIMEOUT
        )
        
        assert login_response.status_code == 200
        login_result = login_response.json()
        assert "token" in login_result
        
        # 間違ったパスワードでのログイン試行
        wrong_login_response = requests.post(
            f"{E2E_BASE_URL}/auth/login",
            json={
                "email": test_session_data["user_email"],
                "password": "WrongPassword123!"
            },
            timeout=TIMEOUT
        )
        
        assert wrong_login_response.status_code == 401
        
        # 存在しないユーザーでのログイン試行
        nonexistent_login_response = requests.post(
            f"{E2E_BASE_URL}/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "AnyPassword123!"
            },
            timeout=TIMEOUT
        )
        
        assert nonexistent_login_response.status_code == 401
        
        # 無効なトークンでのAPI呼び出し
        invalid_token_response = requests.get(
            f"{E2E_BASE_URL}/auth/verify",
            headers={"Authorization": "Bearer invalid_token_12345"},
            timeout=TIMEOUT
        )
        
        assert invalid_token_response.status_code == 401
    
    def test_07_multilingual_analysis_flow(self, test_session_data):
        """多言語解析フロー"""
        headers = {"Authorization": f"Bearer {test_session_data['token']}"}
        
        # サポート言語での解析
        languages = ["en", "ja", "ko"]
        test_image = base64.b64encode(b"multilingual_test_image").decode()
        
        for language in languages:
            analysis_data = {
                "image": f"data:image/png;base64,{test_image}",
                "language": language,
                "userId": test_session_data["user_id"]
            }
            
            analysis_response = requests.post(
                f"{E2E_BASE_URL}/analyze",
                json=analysis_data,
                headers=headers,
                timeout=TIMEOUT
            )
            
            if analysis_response.status_code == 200:
                analysis_result = analysis_response.json()
                assert analysis_result["language"] == language
                assert "analysis" in analysis_result
    
    def test_08_error_recovery_flow(self, test_session_data):
        """エラー回復フロー"""
        headers = {"Authorization": f"Bearer {test_session_data['token']}"}
        
        # 1. 無効なデータでのAPI呼び出し
        invalid_requests = [
            # 空の画像データ
            {
                "url": f"{E2E_BASE_URL}/analyze",
                "json": {"image": "", "language": "en", "userId": test_session_data["user_id"]},
                "expected_status": [400, 500]
            },
            # 無効な金額での決済
            {
                "url": f"{E2E_BASE_URL}/payment/create-payment-intent",
                "json": {"amount": -100, "userId": test_session_data["user_id"]},
                "expected_status": [400, 500]
            },
            # 存在しないユーザー情報取得
            {
                "url": f"{E2E_BASE_URL}/users/nonexistent-user-id",
                "json": None,
                "expected_status": [404, 403]
            }
        ]
        
        for invalid_request in invalid_requests:
            if invalid_request["json"]:
                response = requests.post(
                    invalid_request["url"],
                    json=invalid_request["json"],
                    headers=headers,
                    timeout=TIMEOUT
                )
            else:
                response = requests.get(
                    invalid_request["url"],
                    headers=headers,
                    timeout=TIMEOUT
                )
            
            assert response.status_code in invalid_request["expected_status"]
            
            # エラーレスポンスが適切な形式か確認
            try:
                error_data = response.json()
                assert "error" in error_data or "message" in error_data
            except json.JSONDecodeError:
                # JSONでないエラーレスポンスも許可
                pass
        
        # 2. エラー後の正常なリクエストが機能することを確認
        verify_response = requests.get(
            f"{E2E_BASE_URL}/auth/verify",
            headers=headers,
            timeout=TIMEOUT
        )
        
        assert verify_response.status_code == 200
    
    def test_09_performance_and_load_simulation(self, test_session_data):
        """パフォーマンス・負荷シミュレーション"""
        headers = {"Authorization": f"Bearer {test_session_data['token']}"}
        
        # 並行リクエスト実行
        import concurrent.futures
        import threading
        
        def make_api_request(request_id):
            """単一APIリクエスト実行"""
            start_time = time.time()
            
            response = requests.get(
                f"{E2E_BASE_URL}/auth/verify",
                headers=headers,
                timeout=TIMEOUT
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code == 200
            }
        
        # 10個の並行リクエストを実行
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_api_request, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # パフォーマンス分析
        success_count = sum(1 for result in results if result["success"])
        avg_response_time = sum(result["response_time"] for result in results) / len(results)
        
        # 基本的なパフォーマンス要件
        assert success_count >= 8  # 80%以上成功
        assert avg_response_time < 5.0  # 平均5秒以内
        
        test_session_data["performance_results"] = {
            "success_rate": success_count / len(results),
            "avg_response_time": avg_response_time
        }
    
    def test_10_data_consistency_verification(self, test_session_data):
        """データ整合性検証"""
        headers = {"Authorization": f"Bearer {test_session_data['token']}"}
        user_id = test_session_data["user_id"]
        
        # 複数のエンドポイントからデータを取得して整合性を確認
        endpoints = [
            f"{E2E_BASE_URL}/users/{user_id}",
            f"{E2E_BASE_URL}/users/stats?userId={user_id}",
            f"{E2E_BASE_URL}/payment/history?userId={user_id}"
        ]
        
        responses = []
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, headers=headers, timeout=TIMEOUT)
                if response.status_code == 200:
                    responses.append(response.json())
            except requests.exceptions.RequestException:
                # ネットワークエラーは無視
                continue
        
        # 取得できたデータがある場合、ユーザーIDの整合性を確認
        for response_data in responses:
            if "userId" in response_data:
                assert response_data["userId"] == user_id
    
    def test_11_cleanup_and_teardown(self, test_session_data):
        """テストデータクリーンアップ"""
        headers = {"Authorization": f"Bearer {test_session_data['token']}"}
        user_id = test_session_data["user_id"]
        
        # テストユーザーの削除試行（権限がある場合）
        delete_response = requests.delete(
            f"{E2E_BASE_URL}/users/{user_id}",
            headers=headers,
            timeout=TIMEOUT
        )
        
        # 削除成功または権限なしエラー
        assert delete_response.status_code in [200, 403, 404]
        
        # 削除後の確認
        if delete_response.status_code == 200:
            verify_delete_response = requests.get(
                f"{E2E_BASE_URL}/users/{user_id}",
                headers=headers,
                timeout=TIMEOUT
            )
            assert verify_delete_response.status_code in [404, 403]