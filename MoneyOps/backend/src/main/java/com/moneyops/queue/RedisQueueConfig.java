package com.moneyops.queue;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RedisQueueConfig {

    @Value("${spring.redis.queues.enabled:false}")
    private boolean queuesEnabled;

    public static final String QUEUE_EMAIL = "moneyops:queue:email";
    public static final String QUEUE_PDF = "moneyops:queue:pdf";
    public static final String QUEUE_TREDS = "moneyops:queue:treds";
    public static final String QUEUE_NOTIFICATION = "moneyops:queue:notification";

    public boolean isQueuesEnabled() {
        return queuesEnabled;
    }
}
