"""
MinIO Object Storage Service
"""

import io
import time
from typing import Optional, List, Dict, Any
from minio import Minio
from minio.error import S3Error

from src.config.logging_config import get_service_logger
from src.config import Settings


class MinioService:
    """MinIO object storage service"""
    
    def __init__(self, settings: Settings):
        # Initialize service logger
        self.logger = get_service_logger("minio")
        
        self.settings = settings
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self.bucket_name = settings.minio_bucket_name
        
        self.logger.info("MinIO service initialized", 
                        endpoint=settings.minio_endpoint,
                        bucket_name=settings.minio_bucket_name,
                        secure=settings.minio_secure)
        
    async def initialize(self) -> bool:
        """Initialize MinIO service and create bucket if needed"""
        start_time = time.time()
        self.logger.log_function_start("initialize", bucket_name=self.bucket_name)
        
        try:
            # Check if bucket exists, create if not
            bucket_exists = self.client.bucket_exists(self.bucket_name)
            
            if not bucket_exists:
                self.client.make_bucket(self.bucket_name)
                
                execution_time = (time.time() - start_time) * 1000
                self.logger.log_function_success(
                    "initialize",
                    result="Bucket created successfully",
                    execution_time=execution_time,
                    bucket_name=self.bucket_name,
                    action="created_bucket"
                )
            else:
                execution_time = (time.time() - start_time) * 1000
                self.logger.log_function_success(
                    "initialize",
                    result="Bucket already exists",
                    execution_time=execution_time,
                    bucket_name=self.bucket_name,
                    action="bucket_exists"
                )
            
            return True
            
        except S3Error as e:
            self.logger.log_function_error("initialize", e, bucket_name=self.bucket_name)
            return False
    
    async def health_check(self) -> bool:
        """Check MinIO service health"""
        start_time = time.time()
        self.logger.log_function_start("health_check")
        
        try:
            # Try to list buckets as a health check
            buckets = list(self.client.list_buckets())
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "health_check",
                result="Health check passed",
                execution_time=execution_time,
                bucket_count=len(buckets)
            )
            return True
            
        except Exception as e:
            self.logger.log_function_error("health_check", e)
            return False
    
    async def upload_file(self, object_name: str, file_data: bytes, 
                         content_type: str = "application/octet-stream",
                         metadata: Optional[Dict[str, str]] = None) -> bool:
        """Upload file to MinIO"""
        start_time = time.time()
        self.logger.log_function_start(
            "upload_file",
            object_name=object_name,
            file_size=len(file_data),
            content_type=content_type,
            metadata_keys=list(metadata.keys()) if metadata else []
        )
        
        try:
            file_stream = io.BytesIO(file_data)
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_stream,
                length=len(file_data),
                content_type=content_type,
                metadata=metadata or {}
            )
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "upload_file",
                result=f"File uploaded: {object_name}",
                execution_time=execution_time,
                object_name=object_name,
                file_size=len(file_data),
                content_type=content_type
            )
            return True
            
        except S3Error as e:
            self.logger.log_function_error("upload_file", e, object_name=object_name, file_size=len(file_data))
            return False
    
    async def download_file(self, object_name: str) -> Optional[bytes]:
        """Download file from MinIO"""
        start_time = time.time()
        self.logger.log_function_start("download_file", object_name=object_name)
        
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "download_file",
                result=f"File downloaded: {object_name}",
                execution_time=execution_time,
                object_name=object_name,
                downloaded_size=len(data)
            )
            return data
            
        except S3Error as e:
            self.logger.log_function_error("download_file", e, object_name=object_name)
            return None
    
    async def delete_file(self, object_name: str) -> bool:
        """Delete file from MinIO"""
        start_time = time.time()
        self.logger.log_function_start("delete_file", object_name=object_name)
        
        try:
            self.client.remove_object(self.bucket_name, object_name)
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "delete_file",
                result=f"File deleted: {object_name}",
                execution_time=execution_time,
                object_name=object_name
            )
            return True
            
        except S3Error as e:
            self.logger.log_function_error("delete_file", e, object_name=object_name)
            return False
    
    async def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in MinIO bucket"""
        start_time = time.time()
        self.logger.log_function_start("list_files", prefix=prefix)
        
        try:
            objects = self.client.list_objects(
                self.bucket_name, 
                prefix=prefix, 
                recursive=True
            )
            
            files = []
            for obj in objects:
                files.append({
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag
                })
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "list_files",
                result=f"Listed {len(files)} files",
                execution_time=execution_time,
                prefix=prefix,
                file_count=len(files)
            )
            return files
            
        except S3Error as e:
            self.logger.log_function_error("list_files", e, prefix=prefix)
            return []
    
    async def get_file_info(self, object_name: str) -> Optional[Dict[str, Any]]:
        """Get file information from MinIO"""
        start_time = time.time()
        self.logger.log_function_start("get_file_info", object_name=object_name)
        
        try:
            stat = self.client.stat_object(self.bucket_name, object_name)
            
            file_info = {
                "name": object_name,
                "size": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "metadata": stat.metadata
            }
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "get_file_info",
                result=f"Got file info: {object_name}",
                execution_time=execution_time,
                object_name=object_name,
                file_size=stat.size,
                content_type=stat.content_type
            )
            return file_info
            
        except S3Error as e:
            self.logger.log_function_error("get_file_info", e, object_name=object_name)
            return None 