"""
Reusable email utilities for Brevo SMTP integration through Django email.
"""

import logging
from email.utils import parseaddr
from html import escape
from typing import Any, Dict, Optional
from urllib.parse import quote

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection

logger = logging.getLogger(__name__)


def _extract_email_address(email: str) -> str:
    """Return the address part from either user@example.com or Name <user@example.com>."""
    return parseaddr(email or '')[1].strip().lower()


def _validate_email(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False

    email = _extract_email_address(email)
    if len(email) < 5 or len(email) > 254:
        return False
    if '@' not in email or email.count('@') != 1:
        return False

    local_part, domain = email.rsplit('@', 1)
    return bool(local_part and domain and '.' in domain)


def _email_service_is_configured() -> Dict[str, Any]:
    required_settings = {
        'EMAIL_HOST': getattr(settings, 'EMAIL_HOST', ''),
        'EMAIL_HOST_USER': getattr(settings, 'EMAIL_HOST_USER', ''),
        'EMAIL_HOST_PASSWORD': getattr(settings, 'EMAIL_HOST_PASSWORD', ''),
        'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', ''),
    }
    missing = [name for name, value in required_settings.items() if not value]

    if missing:
        return {
            'success': False,
            'message': f'Email service is missing: {", ".join(missing)}.',
            'error': 'not_configured',
        }

    if not _validate_email(required_settings['DEFAULT_FROM_EMAIL']):
        return {
            'success': False,
            'message': 'DEFAULT_FROM_EMAIL must be a valid sender email address.',
            'error': 'invalid_from_email',
        }

    return {'success': True}


def _html_paragraphs(message: str) -> str:
    paragraphs = []
    for block in message.strip().splitlines():
        text = block.strip()
        if text:
            paragraphs.append(f'<p style="margin:0 0 14px;">{escape(text)}</p>')
    return ''.join(paragraphs) or '<p style="margin:0;">No message content provided.</p>'


def build_profile_email_html(
    sender_name: str,
    sender_email: str,
    subject: str,
    message: str,
) -> str:
    safe_sender_name = escape(sender_name or 'NoteNexus user')
    safe_sender_email = escape(sender_email or '')
    safe_subject = escape(subject or 'Message from NoteNexus')
    reply_subject = quote('Re: ' + (subject or ''))
    safe_reply_url = f'mailto:{safe_sender_email}?subject={reply_subject}'

    return f"""
    <div style="margin:0; padding:0; background:#f4f7fb; font-family:Arial, Helvetica, sans-serif; color:#1f2937;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f7fb; padding:28px 12px;">
            <tr>
                <td align="center">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:680px; background:#ffffff; border:1px solid #e5e7eb; border-radius:12px; overflow:hidden;">
                        <tr>
                            <td style="background:#2563eb; padding:26px 30px; color:#ffffff;">
                                <div style="font-size:13px; letter-spacing:.08em; text-transform:uppercase; opacity:.9;">NoteNexus Message</div>
                                <h1 style="margin:8px 0 0; font-size:24px; line-height:1.3; font-weight:700;">{safe_subject}</h1>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:28px 30px 12px;">
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f9fafb; border:1px solid #e5e7eb; border-radius:10px;">
                                    <tr>
                                        <td style="padding:18px 20px;">
                                            <div style="font-size:12px; color:#6b7280; text-transform:uppercase; letter-spacing:.06em;">From</div>
                                            <div style="font-size:17px; font-weight:700; margin-top:5px;">{safe_sender_name}</div>
                                            <a href="mailto:{safe_sender_email}" style="font-size:14px; color:#2563eb; text-decoration:none;">{safe_sender_email}</a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:12px 30px 8px;">
                                <div style="font-size:12px; color:#6b7280; text-transform:uppercase; letter-spacing:.06em; margin-bottom:10px;">Message</div>
                                <div style="font-size:15px; line-height:1.7; color:#374151;">
                                    {_html_paragraphs(message)}
                                </div>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:18px 30px 30px;">
                                <a href="{safe_reply_url}" style="display:inline-block; background:#2563eb; color:#ffffff; text-decoration:none; padding:12px 18px; border-radius:8px; font-weight:700;">Reply to sender</a>
                                <p style="margin:18px 0 0; font-size:12px; line-height:1.6; color:#6b7280;">
                                    This email was sent from the NoteNexus profile contact form. Replying opens an email to the sender.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </div>
    """


def send_simple_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    from_email: Optional[str] = None,
    reply_to: Optional[list[str]] = None,
) -> Dict[str, Any]:
    if not _validate_email(to_email):
        return {'success': False, 'message': 'Invalid recipient email address', 'error': 'invalid_email'}

    if not subject or not isinstance(subject, str):
        return {'success': False, 'message': 'Email subject is required', 'error': 'invalid_subject'}

    if not html_content or not isinstance(html_content, str):
        return {'success': False, 'message': 'Email HTML content is required', 'error': 'invalid_content'}

    config_check = _email_service_is_configured()
    if not config_check['success']:
        logger.error(config_check['message'])
        return config_check

    from_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', '')
    if not _validate_email(from_email):
        return {'success': False, 'message': 'Invalid sender email address', 'error': 'invalid_from_email'}

    try:
        connection = get_connection(fail_silently=False)
        email = EmailMultiAlternatives(
            subject=subject.strip(),
            body=text_content or '',
            from_email=from_email,
            to=[to_email.strip().lower()],
            reply_to=reply_to or None,
            connection=connection,
        )
        email.attach_alternative(html_content, 'text/html')
        sent_count = email.send()

        if sent_count:
            logger.info('Email sent successfully to %s', to_email)
            return {'success': True, 'message': 'Email sent successfully'}

        return {'success': False, 'message': 'Brevo did not accept the email.', 'error': 'not_sent'}
    except Exception as error:
        logger.exception('Exception sending email through Brevo SMTP: %s', error)
        return {'success': False, 'message': str(error), 'error': 'smtp_exception'}


def send_profile_contact_email(
    recipient_email: str,
    sender_name: str,
    sender_email: str,
    subject: str,
    message: str,
    from_email: Optional[str] = None,
) -> Dict[str, Any]:
    if not sender_name or not isinstance(sender_name, str):
        return {'success': False, 'message': 'Sender name is required', 'error': 'invalid_name'}
    if not _validate_email(sender_email):
        return {'success': False, 'message': 'Sender email address is invalid', 'error': 'invalid_sender_email'}
    if not message or not isinstance(message, str):
        return {'success': False, 'message': 'Message content is required', 'error': 'invalid_message'}
    if len(message.strip()) < 10:
        return {'success': False, 'message': 'Message must be at least 10 characters', 'error': 'message_too_short'}
    if len(message) > 5000:
        return {'success': False, 'message': 'Message cannot exceed 5000 characters', 'error': 'message_too_long'}

    sender_name = sender_name.strip()
    sender_email = sender_email.strip().lower()
    subject = subject.strip()
    message = message.strip()

    html_content = build_profile_email_html(sender_name, sender_email, subject, message)
    text_content = f"""New NoteNexus message

From: {sender_name} <{sender_email}>
Subject: {subject}

{message}

Reply to this message by emailing {sender_email}.
"""

    return send_simple_email(
        to_email=recipient_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
        from_email=from_email,
        reply_to=[sender_email],
    )


def send_confirmation_email(
    recipient_email: str,
    recipient_name: str,
    from_email: Optional[str] = None,
) -> Dict[str, Any]:
    recipient_name = recipient_name.strip() if recipient_name else 'User'
    safe_name = escape(recipient_name)

    html_content = f"""
    <div style="margin:0; padding:0; background:#f4f7fb; font-family:Arial, Helvetica, sans-serif; color:#1f2937;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f7fb; padding:28px 12px;">
            <tr>
                <td align="center">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:620px; background:#ffffff; border:1px solid #e5e7eb; border-radius:12px; overflow:hidden;">
                        <tr>
                            <td style="background:#16a34a; padding:24px 28px; color:#ffffff;">
                                <div style="font-size:13px; letter-spacing:.08em; text-transform:uppercase; opacity:.9;">Message Sent</div>
                                <h1 style="margin:8px 0 0; font-size:23px; line-height:1.3;">Your email was delivered to Brevo</h1>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:28px;">
                                <p style="margin:0 0 14px; font-size:16px;">Hi {safe_name},</p>
                                <p style="margin:0 0 14px; font-size:15px; line-height:1.7; color:#374151;">
                                    Your NoteNexus message has been sent. If the recipient replies, it will go to your account email address.
                                </p>
                                <p style="margin:18px 0 0; font-size:12px; color:#6b7280;">This is an automatic confirmation from NoteNexus.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </div>
    """

    text_content = f"""Hi {recipient_name},

Your NoteNexus message has been sent. If the recipient replies, it will go to your account email address.
"""

    return send_simple_email(
        to_email=recipient_email,
        subject='Your NoteNexus email was sent',
        html_content=html_content,
        text_content=text_content,
        from_email=from_email,
    )


def send_bulk_email(
    recipient_emails: list,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    from_email: Optional[str] = None,
) -> Dict[str, Any]:
    if not recipient_emails or not isinstance(recipient_emails, list):
        return {'success': False, 'message': 'Recipients list is required', 'error': 'invalid_recipients'}
    if len(recipient_emails) > 100:
        return {'success': False, 'message': 'Cannot send to more than 100 recipients at once', 'error': 'too_many_recipients'}

    stats = {'sent': 0, 'failed': 0, 'failed_emails': []}
    for email in recipient_emails:
        result = send_simple_email(
            to_email=email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            from_email=from_email,
        )
        if result.get('success'):
            stats['sent'] += 1
        else:
            stats['failed'] += 1
            stats['failed_emails'].append(email)

    return {
        'success': stats['failed'] == 0,
        'message': f'Sent to {stats["sent"]} recipients' + (f' ({stats["failed"]} failed)' if stats['failed'] else ''),
        'stats': stats,
    }
