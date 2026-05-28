"""
Конвертация docx → pdf через headless LibreOffice (soffice).

Сервис намеренно вынесен в отдельный модуль (а не лежит в большом
outgoing_registry.py), чтобы переиспользоваться из любого роутера
(KP, исходящие, договоры). Если на машине нет soffice — функция
возвращает None, и вызывающий код фолбэчится на «только docx».
"""
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


# LibreOffice headless при первом запуске может прогревать профиль ~10с.
_DOC_CONVERT_TIMEOUT = 90


def is_soffice_available() -> bool:
    """True, если в PATH есть `soffice`. Кешировать смысла нет —
    нативный shutil.which ~доли мс."""
    return shutil.which("soffice") is not None


def convert_docx_bytes_to_pdf(data: bytes) -> Optional[bytes]:
    """Преобразовать docx (bytes) в pdf (bytes) через soffice.

    Возвращает None если:
      • soffice недоступен;
      • конвертация упала (timeout / non-zero exit);
      • soffice не сгенерировал output-файл.
    Вызывающий код должен корректно обработать None — например, сохранить
    только docx, без pdf.
    """
    if not is_soffice_available():
        return None
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        docx_path = tmp_path / "input.docx"
        docx_path.write_bytes(data)
        try:
            result = subprocess.run(
                [
                    "soffice",
                    "--headless",
                    "--nologo",
                    "--nolockcheck",
                    "--norestore",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(tmp_path),
                    str(docx_path),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=_DOC_CONVERT_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return None
        pdf_path = tmp_path / "input.pdf"
        if result.returncode == 0 and pdf_path.exists():
            return pdf_path.read_bytes()
        return None
