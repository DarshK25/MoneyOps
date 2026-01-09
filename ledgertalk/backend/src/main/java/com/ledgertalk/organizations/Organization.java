// src/main/java/com/ledgertalk/organizations/Organization.java
package com.ledgertalk.organizations;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

@Entity
@Table(name = "organizations")
@Data
public class Organization {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private String name;
    
    @Column(unique = true)
    private String taxId; // GST/PAN for India
    
    private String address;
    private String city;
    private String state;
    private String country;
    private String postalCode;
    
    @Column(unique = true)
    private String email;
    private String phoneNumber;
    
    @Column(nullable = false)
    private LocalDateTime createdAt = LocalDateTime.now();
    
    @Column(nullable = false)
    private Boolean active = true;
    
    // Owner of the organization
    @Column(nullable = false)
    private Long ownerId; // References User.id
}