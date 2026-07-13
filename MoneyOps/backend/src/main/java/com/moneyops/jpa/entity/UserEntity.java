package com.moneyops.jpa.entity;

import com.moneyops.jpa.converter.StringToUuidConverter;
import jakarta.persistence.*;
import lombok.Data;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;

@Entity
@Table(name = "users")
@Data
public class UserEntity {

    @Id
    @Convert(converter = StringToUuidConverter.class)
    private String id;

    @Column(name = "legacy_mongo_id")
    private String legacyMongoId;

    private String email;

    private String name;

    @Column(name = "org_id")
    @Convert(converter = StringToUuidConverter.class)
    private String orgId;

    private String role;

    private String status;

    private String phone;

    @Column(name = "onboarding_complete")
    private Boolean onboardingComplete;

    @Column(name = "last_login_at")
    private LocalDateTime lastLoginAt;

    @Column(name = "password_hash")
    private String passwordHash;

    @Column(name = "created_by")
    private String createdBy;

    @Column(name = "updated_by")
    private String updatedBy;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    @JdbcTypeCode(SqlTypes.JSON)
    private String preferences;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
