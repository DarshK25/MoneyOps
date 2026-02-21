package com.moneyops.transactions.entity;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

@Document(collection = "transactions")
@Data
public class Transaction {
    @Id
    private UUID id = UUID.randomUUID();

    private UUID orgId;
    private UUID clientId;
    private UUID invoiceId;
    private TransactionType type;
    private BigDecimal amount;
    private String currency = "INR";
    private LocalDate transactionDate;
    private String category;
    private String description;
    private String paymentMethod;
    private String referenceNumber;
    private String aiCategory;
    private Float aiConfidence;
    private LocalDateTime createdAt = LocalDateTime.now();
    private LocalDateTime updatedAt = LocalDateTime.now();
    private UUID createdBy;
}
