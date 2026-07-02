package com.moneyops.transactions.repository;

import com.moneyops.transactions.entity.Transaction;
import com.moneyops.transactions.entity.TransactionType;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public interface TransactionRepository extends MongoRepository<Transaction, String> {

    Optional<Transaction> findByIdAndOrgIdAndDeletedAtIsNull(String id, String orgId);

    Page<Transaction> findAllByOrgIdAndDeletedAtIsNull(String orgId, Pageable pageable);

    boolean existsByIdAndOrgIdAndDeletedAtIsNull(String id, String orgId);

    Page<Transaction> findByOrgIdAndClientIdAndDeletedAtIsNull(String orgId, String clientId, Pageable pageable);
    
    Page<Transaction> findByOrgIdAndInvoiceIdAndDeletedAtIsNull(String orgId, String invoiceId, Pageable pageable);

    Optional<Transaction> findByOrgIdAndInvoiceIdAndIdempotencyKeyAndDeletedAtIsNull(
            String orgId,
            String invoiceId,
            String idempotencyKey
    );

    Page<Transaction> findByOrgIdAndTypeAndDeletedAtIsNull(String orgId, TransactionType type, Pageable pageable);

    List<Transaction> findByOrgIdAndTypeAndDeletedAtIsNull(String orgId, TransactionType type);

    List<Transaction> findByOrgIdAndTransactionDateBetweenAndDeletedAtIsNull(
            String orgId,
            LocalDate startDate,
            LocalDate endDate
    );

    List<Transaction> findByOrgIdAndTypeAndTransactionDateBetweenAndDeletedAtIsNull(
            String orgId,
            TransactionType type,
            LocalDate startDate,
            LocalDate endDate
    );

    Page<Transaction> findByOrgIdAndTypeAndTransactionDateBetweenAndDeletedAtIsNull(
            String orgId,
            TransactionType type,
            LocalDate startDate,
            LocalDate endDate,
            Pageable pageable
    );

    // Keep non-paginated for aggregations and internal use
    List<Transaction> findAllByOrgIdAndDeletedAtIsNull(String orgId);
    List<Transaction> findByOrgIdAndClientIdAndDeletedAtIsNull(String orgId, String clientId);
    List<Transaction> findByOrgIdAndInvoiceIdAndDeletedAtIsNull(String orgId, String invoiceId);

    @org.springframework.data.mongodb.repository.Aggregation(pipeline = {
            "{ $match: { 'orgId': ?0, 'type': ?1, 'deletedAt': null } }",
            "{ $addFields: { numericAmount: { $convert: { input: '$amount', to: 'double', onError: 0, onNull: 0 } } } }",
            "{ $group: { _id: null, total: { $sum: '$numericAmount' } } }"
    })
    TotalResult getTotalByOrgIdAndType(String orgId, TransactionType type);

    record TotalResult(Double total) {}
}
