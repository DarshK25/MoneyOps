package com.moneyops.jpa.entity;

import com.moneyops.jpa.converter.StringToUuidConverter;
import jakarta.persistence.*;
import lombok.Data;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;

@Entity
@Table(name = "clients")
@Data
public class ClientEntity {

    @Id
    @Convert(converter = StringToUuidConverter.class)
    private String id;

    @Column(name = "org_id")
    @Convert(converter = StringToUuidConverter.class)
    private String orgId;

    private String name;

    private String gstin;

    private String email;

    @Column(name = "phone_number")
    private String phoneNumber;

    private String company;

    private String currency;

    private String notes;

    private String status;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Column(name = "created_by")
    private String createdBy;

    @Column(name = "updated_by")
    private String updatedBy;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "document_data")
    private String documentData;
}
