"""Gui email thong bao job hoan thanh - CHI gui LINK toi trang chi tiet job,
KHONG dinh kem video (video long tieng thuong vuot gioi han dinh kem cua hau
het nha cung cap email, vd. Gmail ~25MB, de bi bounce/vao spam). Dung
`smtplib` chuan cua Python (khong them dependency moi), mac dinh cau hinh
cho Gmail SMTP + App Password (KHONG phai mat khau Gmail thuong, xem
https://myaccount.google.com/apppasswords).
"""

import os
import smtplib
from email.message import EmailMessage


class EmailNotConfiguredError(RuntimeError):
    pass


def _smtp_settings() -> tuple[str, int, str, str, str]:
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    from_name = os.environ.get("SMTP_FROM_NAME", "VietDub Studio")
    if not user or not password:
        raise EmailNotConfiguredError(
            "Chưa cấu hình SMTP_USER/SMTP_PASSWORD trong .env - xem hướng dẫn trong .env.example"
        )
    return host, port, user, password, from_name


def send_job_result_email(to_email: str, job_id: str, filename: str) -> None:
    """Gui email chua link toi trang chi tiet job (`/studio/jobs/{job_id}`)
    cho `to_email` (email dang ky tai khoan, xem AuthUser.email trong
    backend/security.py). Nguoi nhan can dang nhap lai de xem/tai video -
    link KHONG chua token nen an toan hon khi bi forward/leak.
    """
    host, port, user, password, from_name = _smtp_settings()
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    job_url = f"{frontend_url}/studio/jobs/{job_id}"

    message = EmailMessage()
    message["Subject"] = f'Video "{filename}" đã xử lý xong'
    message["From"] = f"{from_name} <{user}>"
    message["To"] = to_email
    message.set_content(
        "Video của bạn đã xử lý xong.\n\n"
        f"Xem và tải video tại: {job_url}\n\n"
        "(Cần đăng nhập lại tài khoản của bạn để xem.)"
    )

    with smtplib.SMTP_SSL(host, port) as smtp:
        smtp.login(user, password)
        smtp.send_message(message)


def send_direct_download_email(to_email: str, filename: str, download_url: str) -> None:
    """Send a direct signed download link for external flows like Telegram.

    Unlike send_job_result_email(), this does not require the receiver to own a
    web account because the URL itself is already scoped and signed.
    """
    host, port, user, password, from_name = _smtp_settings()

    message = EmailMessage()
    message["Subject"] = f'Video "{filename}" da xu ly xong'
    message["From"] = f"{from_name} <{user}>"
    message["To"] = to_email
    message.set_content(
        "Video cua ban da xu ly xong.\n\n"
        f"Tai video tai: {download_url}\n\n"
        "Link nay chi dung cho file ket qua nay va se het han theo cau hinh he thong."
    )

    with smtplib.SMTP_SSL(host, port) as smtp:
        smtp.login(user, password)
        smtp.send_message(message)
