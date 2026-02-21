package com.moneyops.invoices.entity;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.math.BigDecimal;
import java.util.UUID;

@Document(collection = "invoice_items")
@Data
public class InvoiceItem {
    @Id
    private UUID id = UUID.randomUUID();

    private UUID invoiceId;
    private ItemType type;
    private String description;
    private Integer quantity;
    private BigDecimal rate;
    private BigDecimal gstPercent;
    private BigDecimal lineSubtotal;
    private BigDecimal lineGst;
    private BigDecimal lineTotal;

    public enum ItemType {
        PRODUCT,
        SERVICE
    }
}
