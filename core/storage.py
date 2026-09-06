import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


def _env(*names):
    for name in names:
        value = os.environ.get(name)
        if value:
            return value.strip()
    return ""


def _project_url():
    url = _env("SUPABASE_URL")
    if url:
        return url.rstrip("/")
    endpoint = _env("AWS_S3_ENDPOINT_URL") or getattr(settings, "AWS_S3_ENDPOINT_URL", "")
    if endpoint:
        return (
            endpoint.replace("/storage/v1/s3", "")
            .rstrip("/")
        )
    raise ImproperlyConfigured(
        "Set SUPABASE_URL (https://<project-ref>.supabase.co) or AWS_S3_ENDPOINT_URL."
    )


def _bearer_token():
    """Supabase Storage REST needs a JWT, not S3 access keys."""
    candidates = (
        _env(
            "SUPABASE_SERVICE_ROLE_KEY",
            "SUPABASE_KEY",
            "SUPABASE_ANON_KEY",
            "NEXT_PUBLIC_SUPABASE_ANON_KEY",
        ),
        _env("AWS_SECRET_ACCESS_KEY"),
        _env("AWS_ACCESS_KEY_ID"),
    )
    for value in candidates:
        if value.startswith("eyJ"):
            return value
    return _env("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_KEY", "SUPABASE_ANON_KEY")


class SupabaseStorageError(Exception):
    pass


@deconstructible
class MediaStorage(Storage):
    """Upload via Supabase Storage HTTP API (S3 PutObject is unreliable here)."""

    def __init__(self, **kwargs):
        super().__init__()
        self.bucket = (
            _env("AWS_STORAGE_BUCKET_NAME")
            or getattr(settings, "AWS_STORAGE_BUCKET_NAME", "")
            or "voltpro-media"
        )
        self.project_url = _project_url()
        self.token = _bearer_token()

    def _require_token(self):
        if not self.token:
            raise ImproperlyConfigured(
                "Uploads need SUPABASE_SERVICE_ROLE_KEY in Vercel env vars. "
                "Copy it from Supabase → Project Settings → API → service_role "
                "(secret). S3 access keys are not used for this upload path."
            )

    def _object_url(self, name, public=False):
        name = name.replace("\\", "/").lstrip("/")
        encoded = urllib.parse.quote(name, safe="/")
        kind = "object/public" if public else "object"
        return f"{self.project_url}/storage/v1/{kind}/{self.bucket}/{encoded}"

    def get_available_name(self, name, max_length=None):
        name = name.replace("\\", "/").lstrip("/")
        if max_length and len(name) > max_length:
            name = name[:max_length]
        return name

    def exists(self, name):
        return False

    def url(self, name):
        custom = getattr(settings, "MEDIA_URL", "")
        name = name.replace("\\", "/").lstrip("/")
        if custom and custom.startswith("http"):
            return f"{custom.rstrip('/')}/{name}"
        return self._object_url(name, public=True)

    def _save(self, name, content):
        self._require_token()
        if hasattr(content, "seek"):
            try:
                content.seek(0)
            except Exception:
                pass
        body = content.read() if hasattr(content, "read") else content
        content_type = (
            getattr(content, "content_type", None)
            or mimetypes.guess_type(name)[0]
            or "application/octet-stream"
        )
        request = urllib.request.Request(
            self._object_url(name, public=False),
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.token}",
                "apikey": self.token,
                "Content-Type": content_type,
                "x-upsert": "true",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:800]
            raise SupabaseStorageError(
                f"Supabase upload failed ({exc.code} {exc.reason}): {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise SupabaseStorageError(f"Supabase upload failed: {exc.reason}") from exc
        return name

    def delete(self, name):
        if not self.token:
            return
        request = urllib.request.Request(
            self._object_url(name, public=False),
            method="DELETE",
            headers={
                "Authorization": f"Bearer {self.token}",
                "apikey": self.token,
            },
        )
        try:
            urllib.request.urlopen(request, timeout=30)
        except urllib.error.HTTPError:
            pass

    def size(self, name):
        return 0

    def listdir(self, path):
        return [], []
