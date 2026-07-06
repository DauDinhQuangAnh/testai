"""Test backend/email_sender.py - mock smtplib, khong gui mail that."""

import pytest

from backend.email_sender import EmailNotConfiguredError, send_job_result_email


def test_send_job_result_email_raises_when_not_configured(monkeypatch):
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)

    with pytest.raises(EmailNotConfiguredError):
        send_job_result_email("user@test.com", "job-123", "video.mp4")


def test_send_job_result_email_sends_link_not_attachment(monkeypatch):
    monkeypatch.setenv("SMTP_USER", "bot@gmail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "app-password")
    monkeypatch.setenv("FRONTEND_URL", "https://example.com")

    sent_messages = []

    class FakeSMTP:
        def __init__(self, host, port):
            self.host = host
            self.port = port

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def login(self, user, password):
            assert user == "bot@gmail.com"
            assert password == "app-password"

        def send_message(self, message):
            sent_messages.append(message)

    monkeypatch.setattr("backend.email_sender.smtplib.SMTP_SSL", FakeSMTP)

    send_job_result_email("user@test.com", "job-123", "video.mp4")

    assert len(sent_messages) == 1
    message = sent_messages[0]
    assert message["To"] == "user@test.com"
    body = message.get_content()
    assert "https://example.com/studio/jobs/job-123" in body
    # Khong dinh kem file - chi gui link.
    assert list(message.iter_attachments()) == []
