import json
import boto3
import base64
import uuid
from datetime import datetime
import os

def main(event, context):
    """
    画像をS3にアップロードし、メタデータをDynamoDBに保存
    """
    try:
        # CORS headers
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'POST,OPTIONS'
        }
        
        if event['httpMethod'] == 'OPTIONS':
            return {'statusCode': 200, 'headers': headers, 'body': ''}
        
        # リクエスト解析
        body = json.loads(event['body'])
        image_data = body.get('image')  # base64 encoded image
        filename = body.get('filename', 'image.jpg')
        user_id = body.get('userId', 'sapporo-guide')
        analysis_type = body.get('analysisType', 'store')
        language = body.get('language', 'ja')
        
        if not image_data:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Image data is required'})
            }
        
        # S3にアップロード
        s3_result = upload_to_s3(image_data, filename, user_id)
        
        # DynamoDBにメタデータ保存
        metadata_result = save_image_metadata(
            s3_result['s3_key'], 
            s3_result['s3_url'], 
            user_id, 
            filename, 
            analysis_type, 
            language
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Image uploaded successfully',
                'image_id': metadata_result['image_id'],
                's3_url': s3_result['s3_url'],
                's3_key': s3_result['s3_key'],
                'uploaded_at': metadata_result['uploaded_at']
            })
        }
        
    except Exception as e:
        print(f"Image upload error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Image upload failed: {str(e)}'})
        }


def upload_to_s3(image_data, filename, user_id):
    """
    Base64画像をS3にアップロード
    """
    s3_client = boto3.client('s3')
    bucket_name = 'ai-tourism-poc-images-dev'
    
    # Base64デコード
    try:
        image_bytes = base64.b64decode(image_data)
    except Exception as e:
        raise Exception(f"Invalid base64 image data: {str(e)}")
    
    # ユニークなファイル名生成
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    file_extension = filename.split('.')[-1].lower() if '.' in filename else 'jpg'
    s3_filename = f"{timestamp}_{unique_id}.{file_extension}"
    
    # S3キー（パス）
    s3_key = f"users/{user_id}/images/{s3_filename}"
    
    # Content-Type設定
    content_type_map = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg', 
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp'
    }
    content_type = content_type_map.get(file_extension, 'image/jpeg')
    
    # S3アップロード
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=image_bytes,
            ContentType=content_type,
            CacheControl='max-age=31536000',  # 1年キャッシュ
            ServerSideEncryption='AES256'
        )
        
        s3_url = f"https://{bucket_name}.s3.ap-northeast-1.amazonaws.com/{s3_key}"
        
        return {
            's3_key': s3_key,
            's3_url': s3_url,
            'bucket': bucket_name
        }
        
    except Exception as e:
        raise Exception(f"S3 upload failed: {str(e)}")


def save_image_metadata(s3_key, s3_url, user_id, filename, analysis_type, language, analysis_result=None):
    """
    画像メタデータをDynamoDBに保存
    """
    dynamodb = boto3.resource('dynamodb')
    table_name = f"{os.environ.get('PROJECT_NAME', 'ai-tourism-poc')}-images-{os.environ.get('STAGE', 'dev')}"
    table = dynamodb.Table(table_name)
    
    image_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    # 返答文の先頭200文字を保存
    analysis_summary = ""
    response_truncated = False
    if analysis_result:
        analysis_summary = analysis_result[:200]
        response_truncated = len(analysis_result) > 200
    
    item = {
        'image_id': image_id,
        'user_id': user_id,
        's3_key': s3_key,
        's3_url': s3_url,
        'original_filename': filename,
        'analysis_type': analysis_type,
        'language': language,
        'uploaded_at': timestamp,
        'created_at': timestamp,
        'status': 'uploaded',
        'analysis_summary': analysis_summary,
        'response_truncated': response_truncated
    }
    
    try:
        table.put_item(Item=item)
        return {
            'image_id': image_id,
            'uploaded_at': timestamp
        }
    except Exception as e:
        print(f"DynamoDB save error: {str(e)}")
        # S3にはアップロード済みなので、メタデータ保存失敗でもエラーにしない
        return {
            'image_id': image_id,
            'uploaded_at': timestamp,
            'warning': 'Metadata save failed but image uploaded to S3'
        }


def update_image_with_analysis(image_id, analysis_result):
    """
    画像に解析結果を追加保存
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table_name = f"{os.environ.get('PROJECT_NAME', 'ai-tourism-poc')}-images-{os.environ.get('STAGE', 'dev')}"
        table = dynamodb.Table(table_name)
        
        # 返答文の先頭200文字を保存
        analysis_summary = analysis_result[:200] if analysis_result else ""
        response_truncated = len(analysis_result) > 200 if analysis_result else False
        
        table.update_item(
            Key={'image_id': image_id},
            UpdateExpression="SET analysis_summary = :summary, response_truncated = :truncated, #status = :status, analyzed_at = :analyzed_at",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':summary': analysis_summary,
                ':truncated': response_truncated,
                ':status': 'analyzed',
                ':analyzed_at': datetime.now().isoformat()
            }
        )
        return True
    except Exception as e:
        print(f"Failed to update image analysis: {str(e)}")
        return False