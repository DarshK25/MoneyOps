// src/main/java/com/ledgertalk/clients/Client.java
package com.ledgertalk.clients;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

@Entity
@Table(name = "clients")
@Data
public class Client {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private String name;
    
    @Column(nullable = false)
    private Long organizationId; // Which org owns this client
    
    private String taxId; // Client's GST/PAN
    
    @Column(nullable = false)
    private String email;
    private String phoneNumber;
    
    private String address;
    private String city;
    private String state;
    private String country;
    private String postalCode;
    
    @Column(nullable = false)
    private LocalDateTime createdAt = LocalDateTime.now();
    
    @Column(nullable = false)
    private Boolean active = true;
    
    // Financial info
    private String paymentTerms; // e.g., "Net 30", "Net 60"
    private String currency = "INR";
}