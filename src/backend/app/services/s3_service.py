import boto3
from botocore.exceptions import ClientError
from app.core.config import settings


class S3Service:
    """AWS S3 파일 업로드/다운로드 서비스"""

    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
        self.bucket = settings.aws_s3_bucket

    def download_image(self, s3_key: str, local_path: str) -> str:
        """
        S3에서 이미지를 다운로드하여 로컬 파일로 저장

        Args:
            s3_key: S3 객체 키 (예: "uploads/original/image.jpg")
            local_path: 저장할 로컬 파일 경로

        Returns:
            로컬 파일 경로
        """
        try:
            self.s3_client.download_file(self.bucket, s3_key, local_path)
            print(f"✅ S3 다운로드 완료: {s3_key} -> {local_path}")
            return local_path
        except ClientError as e:
            print(f"❌ S3 다운로드 실패: {e}")
            raise

    def upload_image(self, local_path: str, s3_key: str) -> str:
        """
        로컬 이미지를 S3에 업로드

        Args:
            local_path: 업로드할 로컬 파일 경로
            s3_key: S3에 저장될 객체 키

        Returns:
            S3 객체 키
        """
        try:
            self.s3_client.upload_file(
                local_path,
                self.bucket,
                s3_key,
                ExtraArgs={"ContentType": "image/png"},
            )
            print(f"✅ S3 업로드 완료: {local_path} -> {s3_key}")
            return s3_key
        except ClientError as e:
            print(f"❌ S3 업로드 실패: {e}")
            raise

    def get_public_url(self, s3_key: str) -> str:
        """
        S3 객체의 공개 URL 반환 (버킷이 공개 설정된 경우)

        Args:
            s3_key: S3 객체 키

        Returns:
            공개 URL
        """
        return f"https://{self.bucket}.s3.{settings.aws_region}.amazonaws.com/{s3_key}"
