// src/main/java/com/ledgertalk/transactions/TransactionRepository.java
package com.ledgertalk.transactions;

import java.math.BigDecimal;

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