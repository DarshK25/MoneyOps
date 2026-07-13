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
@Table(name = "transactions")
@Data
public class TransactionEntity {

    @Id
    @Convert(converter = StringToUuidConverter.class)
    private String id;

    @Column(name = "org_id")
    @Convert(converter = StringToUuidConverter.class)
    private String orgId;

    @Column(name = "invoice_id")
    @Convert(converter = StringToUuidConverter.class)
    private String invoiceId;

    @Column(name = "client_id")
    @Convert(converter = StringToUuidConverter.class)
    private String clientId;

    private String type;

    private BigDecimal amount;

    @Column(name = "transaction_date")
    private LocalDate transactionDate;

    private String currency;

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
