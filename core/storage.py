import os

os.environ.setdefault("AWS_REQUEST_CHECKSUM_CALCULATION", "when_required")
os.environ.setdefault("AWS_RESPONSE_CHECKSUM_VALIDATION", "when_required")

from botocore.config import Config
from botocore.exceptions import ClientError

try:
    from storages.backends.s3boto3 import S3Boto3Storage
except ImportError:
    from storages.backends.s3 import S3Storage as S3Boto3Storage

try:
    CLIENT_CONFIG = Config(
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
        signature_version="s3v4",
        s3={"addressing_style": "path"},
    )
except TypeError:
    CLIENT_CONFIG = Config(
        signature_version="s3v4",
        s3={"addressing_style": "path"},
    )


class MediaStorage(S3Boto3Storage):
    """Supabase-compatible S3 storage for user uploads on Vercel."""

    location = ""
    file_overwrite = True
    default_acl = None
    querystring_auth = False
    addressing_style = "path"
    signature_version = "s3v4"
    object_parameters = {}
    client_config = CLIENT_CONFIG
    config = CLIENT_CONFIG

    def exists(self, name):
        try:
            return super().exists(name)
        except ClientError:
            return False

    def get_available_name(self, name, max_length=None):
        name = name.replace("\\", "/").lstrip("/")
        if max_length and len(name) > max_length:
            name = name[:max_length]
        return name

    def _save(self, name, content):
        """Upload with PutObject only — no ACL/CacheControl/checksum extras."""
        if hasattr(content, "seek"):
            try:
                content.seek(0)
            except Exception:
                pass
        body = content.read() if hasattr(content, "read") else content
        content_type = getattr(content, "content_type", None) or "application/octet-stream"
        self.connection.meta.client.put_object(
            Bucket=self.bucket_name,
            Key=name,
            Body=body,
            ContentType=content_type,
        )
        return name
