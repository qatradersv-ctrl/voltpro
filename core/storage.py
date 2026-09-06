from botocore.exceptions import ClientError

try:
    from storages.backends.s3boto3 import S3Boto3Storage
except ImportError:
    from storages.backends.s3 import S3Storage as S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """Supabase-compatible S3 storage for user uploads on Vercel.

    Supabase's S3 API returns 403 for HeadObject, which django-storages
    uses to check whether a name is free. Skip that check and never
    overwrite: callers should use unique object keys.
    """

    location = ""
    file_overwrite = True
    default_acl = None
    querystring_auth = False
    addressing_style = "path"
    signature_version = "s3v4"
    object_parameters = {"CacheControl": "max-age=86400"}

    def exists(self, name):
        try:
            return super().exists(name)
        except ClientError:
            return False

    def get_available_name(self, name, max_length=None):
        # Unique UUID keys are generated in upload_to; do not call HeadObject.
        name = name.replace("\\", "/").lstrip("/")
        if max_length and len(name) > max_length:
            name = name[:max_length]
        return name
