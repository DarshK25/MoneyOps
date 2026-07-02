import os
import json
import logging
from redis_worker import BaseRedisWorker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NotificationWorker(BaseRedisWorker):
    def __init__(self, redis_host='localhost', redis_port=6379):
        super().__init__(redis_host, redis_port, queue_name='moneyops:queue:notification', poll_timeout=5)
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        self.twilio_whatsapp_from = os.getenv('TWILIO_WHATSAPP_FROM', '')

    def process_job(self, job):
        job_type = job.get('type', '')
        payload = job.get('payload', {})

        if job_type == 'WHATSAPP_NOTIFICATION':
            self.send_whatsapp_notification(payload)
        elif job_type == 'IN_APP_NOTIFICATION':
            self.send_in_app_notification(payload)
        else:
            logger.warning(f"Unknown notification job type: {job_type}")

    def send_whatsapp_notification(self, payload):
        to = payload.get('to')
        message = payload.get('message', '')

        if not self.twilio_account_sid or not self.twilio_auth_token:
            logger.warning("Twilio credentials not configured. WhatsApp notification not sent.")
            return

        try:
            from twilio.rest import Client
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            message = client.messages.create(
                from_=f'whatsapp:{self.twilio_whatsapp_from}',
                body=message,
                to=f'whatsapp:{to}'
            )
            logger.info(f"WhatsApp message sent: {message.sid}")
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")

    def send_in_app_notification(self, payload):
        user_id = payload.get('userId')
        org_id = payload.get('orgId')
        message = payload.get('message', '')

        logger.info(f"In-app notification for user {user_id} in org {org_id}: {message}")
        # TODO: Store in database or push via WebSocket


if __name__ == '__main__':
    worker = NotificationWorker(
        redis_host=os.getenv('REDIS_HOST', 'localhost'),
        redis_port=int(os.getenv('REDIS_PORT', 6379))
    )
    try:
        worker.run()
    except KeyboardInterrupt:
        worker.stop()
