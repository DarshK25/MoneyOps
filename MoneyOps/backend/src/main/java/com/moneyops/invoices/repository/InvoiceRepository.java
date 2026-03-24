package com.moneyops.invoices.repository;

import com.moneyops.invoices.entity.Invoice;
import com.moneyops.invoices.entity.InvoiceStatus;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface InvoiceRepository extends MongoRepository<Invoice, String> {

    Optional<Invoice> findByIdAndOrgId(String id, String orgId);

    List<Invoice> findAllByOrgId(String orgId);

    boolean existsByIdAndOrgId(String id, String orgId);

    Optional<Invoice> findByOrgIdAndInvoiceNumber(String orgId, String invoiceNumber);

    List<Invoice> findByOrgIdAndStatus(String orgId, InvoiceStatus status);

    List<Invoice> findAllByOrgIdAndClientId(String orgId, String clientId);

    void deleteByIdAndOrgId(String id, String orgId);

    @org.springframework.data.mongodb.repository.Query("{ 'orgId': ?0, 'dueDate': { $lt: ?1 }, 'status': { $nin: ['PAID', 'DRAFT'] } }")
    List<Invoice> findOverdueByOrgId(String orgId, java.time.LocalDate now);
}