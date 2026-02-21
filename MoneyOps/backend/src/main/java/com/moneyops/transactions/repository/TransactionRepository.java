package com.moneyops.transactions.repository;

import com.moneyops.transactions.entity.Transaction;
import com.moneyops.transactions.entity.TransactionType;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface TransactionRepository extends MongoRepository<Transaction, UUID>, TransactionRepositoryCustom {

    Optional<Transaction> findByIdAndOrgId(UUID id, UUID orgId);
    List<Transaction> findAllByOrgId(UUID orgId);
    void deleteByIdAndOrgId(UUID id, UUID orgId);
    boolean existsByIdAndOrgId(UUID id, UUID orgId);
    List<Transaction> findByOrgIdAndClientId(UUID orgId, UUID clientId);
    List<Transaction> findByOrgIdAndTransactionDateBetween(UUID orgId, LocalDate startDate, LocalDate endDate);
    List<Transaction> findByOrgIdAndType(UUID orgId, TransactionType type);

}
