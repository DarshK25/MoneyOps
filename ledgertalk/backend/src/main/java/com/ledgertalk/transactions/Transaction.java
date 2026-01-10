// src/main/java/com/ledgertalk/transactions/Transaction.java
package com.ledgertalk.transactions;

import jakarta.persistence.*;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "transactions")
@Data
public class Transaction {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private Long organizationId;
    
    private Long clientId; // null if expense
    
    private Long invoiceId; // null if not related to invoice
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private TransactionType type; // INCOME or EXPENSE
    
    @Column(nullable = false)
    private BigDecimal amount;
    
    @Column(nullable = false)
    private String currency = "INR";
    
    @Column(nullable = false)
    private LocalDate transactionDate;
    
    @Column(nullable = false)
    private String category; // e.g., "Payment Received", "Office Rent", "Salary"
    
    @Column(columnDefinition = "TEXT")
    private String description;
    
    private String paymentMethod; // e.g., "Bank Transfer", "Cash", "UPI"
    
    private String referenceNumber; // Transaction ID, Check number, etc.
    
    // AI classification
    private String aiCategory; // AI suggested category
    private Float aiConfidence; // 0.0 to 1.0
    
    @Column(nullable = false)
    private LocalDateTime createdAt = LocalDateTime.now();
}