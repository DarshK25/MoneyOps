package com.moneyops.jpa.entity;

import com.moneyops.jpa.converter.StringToUuidConverter;
import jakarta.persistence.*;
import lombok.Data;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "organizations")
@Data
public class OrganizationEntity {

    @Id
    @Convert(converter = StringToUuidConverter.class)
    private String id;

    @Column(name = "name")
    private String name;

    @Column(name = "legal_name")
    private String legalName;

    @Column(name = "trading_name")
    private String tradingName;

    @Column(name = "business_type")
    private String businessType;

    private String industry;

    @Column(name = "primary_email")
    private String primaryEmail;

    @Column(name = "primary_phone")
    private String primaryPhone;

    private String website;

    @Column(name = "registered_address")
    private String registeredAddress;

    @Column(name = "registration_date")
    private LocalDate registrationDate;

    @Column(name = "employee_count")
    private Integer employeeCount;

    @Column(name = "annual_turnover")
    private String annualTurnover;

    private String pincode;

    @Column(name = "gst_registered")
    private Boolean gstRegistered;

    @Column(name = "verification_tier")
    private String verificationTier;

    @Column(name = "team_action_code_hash")
    private String teamActionCodeHash;

    private String gstin;

    @Column(name = "gst_filing_frequency")
    private String gstFilingFrequency;

    @Column(name = "pan_number")
    private String panNumber;

    @Column(name = "tan_number")
    private String tanNumber;

    private String cin;

    private String llpin;

    @Column(name = "msme_number")
    private String msmeNumber;

    @Column(name = "iec_code")
    private String iecCode;

    @Column(name = "professional_tax_reg")
    private String professionalTaxReg;

    @Column(name = "state_of_registration")
    private String stateOfRegistration;

    @Column(name = "created_by")
    private String createdBy;

    @Column(name = "updated_by")
    private String updatedBy;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    @JdbcTypeCode(SqlTypes.JSON)
    private String settings;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    public String getName() {
        return name != null ? name : legalName;
    }
}
