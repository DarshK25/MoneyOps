package com.moneyops.queue;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.moneyops.queue.dto.JobDto;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class RedisQueueService {

    private final RedisTemplate<String, String> redisTemplate;
    private final ObjectMapper objectMapper;
    private final RedisQueueConfig queueConfig;

    public String pushJob(String queueName, String type, Map<String, Object> payload) {
        if (!queueConfig.isQueuesEnabled()) {
            log.warn("Redis queues are disabled. Job not pushed to {}", queueName);
            return null;
        }

        JobDto job = JobDto.builder()
                .jobId(UUID.randomUUID().toString())
                .type(type)
                .payload(payload)
                .status("PENDING")
                .createdAt(LocalDateTime.now())
                .retries(0)
                .build();

        try {
            String jobJson = objectMapper.writeValueAsString(job);
            redisTemplate.opsForList().leftPush(queueName, jobJson);
            log.info("Pushed job {} to queue {}", job.getJobId(), queueName);
            return job.getJobId();
        } catch (JsonProcessingException e) {
            log.error("Failed to serialize job for queue {}", queueName, e);
            throw new RuntimeException("Failed to push job to queue", e);
        }
    }

    public JobDto popJob(String queueName, int timeoutSeconds) {
        if (!queueConfig.isQueuesEnabled()) {
            log.warn("Redis queues are disabled. Cannot pop from {}", queueName);
            return null;
        }

        try {
            List<String> result = redisTemplate.opsForList().rightPop(queueName, timeoutSeconds);
            if (result == null || result.isEmpty()) {
                return null;
            }

            String jobJson = result.get(0);
            JobDto job = objectMapper.readValue(jobJson, JobDto.class);
            log.info("Popped job {} from queue {}", job.getJobId(), queueName);
            return job;
        } catch (JsonProcessingException e) {
            log.error("Failed to deserialize job from queue {}", queueName, e);
            return null;
        }
    }

    public JobDto popJob(String queueName) {
        return popJob(queueName, 5);
    }

    public Long getQueueSize(String queueName) {
        if (!queueConfig.isQueuesEnabled()) {
            return 0L;
        }
        return redisTemplate.opsForList().size(queueName);
    }

    public void pushToDeadLetterQueue(String queueName, JobDto job) {
        String dlqName = queueName + ":dlq";
        try {
            String jobJson = objectMapper.writeValueAsString(job);
            redisTemplate.opsForList().leftPush(dlqName, jobJson);
            log.warn("Job {} moved to DLQ {}", job.getJobId(), dlqName);
        } catch (JsonProcessingException e) {
            log.error("Failed to push job to DLQ", e);
        }
    }

    public List<String> getQueueJobs(String queueName, int maxJobs) {
        if (!queueConfig.isQueuesEnabled()) {
            return Collections.emptyList();
        }
        return redisTemplate.opsForList().range(queueName, 0, maxJobs - 1);
    }
}
