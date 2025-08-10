"""
pytest設定・フィクスチャ定義
"""
import pytest
import boto3
import os
from moto import mock_dynamodb
from unittest.mock import patch


@pytest.fixture(scope="session")
def aws_credentials():
    """Mock AWS認証情報"""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "ap-northeast-1"


@pytest.fixture(scope="function")
def mock_dynamodb_fixture(aws_credentials):
    """DynamoDB モック"""
    with mock_dynamodb():
        yield boto3.resource("dynamodb", region_name="ap-northeast-1")


@pytest.fixture
def mock_environment():
    """環境変数モック"""
    with patch.dict(os.environ, {
        "STAGE": "test",
        "GOOGLE_GEMINI_API_KEY": "test-gemini-key",
        "STRIPE_SECRET_KEY": "test-stripe-key",
        "JWT_SECRET": "test-jwt-secret",
        "PROJECT_NAME": "ai-tourism-poc"
    }):
        yield


@pytest.fixture
def create_test_tables(mock_dynamodb_fixture):
    """テスト用DynamoDBテーブル作成"""
    dynamodb = mock_dynamodb_fixture
    
    # Users Table
    users_table = dynamodb.create_table(
        TableName="ai-tourism-poc-users-test",
        KeySchema=[
            {"AttributeName": "userId", "KeyType": "HASH"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "userId", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST"
    )
    
    # Analysis History Table
    analysis_table = dynamodb.create_table(
        TableName="ai-tourism-poc-analysis-history-test",
        KeySchema=[
            {"AttributeName": "userId", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "userId", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST"
    )
    
    # Payment History Table
    payment_table = dynamodb.create_table(
        TableName="ai-tourism-poc-payment-history-test",
        KeySchema=[
            {"AttributeName": "userId", "KeyType": "HASH"},
            {"AttributeName": "paymentId", "KeyType": "RANGE"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "userId", "AttributeType": "S"},
            {"AttributeName": "paymentId", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST"
    )
    
    yield {
        'users': users_table,
        'analysis': analysis_table,
        'payment': payment_table
    }


@pytest.fixture
def sample_user_data():
    """サンプルユーザーデータ"""
    return {
        "userId": "test-user-001",
        "email": "test@example.com",
        "name": "Test User",
        "passwordHash": "hashed-password",
        "createdAt": "2025-01-09T00:00:00.000Z",
        "lastLogin": "2025-01-09T00:00:00.000Z"
    }


@pytest.fixture
def sample_event():
    """サンプルLambdaイベント"""
    return {
        "httpMethod": "POST",
        "path": "/test",
        "pathParameters": None,
        "queryStringParameters": None,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": '{"test": "data"}',
        "isBase64Encoded": False
    }


@pytest.fixture
def sample_context():
    """サンプルLambdaコンテキスト"""
    class MockContext:
        def __init__(self):
            self.function_name = "test-function"
            self.function_version = "$LATEST"
            self.invoked_function_arn = "arn:aws:lambda:ap-northeast-1:123456789012:function:test-function"
            self.memory_limit_in_mb = "128"
            self.remaining_time_in_millis = lambda: 300000
            self.log_group_name = "/aws/lambda/test-function"
            self.log_stream_name = "test-stream"
            self.aws_request_id = "test-request-id"
    
    return MockContext()


@pytest.fixture
def mock_stripe_api():
    """Stripe API モック"""
    import stripe
    from unittest.mock import Mock
    
    # PaymentIntent モック
    mock_payment_intent = Mock()
    mock_payment_intent.id = "pi_test_123"
    mock_payment_intent.client_secret = "pi_test_123_secret_test"
    mock_payment_intent.status = "succeeded"
    mock_payment_intent.metadata = {"userId": "test-user-001"}
    
    with patch.object(stripe.PaymentIntent, 'create', return_value=mock_payment_intent), \
         patch.object(stripe.PaymentIntent, 'retrieve', return_value=mock_payment_intent):
        yield mock_payment_intent


@pytest.fixture
def mock_google_gemini():
    """Google Gemini API モック"""
    from unittest.mock import Mock, patch
    
    mock_response = Mock()
    mock_response.text = "This is a beautiful temple in Kyoto, Japan. It represents traditional Japanese architecture..."
    
    with patch('google.generativeai.configure'), \
         patch('google.generativeai.GenerativeModel') as mock_model:
        mock_model.return_value.generate_content.return_value = mock_response
        yield mock_response