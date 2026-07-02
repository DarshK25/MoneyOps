package com.moneyops.invoices.repository;

import com.moneyops.invoices.entity.Invoice;
import com.moneyops.invoices.entity.InvoiceStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public interface InvoiceRepository extends MongoRepository<Invoice, String> {

    Optional<Invoice> findByIdAndOrgIdAndDeletedAtIsNull(String id, String orgId);

    Page<Invoice> findAllByOrgIdAndDeletedAtIsNull(String orgId, Pageable pageable);

    boolean existsByIdAndOrgIdAndDeletedAtIsNull(String id, String orgId);

    Optional<Invoice> findByOrgIdAndInvoiceNumberAndDeletedAtIsNull(String orgId, String invoiceNumber);

    Page<Invoice> findByOrgIdAndStatusAndDeletedAtIsNull(String orgId, InvoiceStatus status, Pageable pageable);

    Page<Invoice> findAllByOrgIdAndClientIdAndDeletedAtIsNull(String orgId, String clientId, Pageable pageable);

    @org.springframework.data.mongodb.repository.Query("{ 'orgId': ?0, 'deletedAt': null, 'dueDate': { $lt: ?1 }, 'status': { $nin: ['PAID', 'DRAFT'] } }")
    List<Invoice> findOverdueByOrgId(String orgId, LocalDate now);

    // Keep non-paginated versions for internal use (item lookup, etc.)
    List<Invoice> findAllByOrgIdAndDeletedAtIsNull(String orgId);
    List<Invoice> findAllByOrgIdAndClientIdAndDeletedAtIsNull(String orgId, String clientId);
}