package com.moneyops.invoices.dto;

import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

@Data
public class RecurringInvoiceDto {
    private String id;
    private String orgId;
    private String clientId;
    private String clientName;
    private String clientEmail;
    private String clientCompany;
    private String clientPhone;
    private String frequency;
    private Integer interval;
    private LocalDate startDate;
    private LocalDate endDate;
    private LocalDate lastGenerated;
    private Boolean isActive;
    private List<InvoiceItemDto> items;
    private String currency;
    private Integer paymentTerms;
    private String notes;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private LocalDate nextGenerationDate;
}
