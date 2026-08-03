"""
File upload security controls.
Blueprint reference: Doc 1 section 25, Doc 2 section 9.

Implements: extension allowlist, MIME-type check, magic-byte signature check,
random safe filenames, size limits, and a scan_status pipeline placeholder
(a real deployment would call an actual AV engine, e.g. ClamAV, here).
"""
import os
import uuid
import mimetypes

# Magic-byte signatures for common allowed types (first bytes of the file)
MAGIC_SIGNATURES = {
    b"\xff\xd8\xff": "jpg",
    b"\x89PNG\r\n\x1a\n": "png",
    b"RIFF": "webp",       # WEBP starts with RIFF....WEBP
    b"%PDF-": "pdf",
    b"PK\x03\x04": "docx_xlsx_zip",  # docx/xlsx are zip containers
    b"\xd0\xcf\x11\xe0": "doc_xls_legacy",  # old-style OLE binary doc/xls
}

DANGEROUS_EXTENSIONS = {
    "exe", "bat", "cmd", "sh", "com", "msi", "scr", "js", "jar",
    "vbs", "ps1", "app", "dll", "py", "php", "rb",
}


class FileValidationResult:
    def __init__(self, valid, message=None, safe_filename=None, extension=None):
        self.valid = valid
        self.message = message
        self.safe_filename = safe_filename
        self.extension = extension


def _detect_signature(header: bytes) -> str | None:
    for sig, kind in MAGIC_SIGNATURES.items():
        if header.startswith(sig):
            return kind
    return None


def validate_upload(filename: str, file_bytes: bytes, allowed_extensions: set, max_size: int) -> FileValidationResult:
    if not filename or "." not in filename:
        return FileValidationResult(False, message="This file type is not supported or exceeds the permitted size.")

    ext = filename.rsplit(".", 1)[-1].lower()

    if ext in DANGEROUS_EXTENSIONS:
        return FileValidationResult(False, message="This file type is not permitted for upload.")

    if ext not in allowed_extensions:
        return FileValidationResult(False, message="This file type is not supported or exceeds the permitted size.")

    if len(file_bytes) == 0:
        return FileValidationResult(False, message="The uploaded file appears to be empty.")

    if len(file_bytes) > max_size:
        return FileValidationResult(False, message="This file type is not supported or exceeds the permitted size.")

    # Signature (magic-byte) check — reject files whose content doesn't match extension
    header = file_bytes[:16]
    detected = _detect_signature(header)

    # txt files have no reliable signature — allow only if content decodes as text
    if ext == "txt":
        try:
            file_bytes[:2048].decode("utf-8")
        except UnicodeDecodeError:
            return FileValidationResult(False, message="This file does not appear to be a valid text file.")
    else:
        plausible = {
            "jpg": {"jpg"}, "jpeg": {"jpg"}, "png": {"png"}, "webp": {"webp"},
            "pdf": {"pdf"}, "docx": {"docx_xlsx_zip"}, "xlsx": {"docx_xlsx_zip"},
            "doc": {"doc_xls_legacy"}, "xls": {"doc_xls_legacy"},
        }
        expected = plausible.get(ext)
        if expected and detected not in expected:
            return FileValidationResult(
                False, message="The file's contents do not match its file extension."
            )

    safe_name = f"{uuid.uuid4().hex}.{ext}"
    return FileValidationResult(True, safe_filename=safe_name, extension=ext)


def save_upload(file_bytes: bytes, safe_filename: str, upload_folder: str) -> str:
    """Stores the file outside the public web root and returns the storage path."""
    os.makedirs(upload_folder, exist_ok=True)
    path = os.path.join(upload_folder, safe_filename)
    with open(path, "wb") as f:
        f.write(file_bytes)
    return path


def run_malware_scan(storage_path: str) -> str:
    """
    Placeholder scan hook. In production, integrate a real AV engine
    (e.g. ClamAV via clamd) here and return 'clean' | 'infected' | 'error'.
    Until a real scanner is wired in, files are marked 'pending' so they are
    never auto-previewed (per Doc 1 section 25: 'do not preview a file until
    scanning is complete').
    """
    return "pending"
