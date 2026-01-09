// src/main/java/com/ledgertalk/invoices/InvoiceStatus.java
package com.ledgertalk.invoices;

public enum InvoiceStatus {
    DRAFT,
    SENT,
    VIEWED,
    PARTIALLY_PAID,
    PAID,
    OVERDUE,
    CANCELLED
}