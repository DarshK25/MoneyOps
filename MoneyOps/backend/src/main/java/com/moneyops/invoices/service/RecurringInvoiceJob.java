package com.moneyops.invoices.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
public class RecurringInvoiceJob {

    private final RecurringInvoiceService recurringInvoiceService;

    @Scheduled(cron = "0 0 1 * * *") // Run daily at 1 AM
    public void processRecurringInvoices() {
        log.info("Starting recurring invoice job...");
        try {
            recurringInvoiceService.processDueRecurringInvoices();
            log.info("Recurring invoice job completed successfully.");
        } catch (Exception e) {
            log.error("Error processing recurring invoices: {}", e.getMessage(), e);
        }
    }
}
