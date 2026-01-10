// src/main/java/com/ledgertalk/transactions/TransactionRepository.java
package com.ledgertalk.transactions;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public interface TransactionRepository extends JpaRepository<Transaction, Long> {
    List<Transaction> findByOrganizationId(Long organizationId);
    List<Transaction> findByOrganizationIdAndType(Long organizationId, TransactionType type);
    List<Transaction> findByClientId(Long clientId);
    List<Transaction> findByInvoiceId(Long invoiceId);
    
    @Query("SELECT t FROM Transaction t WHERE t.organizationId = :orgId AND t.transactionDate BETWEEN :startDate AND :endDate")
    List<Transaction> findByOrganizationIdAndDateRange(Long orgId, LocalDate startDate, LocalDate endDate);
    
    @Query("SELECT SUM(t.amount) FROM Transaction t WHERE t.organizationId = :orgId AND t.type = :type")
    BigDecimal getTotalByOrganizationAndType(Long orgId, TransactionType type);
}