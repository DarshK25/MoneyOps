package com.moneyops.jpa.repository;

import com.moneyops.jpa.entity.InvoiceEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface InvoiceJpaRepository extends JpaRepository<InvoiceEntity, String> {
    Optional<InvoiceEntity> findByIdAndOrgId(String id, String orgId);
    List<InvoiceEntity> findByOrgId(String orgId);
    Optional<InvoiceEntity> findByOrgIdAndInvoiceNumber(String orgId, String invoiceNumber);
}
