# from storages.backends.azure_storage import AzureStorage
# from django.conf import settings
# from azure.storage.blob import BlobServiceClient
# import concurrent.futures
# import base64
from django.core.files.storage import default_storage


# Fallback storage class for when Azure is not configured
class AzureMediaStorage:
    """
    Fallback storage class that uses Django's default storage
    when Azure storage is not configured or available.
    """
    def __init__(self):
        pass
    
    def __call__(self):
        return default_storage



# class AzureMediaStorage(AzureStorage):
#     account_name = settings.AZURE_ACCOUNT_NAME
#     connection_string = settings.AZURE_CONNECTION_STRING
#     azure_container = settings.AZURE_CONTAINER
#     expiration_secs = None  # Keep URLs public


# def delete_blob_from_azure(file_uri):
#     """Function to delete a blob from Azure Storage"""
#     try:
#         blob_name = file_uri.split(f'{settings.AZURE_CONTAINER}/')[-1]
#         blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_CONNECTION_STRING)
#         blob_client = blob_service_client.get_blob_client(container=settings.AZURE_CONTAINER, blob=blob_name)
#         blob_client.delete_blob()
#         print(f"Deleted blob: {blob_name}")
#     except Exception as e:
#         print(f"Error deleting blob: {e}")


# def upload_chunk(blob_client, block_id, chunk):
#     """Upload a chunk of the file."""
#     blob_client.stage_block(block_id=block_id, data=chunk)

# def upload_video_to_azure(file_path, blob_name):
#     """Upload a video file to Azure Blob Storage using block blobs."""
#     blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_CONNECTION_STRING)
#     blob_client = blob_service_client.get_blob_client(settings.AZURE_CONTAINER, blob_name)

#     # Read the file in chunks and upload in parallel
#     block_size = 4 * 1024 * 1024  # 4MB chunks
#     block_ids = []
    
#     with open(file_path, "rb") as f:
#         with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
#             offset = 0
#             futures = []
#             while chunk := f.read(block_size):
#                 block_id = base64.b64encode(f"{offset:06}".encode()).decode()  # Fixed: Proper block ID
#                 block_ids.append(block_id)
#                 futures.append(executor.submit(upload_chunk, blob_client, block_id, chunk))
#                 offset += 1

#             # Ensure all chunks are uploaded before committing
#             concurrent.futures.wait(futures)

#     # Commit the blocks in the correct order
#     blob_client.commit_block_list(block_ids)
