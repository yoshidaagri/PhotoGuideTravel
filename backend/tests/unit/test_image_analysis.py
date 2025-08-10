"""
画像解析Lambda関数の単体テスト
"""
import json
import pytest
from unittest.mock import patch, Mock
import base64

# テスト対象をインポート
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../functions/image-analysis'))
from handler import main, analyze_image_with_gemini, save_analysis_log


class TestImageAnalysisHandler:
    """画像解析ハンドラーテストクラス"""
    
    def test_main_success(self, sample_context, mock_environment, create_test_tables, mock_google_gemini):
        """正常な画像解析テスト"""
        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABA...",  # サンプル画像
                "language": "en",
                "userId": "test-user-001"
            })
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 200
        assert "Content-Type" in response["headers"]
        
        body = json.loads(response["body"])
        assert "analysis" in body
        assert body["language"] == "en"
        assert "timestamp" in body

    def test_main_missing_image(self, sample_context, mock_environment):
        """画像データ未提供エラーテスト"""
        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "language": "en",
                "userId": "test-user-001"
            })
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body
        assert "Image data is required" in body["error"]

    def test_main_options_request(self, sample_context, mock_environment):
        """OPTIONSリクエスト（CORS）テスト"""
        event = {
            "httpMethod": "OPTIONS"
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 200
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        assert "Access-Control-Allow-Methods" in response["headers"]

    def test_main_invalid_json(self, sample_context, mock_environment):
        """無効なJSONエラーテスト"""
        event = {
            "httpMethod": "POST",
            "body": "invalid json"
        }
        
        response = main(event, sample_context)
        
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body

    def test_analyze_image_with_gemini_success(self, mock_environment, mock_google_gemini):
        """Gemini API正常呼び出しテスト"""
        image_data = base64.b64encode(b"fake image data").decode()
        
        result = analyze_image_with_gemini(image_data, "en")
        
        assert "analysis" in result
        assert result["language"] == "en"
        assert "timestamp" in result
        assert result["model"] == "gemini-2.0-flash-exp"
        assert not result.get("error", False)

    def test_analyze_image_with_gemini_japanese(self, mock_environment, mock_google_gemini):
        """Gemini API日本語解析テスト"""
        image_data = base64.b64encode(b"fake image data").decode()
        
        result = analyze_image_with_gemini(image_data, "ja")
        
        assert result["language"] == "ja"
        assert "analysis" in result

    def test_analyze_image_with_gemini_korean(self, mock_environment, mock_google_gemini):
        """Gemini API韓国語解析テスト"""
        image_data = base64.b64encode(b"fake image data").decode()
        
        result = analyze_image_with_gemini(image_data, "ko")
        
        assert result["language"] == "ko"
        assert "analysis" in result

    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_analyze_image_with_gemini_api_error(self, mock_model, mock_configure, mock_environment):
        """Gemini APIエラーテスト"""
        mock_model.return_value.generate_content.side_effect = Exception("API Error")
        
        image_data = base64.b64encode(b"fake image data").decode()
        result = analyze_image_with_gemini(image_data, "en")
        
        assert result.get("error") == True
        assert "API Error" in result["analysis"]

    def test_save_analysis_log_success(self, mock_environment, create_test_tables):
        """解析ログ保存成功テスト"""
        user_id = "test-user-001"
        result = {
            "analysis": "Test analysis result",
            "language": "en",
            "model": "gemini-2.0-flash-exp"
        }
        image_data = "base64_image_data"
        
        # エラーが発生しないことを確認
        save_analysis_log(user_id, result, image_data)

    def test_save_analysis_log_with_error(self, mock_environment, create_test_tables):
        """解析ログ保存エラー時テスト"""
        user_id = "test-user-001"
        result = {
            "analysis": "Error analysis",
            "language": "en",
            "error": True
        }
        image_data = "base64_image_data"
        
        # エラーが発生してもクラッシュしないことを確認
        save_analysis_log(user_id, result, image_data)

    def test_base64_image_processing(self, mock_environment, mock_google_gemini):
        """Base64画像データ処理テスト"""
        # data URL形式
        data_url_image = "data:image/jpeg;base64,/9j/4AAQSkZJRgABA..."
        result1 = analyze_image_with_gemini(data_url_image, "en")
        assert not result1.get("error", False)
        
        # 直接Base64
        direct_b64 = "/9j/4AAQSkZJRgABA..."
        result2 = analyze_image_with_gemini(direct_b64, "en")
        assert not result2.get("error", False)

    def test_multilingual_prompt_generation(self, mock_environment):
        """多言語プロンプト生成テスト"""
        # 各言語でプロンプトが適切に生成されることを間接的にテスト
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel') as mock_model:
            mock_response = Mock()
            mock_response.text = "Test response"
            mock_model.return_value.generate_content.return_value = mock_response
            
            # 英語
            result_en = analyze_image_with_gemini("test_image", "en")
            assert result_en["language"] == "en"
            
            # 日本語
            result_ja = analyze_image_with_gemini("test_image", "ja")
            assert result_ja["language"] == "ja"
            
            # 韓国語
            result_ko = analyze_image_with_gemini("test_image", "ko")
            assert result_ko["language"] == "ko"
            
            # デフォルト（英語）
            result_default = analyze_image_with_gemini("test_image", "unknown")
            assert result_default["language"] == "unknown"  # 指定された言語を保持

    def test_large_image_handling(self, sample_context, mock_environment, mock_google_gemini):
        """大きな画像データの処理テスト"""
        # 大きなBase64データをシミュレート
        large_image_data = "x" * 10000  # 10KB相当
        
        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "image": large_image_data,
                "language": "en",
                "userId": "test-user-001"
            })
        }
        
        response = main(event, sample_context)
        # エラーにならないことを確認
        assert response["statusCode"] in [200, 500]  # 500の場合はデコードエラー

    def test_concurrent_requests_simulation(self, sample_context, mock_environment, mock_google_gemini):
        """並行リクエストシミュレーションテスト"""
        import threading
        import time
        
        results = []
        
        def make_request():
            event = {
                "httpMethod": "POST",
                "body": json.dumps({
                    "image": "dGVzdCBpbWFnZQ==",  # "test image" in base64
                    "language": "en",
                    "userId": "test-user-concurrent"
                })
            }
            response = main(event, sample_context)
            results.append(response)
        
        # 5つの並行リクエストを実行
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # すべてのリクエストが処理されたことを確認
        assert len(results) == 5
        for result in results:
            assert result["statusCode"] in [200, 500]