package com.moneyops.clients.entity;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.LocalDateTime;
import java.util.UUID;

@Document(collection = "clients")
@Data
public class Client {
    @Id
    private UUID id = UUID.randomUUID();

    private UUID orgId;
    private String name;
    private String taxId;
    private String email;
    private String phoneNumber;
    private String address;
    private String city;
    private String state;
    private String country;
    private String postalCode;
    private String paymentTerms;
    private String currency = "INR";
    private Status status = Status.ACTIVE;
    private LocalDateTime createdAt = LocalDateTime.now();
    private LocalDateTime updatedAt = LocalDateTime.now();
    private UUID createdBy;
    private UUID updatedBy;

    public enum Status {
        ACTIVE, INACTIVE, SUSPENDED
    }
}
