import redis
import json
import time
import logging
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BaseRedisWorker(ABC):
    def __init__(self, redis_host='localhost', redis_port=6379, queue_name='', poll_timeout=5):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.queue_name = queue_name
        self.poll_timeout = poll_timeout
        self.running = True
        self.max_retries = 3

    @abstractmethod
    def process_job(self, job_data):
        pass

    def run(self):
        logger.info(f"Starting worker for queue: {self.queue_name}")
        while self.running:
            try:
                result = self.redis_client.brpop(self.queue_name, self.poll_timeout)
                if result is None:
                    continue

                _, job_json = result
                job = json.loads(job_json)
                job_id = job.get('jobId', 'unknown')

                logger.info(f"Processing job {job_id} from {self.queue_name}")
                job['status'] = 'PROCESSING'
                job['startedAt'] = time.time()

                try:
                    self.process_job(job)
                    job['status'] = 'COMPLETED'
                    job['completedAt'] = time.time()
                    logger.info(f"Job {job_id} completed successfully")
                except Exception as e:
                    logger.error(f"Job {job_id} failed: {e}")
                    job['retries'] = job.get('retries', 0) + 1
                    job['errorMessage'] = str(e)

                    if job['retries'] >= self.max_retries:
                        job['status'] = 'FAILED'
                        dlq_name = f"{self.queue_name}:dlq"
                        self.redis_client.lpush(dlq_name, json.dumps(job))
                        logger.error(f"Job {job_id} moved to DLQ after {job['retries']} retries")
                    else:
                        job['status'] = 'PENDING'
                        backoff = 2 ** job['retries']
                        logger.warning(f"Job {job_id} retry {job['retries']}/{self.max_retries} after {backoff}s")
                        time.sleep(backoff)
                        self.redis_client.lpush(self.queue_name, json.dumps(job))

            except redis.RedisError as e:
                logger.error(f"Redis error: {e}")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(1)

    def stop(self):
        self.running = False
        logger.info(f"Stopping worker for queue: {self.queue_name}")


if __name__ == '__main__':
    import os
    worker = BaseRedisWorker(
        redis_host=os.getenv('REDIS_HOST', 'localhost'),
        redis_port=int(os.getenv('REDIS_PORT', 6379))
    )
    try:
        worker.run()
    except KeyboardInterrupt:
        worker.stop()
