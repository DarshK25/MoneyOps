package com.moneyops.jpa.repository;

import com.moneyops.jpa.entity.TransactionEntity;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

@Repository
public interface TransactionJpaRepository extends JpaRepository<TransactionEntity, String> {
    Optional<TransactionEntity> findByIdAndOrgId(String id, String orgId);
    Optional<TransactionEntity> findByIdAndOrgIdAndDeletedAtIsNull(String id, String orgId);
    List<TransactionEntity> findByOrgId(String orgId);
    List<TransactionEntity> findByOrgIdAndDeletedAtIsNull(String orgId);
    Page<TransactionEntity> findByOrgIdAndDeletedAtIsNull(String orgId, Pageable pageable);
    List<TransactionEntity> findByOrgIdAndInvoiceId(String orgId, String invoiceId);
    List<TransactionEntity> findByOrgIdAndClientId(String orgId, String clientId);
    List<TransactionEntity> findByOrgIdAndInvoiceIdAndDeletedAtIsNull(String orgId, String invoiceId);
    List<TransactionEntity> findByOrgIdAndClientIdAndDeletedAtIsNull(String orgId, String clientId);
    List<TransactionEntity> findByOrgIdAndTransactionDateBetweenAndDeletedAtIsNull(
            String orgId, LocalDate start, LocalDate end);
    List<TransactionEntity> findByOrgIdAndTypeAndDeletedAtIsNull(String orgId, String type);
    List<TransactionEntity> findByOrgIdAndTypeAndTransactionDateBetweenAndDeletedAtIsNull(
            String orgId, String type, LocalDate start, LocalDate end);

    @Query("""
            SELECT COALESCE(SUM(t.amount), 0) FROM TransactionEntity t
            WHERE t.orgId = :orgId AND t.type = :type AND t.deletedAt IS NULL
            """)
    BigDecimal sumAmountByOrgIdAndType(@Param("orgId") String orgId, @Param("type") String type);
}
