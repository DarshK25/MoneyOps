package com.moneyops.queue.worker;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.moneyops.email.EmailService;
import com.moneyops.queue.RedisQueueConfig;
import com.moneyops.queue.RedisQueueService;
import com.moneyops.queue.dto.JobDto;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;

import java.util.Map;

@Slf4j
public class EmailWorker extends BaseWorker {

    private final EmailService emailService;

    public EmailWorker(RedisQueueService queueService,
                       RedisTemplate<String, String> redisTemplate,
                       ObjectMapper objectMapper,
                       RedisQueueConfig queueConfig,
                       EmailService emailService) {
        super(queueService, redisTemplate, objectMapper, queueConfig,
                RedisQueueConfig.QUEUE_EMAIL, 5);
        this.emailService = emailService;
    }

    @Override
    protected void processJob(JobDto job) {
        try {
            Map<String, Object> payload = job.getPayload();
            String type = job.getType();

            job.setStatus("PROCESSING");
            job.setStartedAt(java.time.LocalDateTime.now());

            switch (type) {
                case "INVOICE_EMAIL":
                    processInvoiceEmail(payload);
                    break;
                case "INVOICE_FOLLOWUP":
                    processInvoiceFollowUp(payload);
                    break;
                case "INVITE_EMAIL":
                    processInviteEmail(payload);
                    break;
                default:
                    log.warn("Unknown email job type: {}", type);
            }

            markJobCompleted(job);

        } catch (Exception e) {
            log.error("Failed to process email job {}", job.getJobId(), e);
            markJobFailed(job, e);
        }
    }

    private void processInvoiceEmail(Map<String, Object> payload) {
        String toEmail = (String) payload.get("toEmail");
        String subject = (String) payload.get("subject");
        String htmlContent = (String) payload.get("htmlContent");
        emailService.sendInvoiceEmail(toEmail, subject, htmlContent);
        log.info("Sent invoice email to {}", toEmail);
    }

    private void processInvoiceFollowUp(Map<String, Object> payload) {
        String toEmail = (String) payload.get("toEmail");
        String invoiceNumber = (String) payload.get("invoiceNumber");
        String clientName = (String) payload.get("clientName");
        String orgName = (String) payload.get("orgName");
        String dueDate = (String) payload.get("dueDate");
        String amount = (String) payload.get("amount");
        emailService.sendInvoiceFollowUp(toEmail, invoiceNumber, clientName, orgName, dueDate, amount);
        log.info("Sent follow-up email to {}", toEmail);
    }

    private void processInviteEmail(Map<String, Object> payload) {
        String toEmail = (String) payload.get("toEmail");
        String token = (String) payload.get("token");
        String orgName = (String) payload.get("orgName");
        String role = (String) payload.get("role");
        emailService.sendInviteEmail(toEmail, token, orgName, role);
        log.info("Sent invite email to {}", toEmail);
    }
}
