import logging
import os

import httpx

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "Raimy <noreply@raimy.app>")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


async def _send(to: str, subject: str, html: str) -> None:
    if not RESEND_API_KEY:
        logger.info(f"[DEV email skipped] to={to} subject={subject}\n{html}")
        return

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={"from": RESEND_FROM_EMAIL, "to": [to], "subject": subject, "html": html},
        )
        if response.status_code >= 400:
            logger.error(f"Resend send failed ({response.status_code}): {response.text}")


async def send_verification_email(to: str, token: str) -> None:
    link = f"{FRONTEND_URL}/verify-email?token={token}"
    html = f'<p>Click the link below to verify your email and finish creating your Raimy account:</p><p><a href="{link}">{link}</a></p><p>This link expires in 24 hours.</p>'
    await _send(to, "Verify your email for Raimy", html)


async def send_password_reset_email(to: str, token: str) -> None:
    link = f"{FRONTEND_URL}/reset-password?token={token}"
    html = f'<p>Click the link below to reset your Raimy password:</p><p><a href="{link}">{link}</a></p><p>This link expires in 1 hour. If you didn\'t request this, you can ignore this email.</p>'
    await _send(to, "Reset your Raimy password", html)


async def send_account_exists_email(to: str) -> None:
    html = f'<p>Someone tried to sign up with this email, but you already have a Raimy account.</p><p>If this was you, just <a href="{FRONTEND_URL}">log in</a> instead, or use "Forgot password?" if you don\'t remember your password.</p>'
    await _send(to, "You already have a Raimy account", html)


async def send_google_only_account_email(to: str) -> None:
    html = f'<p>Your Raimy account uses Google Sign-In and doesn\'t have a password to reset.</p><p>Just <a href="{FRONTEND_URL}">sign in with Google</a> instead.</p>'
    await _send(to, "Your Raimy account uses Google Sign-In", html)
