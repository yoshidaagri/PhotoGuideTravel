"""
ユーザー管理Lambda関数の単体テスト
"""
import json
import pytest
from unittest.mock import patch, Mock

# テスト対象をインポート
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../functions/user-management'))
from handler import main, handle_get_user, handle_update_user, handle_delete_user, handle_get_user_stats


class TestUserManagementHandler:
    """ユーザー管理ハンドラーテストクラス"""
    
    def test_get_user_success(self, sample_context, mock_environment, create_test_tables, sample_user_data):
        """ユーザー情報取得成功テスト"""
        # テストユーザー作成
        tables = create_test_tables
        enhanced_user_data = sample_user_data.copy()
        enhanced_user_data.update({
            'analysisCount': 5,
            'totalSpent': 2500.0
        })
        tables['users'].put_item(Item=enhanced_user_data)
        
        event = {
            "httpMethod": "GET",
            "pathParameters": {"proxy": "test-user-001"},
            "path": "/users/test-user-001"
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["userId"] == "test-user-001"
        assert body["email"] == "test@example.com"
        assert body["name"] == "Test User"
        assert body["analysisCount"] == 5
        assert body["totalSpent"] == 2500.0
        assert "passwordHash" not in body  # パスワードハッシュは除外

    def test_get_user_not_found(self, sample_context, mock_environment, create_test_tables):
        """存在しないユーザーテスト"""
        event = {
            "httpMethod": "GET",
            "pathParameters": {"proxy": "nonexistent-user"},
            "path": "/users/nonexistent-user"
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert "User not found" in body["error"]

    def test_get_user_missing_id(self, sample_context, mock_environment):
        """ユーザーID未提供テスト"""
        event = {
            "httpMethod": "GET",
            "pathParameters": None,
            "path": "/users/"
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "User ID is required" in body["error"]

    def test_update_user_success(self, sample_context, mock_environment, create_test_tables, sample_user_data):
        """ユーザー情報更新成功テスト"""
        # テストユーザー作成
        tables = create_test_tables
        tables['users'].put_item(Item=sample_user_data)
        
        event = {
            "httpMethod": "PUT",
            "pathParameters": {"proxy": "test-user-001"},
            "path": "/users/test-user-001",
            "body": json.dumps({
                "name": "Updated Test User"
            })
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["userId"] == "test-user-001"
        assert "User updated successfully" in body["message"]

    def test_update_user_missing_name(self, sample_context, mock_environment, create_test_tables, sample_user_data):
        """名前未入力更新テスト"""
        tables = create_test_tables
        tables['users'].put_item(Item=sample_user_data)
        
        event = {
            "httpMethod": "PUT",
            "pathParameters": {"proxy": "test-user-001"},
            "path": "/users/test-user-001",
            "body": json.dumps({})
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "Name is required" in body["error"]

    def test_update_user_not_found(self, sample_context, mock_environment, create_test_tables):
        """存在しないユーザー更新テスト"""
        event = {
            "httpMethod": "PUT",
            "pathParameters": {"proxy": "nonexistent-user"},
            "path": "/users/nonexistent-user",
            "body": json.dumps({
                "name": "New Name"
            })
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert "User not found" in body["error"]

    def test_delete_user_success(self, sample_context, mock_environment, create_test_tables, sample_user_data):
        """ユーザー削除成功テスト"""
        # テストデータ作成
        tables = create_test_tables
        tables['users'].put_item(Item=sample_user_data)
        
        # 関連データも作成
        tables['analysis'].put_item(Item={
            'userId': 'test-user-001',
            'timestamp': '2025-01-09T10:00:00.000Z',
            'analysis': 'Test analysis',
            'language': 'en'
        })
        
        tables['payment'].put_item(Item={
            'userId': 'test-user-001',
            'paymentId': 'pi_test_delete',
            'amount': 1000,
            'status': 'succeeded'
        })
        
        event = {
            "httpMethod": "DELETE",
            "pathParameters": {"proxy": "test-user-001"},
            "path": "/users/test-user-001"
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["userId"] == "test-user-001"
        assert "User deleted successfully" in body["message"]

    def test_delete_user_not_found(self, sample_context, mock_environment, create_test_tables):
        """存在しないユーザー削除テスト"""
        event = {
            "httpMethod": "DELETE",
            "pathParameters": {"proxy": "nonexistent-user"},
            "path": "/users/nonexistent-user"
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert "User not found" in body["error"]

    def test_get_user_stats_success(self, sample_context, mock_environment, create_test_tables):
        """ユーザー統計情報取得成功テスト"""
        tables = create_test_tables
        
        # 分析履歴データ作成
        analysis_data = [
            {
                'userId': 'test-user-stats',
                'timestamp': '2025-01-09T10:00:00.000Z',
                'analysis': 'Analysis 1',
                'success': True
            },
            {
                'userId': 'test-user-stats',
                'timestamp': '2025-01-09T11:00:00.000Z',
                'analysis': 'Analysis 2',
                'success': True
            }
        ]
        
        for item in analysis_data:
            tables['analysis'].put_item(Item=item)
        
        # 決済履歴データ作成
        payment_data = [
            {
                'userId': 'test-user-stats',
                'paymentId': 'pi_stats_001',
                'amount': 1000,
                'status': 'succeeded'
            },
            {
                'userId': 'test-user-stats',
                'paymentId': 'pi_stats_002',
                'amount': 1500,
                'status': 'succeeded'
            }
        ]
        
        for item in payment_data:
            tables['payment'].put_item(Item=item)
        
        event = {
            "httpMethod": "GET",
            "path": "/users/stats",
            "queryStringParameters": {
                "userId": "test-user-stats"
            }
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["userId"] == "test-user-stats"
        assert body["analysisCount"] == 2
        assert body["paymentCount"] == 2
        assert body["totalSpent"] == 2500.0

    def test_get_user_stats_missing_user_id(self, sample_context, mock_environment):
        """ユーザー統計情報取得ユーザーID未提供テスト"""
        event = {
            "httpMethod": "GET",
            "path": "/users/stats",
            "queryStringParameters": {}
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "userId parameter is required" in body["error"]

    def test_get_user_stats_no_data(self, sample_context, mock_environment, create_test_tables):
        """データなしユーザー統計テスト"""
        event = {
            "httpMethod": "GET",
            "path": "/users/stats",
            "queryStringParameters": {
                "userId": "user-with-no-data"
            }
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["userId"] == "user-with-no-data"
        assert body["analysisCount"] == 0
        assert body["paymentCount"] == 0
        assert body["totalSpent"] == 0

    def test_options_request(self, sample_context, mock_environment):
        """OPTIONSリクエスト（CORS）テスト"""
        event = {
            "httpMethod": "OPTIONS"
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 200
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"

    def test_unknown_endpoint(self, sample_context, mock_environment):
        """存在しないエンドポイントテスト"""
        event = {
            "httpMethod": "GET",
            "path": "/users/unknown-endpoint"
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert "Endpoint not found" in body["error"]

    def test_user_data_completeness(self, sample_context, mock_environment, create_test_tables):
        """ユーザーデータ完全性テスト"""
        # 最小限のデータでユーザー作成
        minimal_user = {
            "userId": "minimal-user",
            "email": "minimal@example.com",
            "passwordHash": "hash123"
        }
        
        tables = create_test_tables
        tables['users'].put_item(Item=minimal_user)
        
        event = {
            "httpMethod": "GET",
            "pathParameters": {"proxy": "minimal-user"},
            "path": "/users/minimal-user"
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["userId"] == "minimal-user"
        assert body["email"] == "minimal@example.com"
        assert body["name"] == ""  # デフォルト値
        assert body["analysisCount"] == 0  # デフォルト値
        assert body["totalSpent"] == 0.0  # デフォルト値

    def test_cascading_delete_verification(self, sample_context, mock_environment, create_test_tables, sample_user_data):
        """関連データ削除確認テスト"""
        tables = create_test_tables
        user_id = "test-cascade-user"
        
        # ユーザーデータ作成
        cascade_user = sample_user_data.copy()
        cascade_user["userId"] = user_id
        tables['users'].put_item(Item=cascade_user)
        
        # 関連データ作成
        analysis_items = [
            {
                'userId': user_id,
                'timestamp': '2025-01-09T10:00:00.000Z',
                'analysis': 'Analysis 1'
            },
            {
                'userId': user_id,
                'timestamp': '2025-01-09T11:00:00.000Z',
                'analysis': 'Analysis 2'
            }
        ]
        
        payment_items = [
            {
                'userId': user_id,
                'paymentId': 'pi_cascade_001',
                'amount': 1000
            },
            {
                'userId': user_id,
                'paymentId': 'pi_cascade_002',
                'amount': 1500
            }
        ]
        
        for item in analysis_items:
            tables['analysis'].put_item(Item=item)
        
        for item in payment_items:
            tables['payment'].put_item(Item=item)
        
        # 削除実行
        event = {
            "httpMethod": "DELETE",
            "pathParameters": {"proxy": user_id},
            "path": f"/users/{user_id}"
        }
        
        response = main(event, sample_context)
        assert response["statusCode"] == 200
        
        # データが削除されていることを確認
        user_response = tables['users'].get_item(Key={'userId': user_id})
        assert 'Item' not in user_response

    def test_concurrent_user_operations(self, sample_context, mock_environment, create_test_tables, sample_user_data):
        """並行ユーザー操作テスト"""
        import threading
        
        tables = create_test_tables
        user_ids = ['concurrent-user-1', 'concurrent-user-2', 'concurrent-user-3']
        results = []
        
        # 複数ユーザーを並行作成
        for user_id in user_ids:
            user_data = sample_user_data.copy()
            user_data['userId'] = user_id
            user_data['email'] = f"{user_id}@example.com"
            tables['users'].put_item(Item=user_data)
        
        def get_user(user_id):
            event = {
                "httpMethod": "GET",
                "pathParameters": {"proxy": user_id},
                "path": f"/users/{user_id}"
            }
            response = main(event, sample_context)
            results.append(response)
        
        threads = []
        for user_id in user_ids:
            thread = threading.Thread(target=get_user, args=(user_id,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # すべてのリクエストが成功
        assert len(results) == 3
        for result in results:
            assert result["statusCode"] == 200

    def test_invalid_json_handling(self, sample_context, mock_environment):
        """無効なJSON処理テスト"""
        event = {
            "httpMethod": "PUT",
            "pathParameters": {"proxy": "test-user"},
            "path": "/users/test-user",
            "body": "invalid json"
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body