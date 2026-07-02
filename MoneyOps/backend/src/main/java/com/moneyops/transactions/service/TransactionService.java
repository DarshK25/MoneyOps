// src/main/java/com/moneyops/transactions/service/TransactionService.java
package com.moneyops.transactions.service;

import com.moneyops.compliance.ComplianceMetadataService;
import com.moneyops.jpa.entity.TransactionEntity;
import com.moneyops.jpa.repository.TransactionJpaRepository;
import com.moneyops.transactions.dto.TransactionDto;
import com.moneyops.transactions.entity.Transaction;
import com.moneyops.transactions.entity.TransactionType;
import com.moneyops.transactions.mapper.TransactionMapper;
import com.moneyops.transactions.repository.TransactionRepository;
import com.moneyops.transactions.validator.TransactionValidator;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.YearMonth;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
@Transactional
public class TransactionService {

    private final TransactionRepository transactionRepository;
    private final TransactionJpaRepository transactionJpaRepository;
    private final TransactionMapper transactionMapper;
    private final TransactionValidator transactionValidator;
    private final ComplianceMetadataService complianceMetadataService;

    public TransactionRepository getTransactionRepository() {
        return transactionRepository;
    }

    public TransactionMapper getTransactionMapper() {
        return transactionMapper;
    }

    private void saveTransactionJpa(Transaction txn) {
        try {
            TransactionEntity entity = new TransactionEntity();
            entity.setId(txn.getId());
            entity.setOrgId(txn.getOrgId());
            entity.setInvoiceId(txn.getInvoiceId());
            entity.setClientId(txn.getClientId());
            entity.setType(txn.getType() != null ? txn.getType().name() : null);
            entity.setAmount(txn.getAmount());
            entity.setTransactionDate(txn.getTransactionDate());
            entity.setCreatedAt(txn.getCreatedAt());
            transactionJpaRepository.save(entity);
            log.debug("Transaction {} written to PostgreSQL", txn.getId());
        } catch (Exception e) {
            log.error("Failed to write transaction {} to PostgreSQL: {}", txn.getId(), e.getMessage());
        }
    }

    private TransactionDto toTransactionDto(TransactionEntity entity) {
        TransactionDto dto = new TransactionDto();
        dto.setId(entity.getId());
        dto.setOrgId(entity.getOrgId());
        dto.setInvoiceId(entity.getInvoiceId());
        dto.setClientId(entity.getClientId());
        dto.setType(entity.getType());
        dto.setAmount(entity.getAmount());
        dto.setTransactionDate(entity.getTransactionDate());
        return dto;
    }

    public Page<TransactionDto> getAllTransactions(String orgId, int page, int size) {
        if (orgId == null || orgId.isBlank()) throw new com.moneyops.shared.exceptions.UnauthorizedException("Missing organization context");
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "transactionDate"));
        Page<Transaction> transactionPage = transactionRepository.findAllByOrgIdAndDeletedAtIsNull(orgId, pageable);
        List<TransactionDto> dtoList = transactionPage.getContent().stream()
                .map(transactionMapper::toDto)
                .collect(Collectors.toList());
        return new PageImpl<>(dtoList, pageable, transactionPage.getTotalElements());
    }

    public TransactionDto getTransactionById(String id, String orgId) {
        var jpaTxn = transactionJpaRepository.findByIdAndOrgId(id, orgId);
        if (jpaTxn.isPresent()) {
            log.debug("Read transaction {} from PostgreSQL", id);
            return toTransactionDto(jpaTxn.get());
        }
        log.warn("Falling back to MongoDB for transaction {}", id);
        Transaction transaction = transactionRepository.findByIdAndOrgIdAndDeletedAtIsNull(id, orgId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Transaction not found"));
        return transactionMapper.toDto(transaction);
    }

    public TransactionDto createTransaction(TransactionDto dto, String orgId, String userId) {
        if (orgId == null || orgId.isBlank()) throw new com.moneyops.shared.exceptions.UnauthorizedException("Missing organization context");
        
        // ✨ Idempotency check
        if (dto.getIdempotencyKey() != null) {
            // Note: In a production app, we'd query an idempotency_keys collection
            // but for now we'll check if a transaction with this key exists
            var existing = transactionRepository.findAllByOrgIdAndDeletedAtIsNull(orgId).stream()
                .filter(t -> dto.getIdempotencyKey().equals(t.getIdempotencyKey()))
                .findFirst();
            if (existing.isPresent()) return transactionMapper.toDto(existing.get());
        }

        transactionValidator.validate(dto);

        Transaction transaction = transactionMapper.toEntity(dto);
        transaction.setOrgId(orgId);
        
        if (transaction.getTransactionDate() == null) {
            transaction.setTransactionDate(LocalDate.now());
        }
        if (transaction.getCurrency() == null) {
            transaction.setCurrency("INR");
        }
        complianceMetadataService.normalizeTransaction(transaction);

        Transaction saved = transactionRepository.save(transaction);
        saveTransactionJpa(saved);
        return transactionMapper.toDto(saved);
    }

    public TransactionDto updateTransaction(String id, TransactionDto dto, String orgId) {
        Transaction existing = transactionRepository.findByIdAndOrgIdAndDeletedAtIsNull(id, orgId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Transaction not found"));

        transactionValidator.validate(dto);

        existing.setClientId(dto.getClientId());
        existing.setInvoiceId(dto.getInvoiceId());
        existing.setType(TransactionType.valueOf(dto.getType().toUpperCase()));
        existing.setAmount(dto.getAmount());
        existing.setCurrency(dto.getCurrency() != null ? dto.getCurrency() : "INR");
        existing.setTransactionDate(dto.getTransactionDate());
        existing.setCategory(dto.getCategory());
        existing.setDescription(dto.getDescription());
        existing.setPaymentMethod(dto.getPaymentMethod());
        existing.setReferenceNumber(dto.getReferenceNumber());
        existing.setVendorName(dto.getVendorName());
        existing.setVendorGstin(dto.getVendorGstin());
        existing.setVendorPan(dto.getVendorPan());
        existing.setTaxableAmount(dto.getTaxableAmount());
        existing.setGstAmount(dto.getGstAmount());
        existing.setItcEligible(dto.getItcEligible());
        existing.setHasReceipt(dto.getHasReceipt());
        existing.setBankMatched(dto.getBankMatched());
        complianceMetadataService.normalizeTransaction(existing);

        Transaction saved = transactionRepository.save(existing);
        saveTransactionJpa(saved);
        return transactionMapper.toDto(saved);
    }

    public void deleteTransaction(String id, String orgId) {
        Transaction transaction = transactionRepository.findByIdAndOrgIdAndDeletedAtIsNull(id, orgId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Transaction not found"));
        
        // ✨ Soft Delete
        transaction.setDeletedAt(LocalDateTime.now());
        transactionRepository.save(transaction);
        transactionJpaRepository.deleteById(id);
    }

    public List<TransactionDto> getTransactionsByClient(String clientId, String orgId) {
        var jpaTxns = transactionJpaRepository.findByOrgIdAndClientId(orgId, clientId);
        if (!jpaTxns.isEmpty()) {
            log.debug("Read transactions for client {} from PostgreSQL", clientId);
            return jpaTxns.stream()
                    .map(this::toTransactionDto)
                    .collect(Collectors.toList());
        }
        log.warn("Falling back to MongoDB for transactions by client {}", clientId);
        return transactionRepository.findByOrgIdAndClientIdAndDeletedAtIsNull(orgId, clientId).stream()
                .map(transactionMapper::toDto)
                .collect(Collectors.toList());
    }

    public List<TransactionDto> getTransactionsByInvoice(String invoiceId, String orgId) {
        var jpaTxns = transactionJpaRepository.findByOrgIdAndInvoiceId(orgId, invoiceId);
        if (!jpaTxns.isEmpty()) {
            log.debug("Read transactions for invoice {} from PostgreSQL", invoiceId);
            return jpaTxns.stream()
                    .map(this::toTransactionDto)
                    .collect(Collectors.toList());
        }
        log.warn("Falling back to MongoDB for transactions by invoice {}", invoiceId);
        return transactionRepository.findByOrgIdAndInvoiceIdAndDeletedAtIsNull(orgId, invoiceId).stream()
                .map(transactionMapper::toDto)
                .collect(Collectors.toList());
    }

    public List<TransactionDto> getTransactionsByDateRange(String orgId, LocalDate startDate, LocalDate endDate) {
        return transactionRepository.findByOrgIdAndTransactionDateBetweenAndDeletedAtIsNull(orgId, startDate, endDate).stream()
                .map(transactionMapper::toDto)
                .collect(Collectors.toList());
    }

    public List<TransactionDto> getTransactions(String orgId, String type, String month, Integer limit) {
        List<Transaction> transactions;

        if (type != null && !type.isBlank() && month != null && !month.isBlank()) {
            YearMonth period = YearMonth.parse(month);
            transactions = transactionRepository.findByOrgIdAndTypeAndTransactionDateBetweenAndDeletedAtIsNull(
                    orgId,
                    TransactionType.valueOf(type.toUpperCase()),
                    period.atDay(1),
                    period.atEndOfMonth()
            );
        } else if (type != null && !type.isBlank()) {
            transactions = transactionRepository.findByOrgIdAndTypeAndDeletedAtIsNull(
                    orgId,
                    TransactionType.valueOf(type.toUpperCase())
            );
        } else if (month != null && !month.isBlank()) {
            YearMonth period = YearMonth.parse(month);
            transactions = transactionRepository.findByOrgIdAndTransactionDateBetweenAndDeletedAtIsNull(
                    orgId,
                    period.atDay(1),
                    period.atEndOfMonth()
            );
        } else {
            transactions = transactionRepository.findAllByOrgIdAndDeletedAtIsNull(orgId);
        }

        return transactions.stream()
                .sorted((left, right) -> {
                    LocalDate leftDate = left.getTransactionDate() != null ? left.getTransactionDate() : LocalDate.MIN;
                    LocalDate rightDate = right.getTransactionDate() != null ? right.getTransactionDate() : LocalDate.MIN;
                    return rightDate.compareTo(leftDate);
                })
                .limit(limit != null && limit > 0 ? limit : Long.MAX_VALUE)
                .map(transactionMapper::toDto)
                .collect(Collectors.toList());
    }

    public Page<TransactionDto> getTransactions(String orgId, String type, String month, int page, int size) {
        List<TransactionDto> transactions = getTransactions(orgId, type, month, null);
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "transactionDate"));
        int start = Math.min((int) pageable.getOffset(), transactions.size());
        int end = Math.min(start + pageable.getPageSize(), transactions.size());
        return new PageImpl<>(transactions.subList(start, end), pageable, transactions.size());
    }

    public BigDecimal getTotalIncome(String orgId) {
        var result = transactionRepository.getTotalByOrgIdAndType(orgId, TransactionType.INCOME);
        return (result != null && result.total() != null) ? BigDecimal.valueOf(result.total()) : BigDecimal.ZERO;
    }

    public BigDecimal getTotalExpense(String orgId) {
        var result = transactionRepository.getTotalByOrgIdAndType(orgId, TransactionType.EXPENSE);
        return (result != null && result.total() != null) ? BigDecimal.valueOf(result.total()) : BigDecimal.ZERO;
    }

    public Map<String, BigDecimal> getFinancialSummary(String orgId) {
        BigDecimal income = getTotalIncome(orgId);
        BigDecimal expense = getTotalExpense(orgId);
        return Map.of(
            "totalIncome", income,
            "totalExpense", expense,
            "netProfit", income.subtract(expense)
        );
    }
}
