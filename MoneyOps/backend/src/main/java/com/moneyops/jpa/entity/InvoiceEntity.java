package com.moneyops.jpa.entity;

import com.moneyops.jpa.converter.StringToUuidConverter;
import jakarta.persistence.*;
import lombok.Data;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.math.BigDecimal;
import java.time.LocalDate;
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

    @Column(name = "issue_date")
    private LocalDate issueDate;

    @Column(name = "due_date")
    private LocalDate dueDate;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "document_data")
    private String documentData;
}
