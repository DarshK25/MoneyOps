import os
import json
import logging
from redis_worker import BaseRedisWorker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EmailWorker(BaseRedisWorker):
    def __init__(self, redis_host='localhost', redis_port=6379):
        super().__init__(redis_host, redis_port, queue_name='moneyops:queue:email', poll_timeout=5)
        self.resend_api_key = os.getenv('RESEND_API_KEY', '')
        self.brevo_api_key = os.getenv('BREVO_API_KEY', '')

    def process_job(self, job):
        job_type = job.get('type', '')
        payload = job.get('payload', {})

        if job_type == 'INVOICE_EMAIL':
            self.send_invoice_email(payload)
        elif job_type == 'INVOICE_FOLLOWUP':
            self.send_followup_email(payload)
        elif job_type == 'INVITE_EMAIL':
            self.send_invite_email(payload)
        else:
            logger.warning(f"Unknown email job type: {job_type}")

    def send_invoice_email(self, payload):
        to_email = payload.get('toEmail')
        subject = payload.get('subject')
        html_content = payload.get('htmlContent')
        logger.info(f"Sending invoice email to {to_email}")
        self._send_email(to_email, subject, html_content)

    def send_followup_email(self, payload):
        to_email = payload.get('toEmail')
        invoice_number = payload.get('invoiceNumber')
        client_name = payload.get('clientName', 'there')
        org_name = payload.get('orgName', 'MoneyOps')
        due_date = payload.get('dueDate', 'N/A')
        amount = payload.get('amount', '0.00')

        subject = f"Reminder: Invoice {invoice_number} is overdue"
        html = f"""
        <div style='font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px;'>
            <h2 style='color: #E53E3E;'>Payment Reminder</h2>
            <p>Dear {client_name},</p>
            <p>This is a friendly reminder that your invoice <strong>{invoice_number}</strong> 
               from {org_name} is past its due date.</p>
            <div style='background-color: #f9f9f9; padding: 16px; border-radius: 8px; margin: 20px 0;'>
                <p>Invoice Number: <strong>{invoice_number}</strong></p>
                <p>Due Date: <strong>{due_date}</strong></p>
                <p>Amount Due: <strong>{amount}</strong></p>
            </div>
            <p>Please arrange payment at your earliest convenience.</p>
        </div>
        """
        logger.info(f"Sending follow-up email to {to_email}")
        self._send_email(to_email, subject, html)

    def send_invite_email(self, payload):
        to_email = payload.get('toEmail')
        token = payload.get('token')
        org_name = payload.get('orgName', 'MoneyOps')
        role = payload.get('role', 'MEMBER')
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        invite_link = f"{frontend_url}/invite/{token}"

        subject = f"You're invited to {org_name}"
        html = f"""
        <div style='font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px;'>
            <h2>You've been invited to {org_name}</h2>
            <p>You have been added as a <strong>{role}</strong>.</p>
            <a href='{invite_link}' style='display:inline-block; padding: 12px 24px; 
               background-color: #4CBB17; color: white; text-decoration: none; border-radius: 6px;'>
               Accept Invitation</a>
        </div>
        """
        logger.info(f"Sending invite email to {to_email}")
        self._send_email(to_email, subject, html)

    def _send_email(self, to, subject, html_content):
        if self.resend_api_key:
            self._send_via_resend(to, subject, html_content)
        elif self.brevo_api_key:
            self._send_via_brevo(to, subject, html_content)
        else:
            logger.warning("No email provider configured. Email not sent.")

    def _send_via_resend(self, to, subject, html):
        try:
            import requests
            response = requests.post(
                'https://api.resend.com/emails',
                headers={
                    'Authorization': f'Bearer {self.resend_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'from': os.getenv('EMAIL_FROM_ADDRESS', 'onboarding@resend.dev'),
                    'to': to,
                    'subject': subject,
                    'html': html
                }
            )
            if response.status_code == 200:
                logger.info(f"Email sent via Resend to {to}")
            else:
                logger.error(f"Resend error: {response.text}")
        except Exception as e:
            logger.error(f"Failed to send via Resend: {e}")

    def _send_via_brevo(self, to, subject, html):
        try:
            import requests
            response = requests.post(
                'https://api.brevo.com/v3/smtp/email',
                headers={
                    'api-key': self.brevo_api_key,
                    'Content-Type': 'application/json'
                },
                json={
                    'sender': {'email': os.getenv('EMAIL_FROM_ADDRESS', 'noreply@moneyops.app')},
                    'to': [{'email': to}],
                    'subject': subject,
                    'htmlContent': html
                }
            )
            if response.status_code == 201:
                logger.info(f"Email sent via Brevo to {to}")
            else:
                logger.error(f"Brevo error: {response.text}")
        except Exception as e:
            logger.error(f"Failed to send via Brevo: {e}")


if __name__ == '__main__':
    worker = EmailWorker(
        redis_host=os.getenv('REDIS_HOST', 'localhost'),
        redis_port=int(os.getenv('REDIS_PORT', 6379))
    )
    try:
        worker.run()
    except KeyboardInterrupt:
        worker.stop()
