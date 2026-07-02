package com.moneyops.invoices.entity;

import lombok.Data;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

@Document(collection = "recurring_invoices")
@Data
public class RecurringInvoice {

    @Id
    private String id;

    private String orgId;

    private String clientId;
    private String clientName;
    private String clientEmail;
    private String clientCompany;
    private String clientPhone;

    private String frequency; // DAILY, WEEKLY, MONTHLY, YEARLY
    private Integer interval = 1; // every 1 month, every 2 weeks, etc.

    private LocalDate startDate;
    private LocalDate endDate; // nullable (infinite)

    private LocalDate lastGenerated;
    private Boolean isActive = true;

    private List<InvoiceItem> items;
    private String currency;
    private Integer paymentTerms = 30;
    private String notes;

    @CreatedDate
    private LocalDateTime createdAt;

    @LastModifiedDate
    private LocalDateTime updatedAt;
}
