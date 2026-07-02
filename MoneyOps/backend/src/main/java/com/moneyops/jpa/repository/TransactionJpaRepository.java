package com.moneyops.jpa.repository;

import com.moneyops.jpa.entity.TransactionEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface TransactionJpaRepository extends JpaRepository<TransactionEntity, String> {
    Optional<TransactionEntity> findByIdAndOrgId(String id, String orgId);
    List<TransactionEntity> findByOrgId(String orgId);
    List<TransactionEntity> findByOrgIdAndInvoiceId(String orgId, String invoiceId);
    List<TransactionEntity> findByOrgIdAndClientId(String orgId, String clientId);
}
