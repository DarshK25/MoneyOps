package com.moneyops.jpa.entity;

import com.moneyops.jpa.converter.StringToUuidConverter;
import jakarta.persistence.*;
import lombok.Data;

import java.time.LocalDateTime;

@Entity
@Table(name = "organizations")
@Data
public class OrganizationEntity {

    @Id
    @Convert(converter = StringToUuidConverter.class)
    private String id;

    private String name;

    @Column(name = "business_type")
    private String businessType;

    private String gstin;

    private String pan;

    @Column(columnDefinition = "jsonb")
    private String settings;

    @Column(name = "created_by")
    private String createdBy;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
