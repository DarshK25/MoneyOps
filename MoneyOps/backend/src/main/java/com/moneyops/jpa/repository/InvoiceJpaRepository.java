package com.moneyops.jpa.repository;

import com.moneyops.jpa.entity.InvoiceEntity;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

@Repository
public interface InvoiceJpaRepository extends JpaRepository<InvoiceEntity, String> {
    Optional<InvoiceEntity> findByIdAndOrgId(String id, String orgId);
    Optional<InvoiceEntity> findByIdAndOrgIdAndDeletedAtIsNull(String id, String orgId);
    List<InvoiceEntity> findByOrgId(String orgId);
    List<InvoiceEntity> findByOrgIdAndDeletedAtIsNull(String orgId);
    Page<InvoiceEntity> findByOrgIdAndDeletedAtIsNull(String orgId, Pageable pageable);
    Optional<InvoiceEntity> findByOrgIdAndInvoiceNumber(String orgId, String invoiceNumber);
    Optional<InvoiceEntity> findByOrgIdAndInvoiceNumberAndDeletedAtIsNull(String orgId, String invoiceNumber);
    Page<InvoiceEntity> findByOrgIdAndStatusAndDeletedAtIsNull(String orgId, String status, Pageable pageable);
    Page<InvoiceEntity> findByOrgIdAndClientIdAndDeletedAtIsNull(String orgId, String clientId, Pageable pageable);

    @Query("""
            SELECT i FROM InvoiceEntity i
            WHERE i.orgId = :orgId
              AND i.deletedAt IS NULL
              AND i.dueDate < :now
              AND i.status NOT IN ('PAID', 'DRAFT')
            """)
    List<InvoiceEntity> findOverdueByOrgId(@Param("orgId") String orgId, @Param("now") LocalDate now);
}
