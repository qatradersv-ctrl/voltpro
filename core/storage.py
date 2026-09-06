try:
    from storages.backends.s3boto3 import S3Boto3Storage
except ImportError:
    from storages.backends.s3 import S3Storage as S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """Supabase-compatible S3 storage for user uploads on Vercel."""

    location = ""
    file_overwrite = False
    default_acl = None
    querystring_auth = False
    addressing_style = "path"
    signature_version = "s3v4"
    object_parameters = {"CacheControl": "max-age=86400"}
