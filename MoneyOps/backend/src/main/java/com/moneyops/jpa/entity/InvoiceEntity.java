package com.moneyops.jpa.entity;

import com.moneyops.jpa.converter.StringToUuidConverter;
import jakarta.persistence.*;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "invoices")
@Data
public class InvoiceEntity {

    @Id
    @Convert(converter = StringToUuidConverter.class)
    private String id;

    @Column(name = "org_id")
    @Convert(converter = StringToUuidConverter.class)
    private String orgId;

    @Column(name = "client_id")
    @Convert(converter = StringToUuidConverter.class)
    private String clientId;

    @Column(name = "invoice_number")
    private String invoiceNumber;

    private String status;

    @Column(name = "total_amount")
    private BigDecimal totalAmount;

    @Column(name = "created_at")
    private LocalDateTime createdAt;
}
