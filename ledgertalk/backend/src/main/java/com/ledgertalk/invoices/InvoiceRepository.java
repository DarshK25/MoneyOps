// src/main/java/com/ledgertalk/invoices/InvoiceRepository.java
package com.ledgertalk.invoices;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import java.time.LocalDate;
import java.util.List;

public interface InvoiceRepository extends JpaRepository<Invoice, Long> {
    List<Invoice> findByOrganizationId(Long organizationId);
    List<Invoice> findByClientId(Long clientId);
    List<Invoice> findByStatus(InvoiceStatus status);
    
    @Query("SELECT i FROM Invoice i WHERE i.dueDate < :date AND i.status NOT IN ('PAID', 'CANCELLED')")
    List<Invoice> findOverdueInvoices(LocalDate date);
    
    List<Invoice> findByOrganizationIdAndStatus(Long organizationId, InvoiceStatus status);
}