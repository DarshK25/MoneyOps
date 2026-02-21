package com.moneyops.organizations.entity;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

@Document(collection = "business_organizations")
@Data
public class BusinessOrganization {
    @Id
    private UUID id = UUID.randomUUID();

    private String legalName;
    private String tradingName;
    private BusinessType businessType;
    private Industry industry;
    private LocalDate registrationDate;
    private TurnoverRange annualTurnoverRange;
    private String primaryEmail;
    private String primaryPhone;
    private String website;
    private Integer employeeCount;
    private String registeredAddress;
    private Month financialYearStartMonth;
    private String preferredLanguage;
    private String primaryActivity;
    private TargetMarket targetMarket;
    private AccountingMethod accountingMethod;
    private LocalDateTime createdAt = LocalDateTime.now();
    private LocalDateTime updatedAt = LocalDateTime.now();
    private UUID createdBy;

    public enum BusinessType {
        Proprietorship, Partnership, LLP, PvtLtd, PublicLtd, NGO, Other
    }

    public enum Industry {
        IT, Manufacturing, Retail, Healthcare, Education, Finance, Hospitality, Construction, Other
    }

    public enum TurnoverRange {
        LESS_THAN_10L, TEN_TO_50L, FIFTY_TO_2CR, TWO_TO_10CR, MORE_THAN_10CR
    }

    public enum Month {
        JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC
    }

    public enum TargetMarket {
        Local, National, International
    }

    public enum AccountingMethod {
        Cash, Accrual
    }
}
