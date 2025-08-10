"""
決済Lambda関数の単体テスト
"""
import json
import pytest
from unittest.mock import patch, Mock

# テスト対象をインポート
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../functions/payment'))
from handler import main, handle_create_payment_intent, handle_confirm_payment, handle_payment_history


class TestPaymentHandler:
    """決済ハンドラーテストクラス"""
    
    def test_create_payment_intent_success(self, sample_context, mock_environment, create_test_tables, mock_stripe_api):
        """PaymentIntent作成成功テスト"""
        event = {
            "httpMethod": "POST",
            "path": "/payment/create-payment-intent",
            "body": json.dumps({
                "amount": 1000,  # 1000円
                "currency": "jpy",
                "userId": "test-user-001",
                "serviceType": "image_analysis"
            })
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "clientSecret" in body
        assert "paymentId" in body
        assert body["paymentId"] == "pi_test_123"

    def test_create_payment_intent_missing_fields(self, sample_context, mock_environment):
        """必須フィールド未入力テスト"""
        event = {
            "httpMethod": "POST",
            "path": "/payment/create-payment-intent",
            "body": json.dumps({
                "amount": 1000
                # userId missing
            })
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "Amount and userId are required" in body["error"]

    def test_create_payment_intent_stripe_error(self, sample_context, mock_environment, create_test_tables):
        """Stripe APIエラーテスト"""
        with patch('stripe.PaymentIntent.create') as mock_create:
            import stripe
            mock_create.side_effect = stripe.error.StripeError("Stripe API Error")
            
            event = {
                "httpMethod": "POST",
                "path": "/payment/create-payment-intent",
                "body": json.dumps({
                    "amount": 1000,
                    "userId": "test-user-001"
                })
            }
            
            response = main(event, sample_context)
            
            assert response["statusCode"] == 400
            body = json.loads(response["body"])
            assert "Stripe API Error" in body["error"]

    def test_confirm_payment_success(self, sample_context, mock_environment, create_test_tables, mock_stripe_api):
        """決済確認成功テスト"""
        # 事前に決済記録を作成
        tables = create_test_tables
        tables['payment'].put_item(Item={
            'userId': 'test-user-001',
            'paymentId': 'pi_test_123',
            'amount': 1000,
            'currency': 'jpy',
            'status': 'created',
            'serviceType': 'image_analysis',
            'createdAt': '2025-01-09T00:00:00.000Z',
            'updatedAt': '2025-01-09T00:00:00.000Z'
        })
        
        event = {
            "httpMethod": "POST",
            "path": "/payment/confirm-payment",
            "body": json.dumps({
                "paymentIntentId": "pi_test_123"
            })
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["status"] == "succeeded"
        assert "Payment confirmed successfully" in body["message"]

    def test_confirm_payment_missing_id(self, sample_context, mock_environment):
        """PaymentIntent ID未提供テスト"""
        event = {
            "httpMethod": "POST",
            "path": "/payment/confirm-payment",
            "body": json.dumps({})
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "PaymentIntent ID is required" in body["error"]

    def test_confirm_payment_not_succeeded(self, sample_context, mock_environment, create_test_tables):
        """未完了決済確認テスト"""
        with patch('stripe.PaymentIntent.retrieve') as mock_retrieve:
            mock_payment_intent = Mock()
            mock_payment_intent.status = "requires_payment_method"
            mock_payment_intent.metadata = {"userId": "test-user-001"}
            mock_retrieve.return_value = mock_payment_intent
            
            event = {
                "httpMethod": "POST",
                "path": "/payment/confirm-payment",
                "body": json.dumps({
                    "paymentIntentId": "pi_test_123"
                })
            }
            
            response = main(event, sample_context)
            
            assert response["statusCode"] == 400
            body = json.loads(response["body"])
            assert body["status"] == "requires_payment_method"
            assert "Payment not completed" in body["message"]

    def test_payment_history_success(self, sample_context, mock_environment, create_test_tables):
        """決済履歴取得成功テスト"""
        # テストデータ作成
        tables = create_test_tables
        test_payments = [
            {
                'userId': 'test-user-history',
                'paymentId': 'pi_test_001',
                'amount': 1000,
                'currency': 'jpy',
                'status': 'succeeded',
                'serviceType': 'image_analysis',
                'createdAt': '2025-01-09T10:00:00.000Z',
                'updatedAt': '2025-01-09T10:01:00.000Z'
            },
            {
                'userId': 'test-user-history',
                'paymentId': 'pi_test_002',
                'amount': 2000,
                'currency': 'jpy',
                'status': 'succeeded',
                'serviceType': 'premium_analysis',
                'createdAt': '2025-01-09T11:00:00.000Z',
                'updatedAt': '2025-01-09T11:01:00.000Z'
            }
        ]
        
        for payment in test_payments:
            tables['payment'].put_item(Item=payment)
        
        event = {
            "httpMethod": "GET",
            "path": "/payment/history",
            "queryStringParameters": {
                "userId": "test-user-history"
            }
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["userId"] == "test-user-history"
        assert len(body["payments"]) == 2

    def test_payment_history_missing_user_id(self, sample_context, mock_environment):
        """ユーザーID未提供テスト"""
        event = {
            "httpMethod": "GET",
            "path": "/payment/history",
            "queryStringParameters": {}
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "userId is required" in body["error"]

    def test_payment_history_no_payments(self, sample_context, mock_environment, create_test_tables):
        """決済履歴なしテスト"""
        event = {
            "httpMethod": "GET",
            "path": "/payment/history",
            "queryStringParameters": {
                "userId": "user-with-no-payments"
            }
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["userId"] == "user-with-no-payments"
        assert len(body["payments"]) == 0

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
            "path": "/payment/unknown"
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert "Endpoint not found" in body["error"]

    def test_currency_support(self, sample_context, mock_environment, create_test_tables, mock_stripe_api):
        """通貨サポートテスト"""
        currencies = ["jpy", "usd", "eur"]
        
        for currency in currencies:
            event = {
                "httpMethod": "POST",
                "path": "/payment/create-payment-intent",
                "body": json.dumps({
                    "amount": 1000,
                    "currency": currency,
                    "userId": "test-user-currency",
                    "serviceType": "image_analysis"
                })
            }
            
            response = main(event, sample_context)
            assert response["statusCode"] == 200

    def test_service_type_variations(self, sample_context, mock_environment, create_test_tables, mock_stripe_api):
        """サービスタイプバリエーションテスト"""
        service_types = ["image_analysis", "premium_analysis", "bulk_processing"]
        
        for service_type in service_types:
            event = {
                "httpMethod": "POST",
                "path": "/payment/create-payment-intent",
                "body": json.dumps({
                    "amount": 1000,
                    "currency": "jpy",
                    "userId": "test-user-service",
                    "serviceType": service_type
                })
            }
            
            response = main(event, sample_context)
            assert response["statusCode"] == 200

    def test_payment_record_saving(self, sample_context, mock_environment, create_test_tables, mock_stripe_api):
        """決済記録保存テスト"""
        event = {
            "httpMethod": "POST",
            "path": "/payment/create-payment-intent",
            "body": json.dumps({
                "amount": 1500,
                "currency": "jpy",
                "userId": "test-user-record",
                "serviceType": "premium_analysis"
            })
        }
        
        response = main(event, sample_context)
        assert response["statusCode"] == 200
        
        # データベースに記録が保存されていることを確認
        tables = create_test_tables
        payment_response = tables['payment'].query(
            KeyConditionExpression='userId = :userId',
            ExpressionAttributeValues={':userId': 'test-user-record'}
        )
        
        assert len(payment_response['Items']) == 1
        payment = payment_response['Items'][0]
        assert payment['amount'] == 1500
        assert payment['currency'] == 'jpy'
        assert payment['serviceType'] == 'premium_analysis'
        assert payment['status'] == 'created'

    def test_concurrent_payment_creation(self, sample_context, mock_environment, create_test_tables, mock_stripe_api):
        """並行決済作成テスト"""
        import threading
        results = []
        
        def create_payment():
            event = {
                "httpMethod": "POST",
                "path": "/payment/create-payment-intent",
                "body": json.dumps({
                    "amount": 1000,
                    "currency": "jpy",
                    "userId": "test-user-concurrent",
                    "serviceType": "image_analysis"
                })
            }
            response = main(event, sample_context)
            results.append(response)
        
        # 3つの並行決済を作成
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=create_payment)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # すべてが成功
        assert len(results) == 3
        for result in results:
            assert result["statusCode"] == 200

    def test_invalid_json_handling(self, sample_context, mock_environment):
        """無効なJSON処理テスト"""
        event = {
            "httpMethod": "POST",
            "path": "/payment/create-payment-intent",
            "body": "invalid json"
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body