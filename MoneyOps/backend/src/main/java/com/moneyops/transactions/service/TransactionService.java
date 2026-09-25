package com.moneyops.transactions.service;

import com.moneyops.compliance.ComplianceMetadataService;
import com.moneyops.events.dto.DomainEvent;
import com.moneyops.events.producer.IEventPublisher;
import com.moneyops.jpa.persistence.TransactionDocumentStore;
import com.moneyops.transactions.dto.TransactionDto;
import com.moneyops.transactions.entity.Transaction;
import com.moneyops.transactions.entity.TransactionType;
import com.moneyops.transactions.mapper.TransactionMapper;
import com.moneyops.transactions.validator.TransactionValidator;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
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
import java.time.YearMonth;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class TransactionService {

    private final TransactionDocumentStore transactionStore;
    private final TransactionMapper transactionMapper;
    private final TransactionValidator transactionValidator;
    private final ComplianceMetadataService complianceMetadataService;
    
    @Autowired(required = false)
    private IEventPublisher eventPublisher;

    private static final String TOPIC_PAYMENT_EVENTS = "moneyops.payment.events";
    private static final String TOPIC_EXPENSE_EVENTS = "moneyops.expense.events";

    public Page<TransactionDto> getAllTransactions(String orgId, int page, int size) {
        if (orgId == null || orgId.isBlank()) {
            throw new com.moneyops.shared.exceptions.UnauthorizedException("Missing organization context");
        }
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "transactionDate"));
        Page<Transaction> transactionPage = transactionStore.findAllByOrgId(orgId, pageable);
        List<TransactionDto> dtoList = transactionPage.getContent().stream()
                .map(transactionMapper::toDto)
                .collect(Collectors.toList());
        return new PageImpl<>(dtoList, pageable, transactionPage.getTotalElements());
    }

    public TransactionDto getTransactionById(String id, String orgId) {
        Transaction transaction = transactionStore.findByIdAndOrgId(id, orgId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Transaction not found"));
        return transactionMapper.toDto(transaction);
    }

    public TransactionDto createTransaction(TransactionDto dto, String orgId, String userId) {
        if (orgId == null || orgId.isBlank()) {
            throw new com.moneyops.shared.exceptions.UnauthorizedException("Missing organization context");
        }

        if (dto.getIdempotencyKey() != null) {
            var existing = transactionStore.findAllByOrgId(orgId).stream()
                    .filter(t -> dto.getIdempotencyKey().equals(t.getIdempotencyKey()))
                    .findFirst();
            if (existing.isPresent()) {
                return transactionMapper.toDto(existing.get());
            }
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

        Transaction saved = transactionStore.save(transaction);
        
        // Publish Kafka event
        publishTransactionEvent(saved, "TRANSACTION_CREATED", "Transaction created");
        
        return transactionMapper.toDto(saved);
    }

    public TransactionDto updateTransaction(String id, TransactionDto dto, String orgId) {
        Transaction existing = transactionStore.findByIdAndOrgId(id, orgId)
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

        Transaction saved = transactionStore.save(existing);
        return transactionMapper.toDto(saved);
    }

    public void deleteTransaction(String id, String orgId) {
        transactionStore.findByIdAndOrgId(id, orgId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Transaction not found"));
        transactionStore.softDelete(id, orgId);
    }

    public List<TransactionDto> getTransactionsByClient(String clientId, String orgId) {
        return transactionStore.findByOrgIdAndClientId(orgId, clientId).stream()
                .map(transactionMapper::toDto)
                .collect(Collectors.toList());
    }

    public List<TransactionDto> getTransactionsByInvoice(String invoiceId, String orgId) {
        return transactionStore.findByOrgIdAndInvoiceId(orgId, invoiceId).stream()
                .map(transactionMapper::toDto)
                .collect(Collectors.toList());
    }

    public List<TransactionDto> getTransactionsByDateRange(String orgId, LocalDate startDate, LocalDate endDate) {
        return transactionStore.findByOrgIdAndTransactionDateBetween(orgId, startDate, endDate).stream()
                .map(transactionMapper::toDto)
                .collect(Collectors.toList());
    }

    public List<TransactionDto> getTransactions(String orgId, String type, String month, Integer limit) {
        List<Transaction> transactions;

        if (type != null && !type.isBlank() && month != null && !month.isBlank()) {
            YearMonth period = YearMonth.parse(month);
            transactions = transactionStore.findByOrgIdAndTypeAndTransactionDateBetween(
                    orgId,
                    TransactionType.valueOf(type.toUpperCase()),
                    period.atDay(1),
                    period.atEndOfMonth());
        } else if (type != null && !type.isBlank()) {
            transactions = transactionStore.findByOrgIdAndType(orgId, TransactionType.valueOf(type.toUpperCase()));
        } else if (month != null && !month.isBlank()) {
            YearMonth period = YearMonth.parse(month);
            transactions = transactionStore.findByOrgIdAndTransactionDateBetween(
                    orgId, period.atDay(1), period.atEndOfMonth());
        } else {
            transactions = transactionStore.findAllByOrgId(orgId);
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
        BigDecimal result = transactionStore.sumAmountByOrgIdAndType(orgId, TransactionType.INCOME);
        return result != null ? result : BigDecimal.ZERO;
    }

    public BigDecimal getTotalExpense(String orgId) {
        BigDecimal result = transactionStore.sumAmountByOrgIdAndType(orgId, TransactionType.EXPENSE);
        return result != null ? result : BigDecimal.ZERO;
    }

    public Map<String, BigDecimal> getFinancialSummary(String orgId) {
        BigDecimal income = getTotalIncome(orgId);
        BigDecimal expense = getTotalExpense(orgId);
        return Map.of(
                "totalIncome", income,
                "totalExpense", expense,
                "netProfit", income.subtract(expense));
    }

    private void publishTransactionEvent(Transaction transaction, String eventType, String message) {
        if (eventPublisher != null) {
            try {
                String topic = transaction.getType() == TransactionType.INCOME ? TOPIC_PAYMENT_EVENTS : TOPIC_EXPENSE_EVENTS;
                String payload = String.format(
                    "{\"eventType\":\"%s\",\"transactionId\":\"%s\",\"orgId\":\"%s\",\"amount\":%s,\"type\":\"%s\",\"category\":\"%s\",\"description\":\"%s\",\"timestamp\":%d}",
                    eventType,
                    transaction.getId(),
                    transaction.getOrgId(),
                    transaction.getAmount(),
                    transaction.getType().name(),
                    transaction.getCategory() != null ? transaction.getCategory() : "",
                    transaction.getDescription() != null ? transaction.getDescription().replace("\"", "'") : "",
                    System.currentTimeMillis()
                );
                DomainEvent event = new DomainEvent(topic, transaction.getId(), payload);
                eventPublisher.publish(event);
            } catch (Exception e) {
                log.warn("Failed to publish transaction event", e);
            }
        }
    }

    private void log(String msg) {
        System.out.println(msg);
    }
}
