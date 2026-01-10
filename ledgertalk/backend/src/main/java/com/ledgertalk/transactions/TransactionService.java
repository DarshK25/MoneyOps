// src/main/java/com/ledgertalk/transactions/TransactionService.java
package com.ledgertalk.transactions;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

@Service
@RequiredArgsConstructor
public class TransactionService {
    private final TransactionRepository transactionRepository;
    
    public List<Transaction> getAllTransactions() {
        return transactionRepository.findAll();
    }
    
    public Transaction createTransaction(Transaction transaction) {
        return transactionRepository.save(transaction);
    }
    
    public Transaction getTransactionById(Long id) {
        return transactionRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("Transaction not found"));
    }
    
    public List<Transaction> getTransactionsByOrganization(Long organizationId) {
        return transactionRepository.findByOrganizationId(organizationId);
    }
    
    public List<Transaction> getTransactionsByClient(Long clientId) {
        return transactionRepository.findByClientId(clientId);
    }
    
    public List<Transaction> getTransactionsByDateRange(Long organizationId, LocalDate startDate, LocalDate endDate) {
        return transactionRepository.findByOrganizationIdAndDateRange(organizationId, startDate, endDate);
    }
    
    public BigDecimal getTotalIncome(Long organizationId) {
        BigDecimal total = transactionRepository.getTotalByOrganizationAndType(organizationId, TransactionType.INCOME);
        return total != null ? total : BigDecimal.ZERO;
    }
    
    public BigDecimal getTotalExpense(Long organizationId) {
        BigDecimal total = transactionRepository.getTotalByOrganizationAndType(organizationId, TransactionType.EXPENSE);
        return total != null ? total : BigDecimal.ZERO;
    }
    
    public Transaction updateTransaction(Long id, Transaction transaction) {
        Transaction existing = getTransactionById(id);
        existing.setType(transaction.getType());
        existing.setAmount(transaction.getAmount());
        existing.setTransactionDate(transaction.getTransactionDate());
        existing.setCategory(transaction.getCategory());
        existing.setDescription(transaction.getDescription());
        existing.setPaymentMethod(transaction.getPaymentMethod());
        existing.setReferenceNumber(transaction.getReferenceNumber());
        return transactionRepository.save(existing);
    }
    
    public void deleteTransaction(Long id) {
        transactionRepository.deleteById(id);
    }
}