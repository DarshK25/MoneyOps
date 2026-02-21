package com.moneyops.invoices.repository;

import com.moneyops.invoices.entity.Invoice;
import com.moneyops.invoices.entity.InvoiceStatus;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface InvoiceRepository extends MongoRepository<Invoice, UUID>, InvoiceRepositoryCustom {

    Optional<Invoice> findByIdAndOrgId(UUID id, UUID orgId);
    List<Invoice> findAllByOrgId(UUID orgId);
    void deleteByIdAndOrgId(UUID id, UUID orgId);
    boolean existsByIdAndOrgId(UUID id, UUID orgId);
    Optional<Invoice> findByOrgIdAndInvoiceNumber(UUID orgId, String invoiceNumber);
    List<Invoice> findByOrgIdAndStatus(UUID orgId, InvoiceStatus status);

    @Query("{ 'orgId' : ?0, 'dueDate' : { $lt: ?1 }, 'status' : { $ne: 'PAID' } }")
    List<Invoice> findOverdueByOrgId(UUID orgId, LocalDate date);

}
