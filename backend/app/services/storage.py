import io
import logging
from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error
from datetime import timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


class MinIOService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_prefix = settings.MINIO_BUCKET_PREFIX
    
    def _get_bucket_name(self, project_id: str) -> str:
        safe_id = str(project_id).replace("-", "").lower()[:20]
        return f"{self.bucket_prefix}{safe_id}"
    
    def ensure_bucket_exists(self, project_id: str) -> str:
        bucket_name = self._get_bucket_name(project_id)
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created MinIO bucket: {bucket_name}")
        except S3Error as e:
            logger.error(f"Error creating bucket {bucket_name}: {e}")
            raise
        return bucket_name
    
    async def upload_file(
        self,
        project_id: str,
        file_name: str,
        file_data: BinaryIO,
        content_type: str = "application/octet-stream",
        file_size: int = None
    ) -> dict:
        bucket_name = self.ensure_bucket_exists(project_id)
        
        if file_size is None:
            file_data.seek(0, 2)
            file_size = file_data.tell()
            file_data.seek(0)
        
        try:
            self.client.put_object(
                bucket_name,
                file_name,
                file_data,
                file_size,
                content_type=content_type
            )
            
            object_url = self.get_file_url(project_id, file_name)
            
            logger.info(f"Uploaded file {file_name} to bucket {bucket_name}")
            
            return {
                "bucket_name": bucket_name,
                "object_name": file_name,
                "size": file_size,
                "url": object_url
            }
        except S3Error as e:
            logger.error(f"Error uploading file {file_name}: {e}")
            raise
    
    def get_file_url(self, project_id: str, file_name: str, expires: int = 3600) -> str:
        bucket_name = self._get_bucket_name(project_id)
        try:
            url = self.client.presigned_get_object(
                bucket_name,
                file_name,
                expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            logger.error(f"Error getting file URL: {e}")
            return ""
    
    def download_file(self, project_id: str, file_name: str) -> Optional[bytes]:
        bucket_name = self._get_bucket_name(project_id)
        try:
            response = self.client.get_object(bucket_name, file_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Error downloading file {file_name}: {e}")
            return None
    
    def delete_file(self, project_id: str, file_name: str) -> bool:
        bucket_name = self._get_bucket_name(project_id)
        try:
            self.client.remove_object(bucket_name, file_name)
            logger.info(f"Deleted file {file_name} from bucket {bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting file {file_name}: {e}")
            return False
    
    def list_files(self, project_id: str, prefix: str = "") -> list:
        bucket_name = self._get_bucket_name(project_id)
        files = []
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix)
            for obj in objects:
                files.append({
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag
                })
        except S3Error as e:
            logger.error(f"Error listing files in bucket {bucket_name}: {e}")
        return files
    
    def delete_bucket(self, project_id: str) -> bool:
        bucket_name = self._get_bucket_name(project_id)
        try:
            objects = self.client.list_objects(bucket_name)
            for obj in objects:
                self.client.remove_object(bucket_name, obj.object_name)
            
            self.client.remove_bucket(bucket_name)
            logger.info(f"Deleted bucket {bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting bucket {bucket_name}: {e}")
            return False


minio_service = MinIOService()
