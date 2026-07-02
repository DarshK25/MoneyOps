package com.moneyops.queue.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.moneyops.invoices.service.InvoiceService;
import com.moneyops.email.EmailService;
import com.moneyops.queue.RedisQueueConfig;
import com.moneyops.queue.RedisQueueService;
import com.moneyops.queue.worker.EmailWorker;
import com.moneyops.queue.worker.NotificationWorker;
import com.moneyops.queue.worker.PdfWorker;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.core.RedisTemplate;

import jakarta.annotation.PreDestroy;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Configuration
@RequiredArgsConstructor
@ConditionalOnProperty(name = "spring.redis.queues.enabled", havingValue = "true")
public class WorkerConfig {

    private final RedisQueueService queueService;
    private final RedisTemplate<String, String> redisTemplate;
    private final ObjectMapper objectMapper;
    private final RedisQueueConfig queueConfig;
    private final EmailService emailService;
    private final InvoiceService invoiceService;

    private final List<Thread> workerThreads = new ArrayList<>();

    @Bean
    public EmailWorker queueEmailWorker() {
        return new EmailWorker(queueService, redisTemplate, objectMapper, queueConfig, emailService);
    }

    @Bean
    public PdfWorker queuePdfWorker() {
        return new PdfWorker(queueService, redisTemplate, objectMapper, queueConfig, invoiceService);
    }

    @Bean
    public NotificationWorker queueNotificationWorker() {
        return new NotificationWorker(queueService, redisTemplate, objectMapper, queueConfig);
    }

    @Bean
    public WorkerManager workerManager(EmailWorker queueEmailWorker, 
                                      PdfWorker queuePdfWorker, 
                                      NotificationWorker queueNotificationWorker) {
        WorkerManager manager = new WorkerManager(queueEmailWorker, queuePdfWorker, queueNotificationWorker);
        manager.startWorkers();
        return manager;
    }

    public class WorkerManager {
        private final EmailWorker emailWorker;
        private final PdfWorker pdfWorker;
        private final NotificationWorker notificationWorker;

        public WorkerManager(EmailWorker emailWorker, 
                           PdfWorker pdfWorker, 
                           NotificationWorker notificationWorker) {
            this.emailWorker = emailWorker;
            this.pdfWorker = pdfWorker;
            this.notificationWorker = notificationWorker;
        }

        public void startWorkers() {
            startWorkerThread("email-worker", emailWorker);
            startWorkerThread("pdf-worker", pdfWorker);
            startWorkerThread("notification-worker", notificationWorker);
            log.info("All queue workers started");
        }

        private void startWorkerThread(String name, Runnable worker) {
            Thread thread = new Thread(worker, name);
            thread.setDaemon(true);
            thread.start();
            workerThreads.add(thread);
        }

        @PreDestroy
        public void stopWorkers() {
            log.info("Stopping all queue workers...");
            emailWorker.stop();
            pdfWorker.stop();
            notificationWorker.stop();

            for (Thread thread : workerThreads) {
                try {
                    thread.join(5000);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }
            log.info("All queue workers stopped");
        }
    }
}
