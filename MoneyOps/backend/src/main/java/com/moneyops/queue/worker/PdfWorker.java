package com.moneyops.queue.worker;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.moneyops.invoices.service.InvoiceService;
import com.moneyops.queue.RedisQueueConfig;
import com.moneyops.queue.RedisQueueService;
import com.moneyops.queue.dto.JobDto;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;

import java.time.Duration;
import java.util.Base64;
import java.util.Map;

@Slf4j
public class PdfWorker extends BaseWorker {

    private final InvoiceService invoiceService;

    public PdfWorker(RedisQueueService queueService,
                     RedisTemplate<String, String> redisTemplate,
                     ObjectMapper objectMapper,
                     RedisQueueConfig queueConfig,
                     InvoiceService invoiceService) {
        super(queueService, redisTemplate, objectMapper, queueConfig,
                RedisQueueConfig.QUEUE_PDF, 5);
        this.invoiceService = invoiceService;
    }

    @Override
    protected void processJob(JobDto job) {
        try {
            Map<String, Object> payload = job.getPayload();
            String type = job.getType();

            job.setStatus("PROCESSING");
            job.setStartedAt(java.time.LocalDateTime.now());

            switch (type) {
                case "INVOICE_PDF":
                    processInvoicePdf(payload);
                    break;
                default:
                    log.warn("Unknown PDF job type: {}", type);
            }

            markJobCompleted(job);

        } catch (Exception e) {
            log.error("Failed to process PDF job {}", job.getJobId(), e);
            markJobFailed(job, e);
        }
    }

    private void processInvoicePdf(Map<String, Object> payload) {
        String invoiceId = (String) payload.get("invoiceId");
        String orgId = (String) payload.get("orgId");

        if (invoiceId == null || orgId == null) {
            throw new IllegalArgumentException("Missing invoiceId or orgId in PDF job payload");
        }

        byte[] pdfBytes = invoiceService.generateInvoicePdf(invoiceId, orgId);
        String key = "moneyops:pdf:" + orgId + ":" + invoiceId;
        redisTemplate.opsForValue().set(key, Base64.getEncoder().encodeToString(pdfBytes), Duration.ofHours(24));

        Map<String, Object> notification = new java.util.HashMap<>();
        notification.put("orgId", orgId);
        notification.put("userId", payload.get("userId"));
        notification.put("message", "Invoice PDF is ready for download");
        notification.put("notificationType", "PDF_READY");
        notification.put("invoiceId", invoiceId);
        notification.put("pdfCacheKey", key);
        if (payload.get("userId") != null) {
            queueService.pushJob(RedisQueueConfig.QUEUE_NOTIFICATION, "IN_APP_NOTIFICATION", notification);
        }

        log.info("Generated and cached PDF for invoice {} ({} bytes)", invoiceId, pdfBytes.length);
    }
}
