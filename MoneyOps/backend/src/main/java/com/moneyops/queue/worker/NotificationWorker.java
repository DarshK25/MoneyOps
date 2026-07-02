package com.moneyops.queue.worker;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.moneyops.queue.RedisQueueConfig;
import com.moneyops.queue.RedisQueueService;
import com.moneyops.queue.dto.JobDto;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;

import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;

@Slf4j
public class NotificationWorker extends BaseWorker {

    private final HttpClient httpClient = HttpClient.newHttpClient();

    public NotificationWorker(RedisQueueService queueService,
                               RedisTemplate<String, String> redisTemplate,
                               ObjectMapper objectMapper,
                               RedisQueueConfig queueConfig) {
        super(queueService, redisTemplate, objectMapper, queueConfig,
                RedisQueueConfig.QUEUE_NOTIFICATION, 5);
    }

    @Override
    protected void processJob(JobDto job) {
        try {
            Map<String, Object> payload = job.getPayload();
            String type = job.getType();

            job.setStatus("PROCESSING");
            job.setStartedAt(java.time.LocalDateTime.now());

            switch (type) {
                case "WHATSAPP_NOTIFICATION":
                    processWhatsAppNotification(payload);
                    break;
                case "IN_APP_NOTIFICATION":
                    processInAppNotification(payload);
                    break;
                default:
                    log.warn("Unknown notification job type: {}", type);
            }

            markJobCompleted(job);

        } catch (Exception e) {
            log.error("Failed to process notification job {}", job.getJobId(), e);
            markJobFailed(job, e);
        }
    }

    private void processWhatsAppNotification(Map<String, Object> payload) {
        String to = (String) payload.get("to");
        String message = (String) payload.get("message");
        if (to == null || to.isBlank() || message == null || message.isBlank()) {
            throw new IllegalArgumentException("Missing to or message in WhatsApp notification payload");
        }

        String accountSid = System.getenv("TWILIO_ACCOUNT_SID");
        String authToken = System.getenv("TWILIO_AUTH_TOKEN");
        String from = System.getenv().getOrDefault("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886");

        if (accountSid == null || accountSid.isBlank() || authToken == null || authToken.isBlank()) {
            throw new IllegalStateException("Twilio WhatsApp credentials are not configured");
        }

        String toNumber = to.startsWith("whatsapp:") ? to : "whatsapp:" + to;
        String body = "From=" + encode(from)
                + "&To=" + encode(toNumber)
                + "&Body=" + encode(message);
        String auth = Base64.getEncoder().encodeToString((accountSid + ":" + authToken).getBytes(StandardCharsets.UTF_8));

        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create("https://api.twilio.com/2010-04-01/Accounts/" + accountSid + "/Messages.json"))
                    .header("Authorization", "Basic " + auth)
                    .header("Content-Type", "application/x-www-form-urlencoded")
                    .POST(HttpRequest.BodyPublishers.ofString(body))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() < 200 || response.statusCode() >= 300) {
                throw new IllegalStateException("Twilio WhatsApp send failed: " + response.statusCode() + " " + response.body());
            }
            log.info("Sent WhatsApp notification to {}", to);
        } catch (Exception e) {
            throw new IllegalStateException("Twilio WhatsApp send failed", e);
        }
    }

    private void processInAppNotification(Map<String, Object> payload) {
        String userId = (String) payload.get("userId");
        String orgId = (String) payload.get("orgId");
        String message = (String) payload.get("message");
        if (userId == null || userId.isBlank() || orgId == null || orgId.isBlank() || message == null || message.isBlank()) {
            throw new IllegalArgumentException("Missing userId, orgId, or message in in-app notification payload");
        }

        try {
            Map<String, Object> notification = new HashMap<>();
            notification.put("userId", userId);
            notification.put("orgId", orgId);
            notification.put("message", message);
            notification.put("type", payload.getOrDefault("notificationType", "INFO"));
            notification.put("createdAt", LocalDateTime.now().toString());
            notification.put("read", false);

            String key = "moneyops:notifications:" + orgId + ":" + userId;
            redisTemplate.opsForList().leftPush(key, objectMapper.writeValueAsString(notification));
            redisTemplate.opsForList().trim(key, 0, 99);
            log.info("Stored in-app notification for user {} in org {}", userId, orgId);
        } catch (Exception e) {
            throw new IllegalStateException("Failed to store in-app notification", e);
        }
    }

    private static String encode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }
}
