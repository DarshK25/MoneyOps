// src/main/java/com/ledgertalk/organizations/OrganizationRepository.java
package com.ledgertalk.organizations;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface OrganizationRepository extends JpaRepository<Organization, Long> {
    Optional<Organization> findByTaxId(String taxId);
    List<Organization> findByOwnerId(Long ownerId);
}