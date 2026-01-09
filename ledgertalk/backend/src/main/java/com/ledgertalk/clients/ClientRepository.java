// src/main/java/com/ledgertalk/clients/ClientRepository.java
package com.ledgertalk.clients;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface ClientRepository extends JpaRepository<Client, Long> {
    List<Client> findByOrganizationId(Long organizationId);
    List<Client> findByOrganizationIdAndActiveTrue(Long organizationId);
}