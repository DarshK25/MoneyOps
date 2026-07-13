package com.moneyops.jpa.persistence;

import com.moneyops.jpa.entity.TransactionEntity;
import com.moneyops.jpa.repository.TransactionJpaRepository;
import com.moneyops.jpa.util.DocumentJsonMapper;
import com.moneyops.transactions.entity.Transaction;
import com.moneyops.transactions.entity.TransactionType;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

@Component
@RequiredArgsConstructor
public class TransactionDocumentStore {

    private final TransactionJpaRepository transactionJpaRepository;
    private final DocumentJsonMapper documentJsonMapper;

    public Transaction save(Transaction transaction) {
        if (transaction.getId() == null || transaction.getId().isBlank()) {
            transaction.setId(UUID.randomUUID().toString());
        }
        if (transaction.getCreatedAt() == null) {
            transaction.setCreatedAt(LocalDateTime.now());
        }

        TransactionEntity entity = new TransactionEntity();
        syncColumns(entity, transaction);
        entity.setDocumentData(documentJsonMapper.toJson(transaction));
        transactionJpaRepository.save(entity);
        return transaction;
    }

    public Optional<Transaction> findByIdAndOrgId(String id, String orgId) {
        return transactionJpaRepository.findByIdAndOrgIdAndDeletedAtIsNull(id, orgId)
                .map(this::toDocument);
    }

    public Page<Transaction> findAllByOrgId(String orgId, Pageable pageable) {
        return transactionJpaRepository.findByOrgIdAndDeletedAtIsNull(orgId, pageable)
                .map(this::toDocument);
    }

    public List<Transaction> findByOrgIdAndClientId(String orgId, String clientId) {
        return transactionJpaRepository.findByOrgIdAndClientIdAndDeletedAtIsNull(orgId, clientId).stream()
                .map(this::toDocument)
                .collect(Collectors.toList());
    }

    public List<Transaction> findByOrgIdAndInvoiceId(String orgId, String invoiceId) {
        return transactionJpaRepository.findByOrgIdAndInvoiceIdAndDeletedAtIsNull(orgId, invoiceId).stream()
                .map(this::toDocument)
                .collect(Collectors.toList());
    }

    public List<Transaction> findByOrgIdAndTransactionDateBetween(String orgId, LocalDate start, LocalDate end) {
        return transactionJpaRepository
                .findByOrgIdAndTransactionDateBetweenAndDeletedAtIsNull(orgId, start, end).stream()
                .map(this::toDocument)
                .collect(Collectors.toList());
    }

    public List<Transaction> findByOrgIdAndType(String orgId, TransactionType type) {
        return transactionJpaRepository.findByOrgIdAndTypeAndDeletedAtIsNull(orgId, type.name()).stream()
                .map(this::toDocument)
                .collect(Collectors.toList());
    }

    public List<Transaction> findByOrgIdAndTypeAndTransactionDateBetween(
            String orgId, TransactionType type, LocalDate start, LocalDate end) {
        return transactionJpaRepository
                .findByOrgIdAndTypeAndTransactionDateBetweenAndDeletedAtIsNull(orgId, type.name(), start, end)
                .stream()
                .map(this::toDocument)
                .collect(Collectors.toList());
    }

    public List<Transaction> findAllByOrgId(String orgId) {
        return transactionJpaRepository.findByOrgIdAndDeletedAtIsNull(orgId).stream()
                .map(this::toDocument)
                .collect(Collectors.toList());
    }

    public BigDecimal sumAmountByOrgIdAndType(String orgId, TransactionType type) {
        return transactionJpaRepository.sumAmountByOrgIdAndType(orgId, type.name());
    }

    public void softDelete(String id, String orgId) {
        transactionJpaRepository.findByIdAndOrgIdAndDeletedAtIsNull(id, orgId).ifPresent(entity -> {
            entity.setDeletedAt(LocalDateTime.now());
            Transaction doc = toDocument(entity);
            if (doc != null) {
                doc.setDeletedAt(entity.getDeletedAt());
                entity.setDocumentData(documentJsonMapper.toJson(doc));
            }
            transactionJpaRepository.save(entity);
        });
    }

    private Transaction toDocument(TransactionEntity entity) {
        Transaction doc = documentJsonMapper.fromJson(entity.getDocumentData(), Transaction.class);
        if (doc == null) {
            doc = new Transaction();
        }
        syncDocumentFromColumns(doc, entity);
        return doc;
    }

    private void syncColumns(TransactionEntity entity, Transaction transaction) {
        entity.setId(transaction.getId());
        entity.setOrgId(transaction.getOrgId());
        entity.setInvoiceId(transaction.getInvoiceId());
        entity.setClientId(transaction.getClientId());
        entity.setType(transaction.getType() != null ? transaction.getType().name() : null);
        entity.setAmount(transaction.getAmount());
        entity.setCurrency(transaction.getCurrency() != null ? transaction.getCurrency() : "INR");
        entity.setTransactionDate(transaction.getTransactionDate());
        entity.setCreatedAt(transaction.getCreatedAt());
        entity.setUpdatedAt(LocalDateTime.now());
        entity.setDeletedAt(transaction.getDeletedAt());
    }

    private void syncDocumentFromColumns(Transaction doc, TransactionEntity entity) {
        doc.setId(entity.getId());
        doc.setOrgId(entity.getOrgId());
        doc.setInvoiceId(entity.getInvoiceId());
        doc.setClientId(entity.getClientId());
        if (entity.getType() != null) {
            doc.setType(TransactionType.valueOf(entity.getType()));
        }
        doc.setAmount(entity.getAmount());
        doc.setCurrency(entity.getCurrency());
        doc.setTransactionDate(entity.getTransactionDate());
        doc.setCreatedAt(entity.getCreatedAt());
        doc.setDeletedAt(entity.getDeletedAt());
    }
}
