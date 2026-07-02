package com.moneyops.queue.worker;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.moneyops.queue.RedisQueueConfig;
import com.moneyops.queue.RedisQueueService;
import com.moneyops.queue.dto.JobDto;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;

import java.time.LocalDateTime;

@Slf4j
public abstract class BaseWorker implements Runnable {

    protected final RedisQueueService queueService;
    protected final RedisTemplate<String, String> redisTemplate;
    protected final ObjectMapper objectMapper;
    protected final RedisQueueConfig queueConfig;
    protected final String queueName;
    protected final int pollTimeout;

    protected volatile boolean running = true;

    protected BaseWorker(RedisQueueService queueService,
                         RedisTemplate<String, String> redisTemplate,
                         ObjectMapper objectMapper,
                         RedisQueueConfig queueConfig,
                         String queueName,
                         int pollTimeout) {
        this.queueService = queueService;
        this.redisTemplate = redisTemplate;
        this.objectMapper = objectMapper;
        this.queueConfig = queueConfig;
        this.queueName = queueName;
        this.pollTimeout = pollTimeout;
    }

    @Override
    public void run() {
        log.info("Worker {} started for queue {}", this.getClass().getSimpleName(), queueName);

        while (running && queueConfig.isQueuesEnabled()) {
            try {
                JobDto job = queueService.popJob(queueName, pollTimeout);

                if (job == null) {
                    continue;
                }

                processJob(job);

            } catch (Exception e) {
                log.error("Worker {} error", this.getClass().getSimpleName(), e);
            }
        }

        log.info("Worker {} stopped", this.getClass().getSimpleName());
    }

    protected abstract void processJob(JobDto job);

    protected void markJobCompleted(JobDto job) {
        job.setStatus("COMPLETED");
        job.setCompletedAt(LocalDateTime.now());
        log.info("Job {} completed", job.getJobId());
    }

    protected void markJobFailed(JobDto job, Exception e) {
        job.setRetries(job.getRetries() + 1);
        job.setErrorMessage(e.getMessage());

        if (job.getRetries() >= getMaxRetries()) {
            job.setStatus("FAILED");
            job.setCompletedAt(LocalDateTime.now());
            queueService.pushToDeadLetterQueue(queueName, job);
            log.error("Job {} failed after {} retries, moved to DLQ", job.getJobId(), job.getRetries());
        } else {
            job.setStatus("PENDING");
            long backoffSeconds = (long) (Math.pow(2, job.getRetries()) * 1000);
            log.warn("Job {} failed, retry {}/{} after {}ms", job.getJobId(), job.getRetries(), getMaxRetries(), backoffSeconds);

            try {
                Thread.sleep(backoffSeconds);
                queueService.pushJob(queueName, job.getType(), job.getPayload());
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
            }
        }
    }

    protected int getMaxRetries() {
        return 3;
    }

    public void stop() {
        this.running = false;
    }
}
