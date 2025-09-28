# import boto3
from botocore.exceptions import NoCredentialsError

AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
AWS_STORAGE_BUCKET_NAME = ''
AWS_S3_REGION_NAME = ''
AWS_S3_ENDPOINT_URL = ''

# Initialize a session using your credentials
# s3_client = boto3.client(
#     's3',
#     aws_access_key_id=AWS_ACCESS_KEY_ID,
#     aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
#     region_name=AWS_S3_REGION_NAME,
#     endpoint_url=AWS_S3_ENDPOINT_URL
# )
s3_client = None

def upload_video_to_s3(video_file_path, s3_key):
    try:
        with open(video_file_path, 'rb') as video_file:
            s3_client.upload_fileobj(
                video_file,
                AWS_STORAGE_BUCKET_NAME,
                s3_key,
                ExtraArgs={
                    'CacheControl': 'max-age=86400',
                    'ContentType': 'video/mp4',
                }
            )
        print(f"Video uploaded successfully: {s3_key}")
    except FileNotFoundError:
        print(f"Error: File {video_file_path} not found.")
    except NoCredentialsError:
        print("Error: AWS credentials not found.")
    except Exception as e:
        print(f"Error: {e}")

# Example usage
video_file_path = '/home/sahil/Music/himstar-backend/media/banners/dancebanner.jpg'  # Replace with your local video file path
s3_key = 'videos/your_video.mp4'

upload_video_to_s3(video_file_path, s3_key)
