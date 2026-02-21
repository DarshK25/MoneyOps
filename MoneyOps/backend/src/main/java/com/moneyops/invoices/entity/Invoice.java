package com.moneyops.invoices.entity;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

@Document(collection = "invoices")
@Data
public class Invoice {
    @Id
    private UUID id = UUID.randomUUID();

    private UUID orgId;
    @Indexed(unique = true)
    private String invoiceNumber;
    private UUID clientId;
    private LocalDate issueDate;
    private LocalDate dueDate;
    private InvoiceStatus status = InvoiceStatus.DRAFT;
    private BigDecimal subtotal;
    private BigDecimal gstTotal;
    private BigDecimal totalAmount;
    private String currency = "INR";
    private LocalDate paymentDate;
    private String notes;
    private LocalDateTime createdAt = LocalDateTime.now();
    private LocalDateTime updatedAt = LocalDateTime.now();
    private UUID createdBy;

    public enum InvoiceStatus {
        DRAFT, SENT, PAID, OVERDUE, CANCELLED
    }
}
