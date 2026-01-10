// src/main/java/com/ledgertalk/transactions/TransactionController.java
package com.ledgertalk.transactions;

import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/transactions")
@RequiredArgsConstructor
public class TransactionController {
    private final TransactionService transactionService;
    
    @GetMapping
    public ResponseEntity<List<Transaction>> getAllTransactions() {
        return ResponseEntity.ok(transactionService.getAllTransactions());
    }
    
    @PostMapping
    public ResponseEntity<Transaction> createTransaction(@RequestBody Transaction transaction) {
        return ResponseEntity.ok(transactionService.createTransaction(transaction));
    }
    
    @GetMapping("/{id}")
    public ResponseEntity<Transaction> getTransaction(@PathVariable Long id) {
        return ResponseEntity.ok(transactionService.getTransactionById(id));
    }
    
    @GetMapping("/organization/{organizationId}")
    public ResponseEntity<List<Transaction>> getTransactionsByOrganization(@PathVariable Long organizationId) {
        return ResponseEntity.ok(transactionService.getTransactionsByOrganization(organizationId));
    }
    
    @GetMapping("/client/{clientId}")
    public ResponseEntity<List<Transaction>> getTransactionsByClient(@PathVariable Long clientId) {
        return ResponseEntity.ok(transactionService.getTransactionsByClient(clientId));
    }
    
    @GetMapping("/organization/{organizationId}/range")
    public ResponseEntity<List<Transaction>> getTransactionsByDateRange(
            @PathVariable Long organizationId,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate) {
        return ResponseEntity.ok(transactionService.getTransactionsByDateRange(organizationId, startDate, endDate));
    }
    
    @GetMapping("/organization/{organizationId}/summary")
    public ResponseEntity<Map<String, BigDecimal>> getFinancialSummary(@PathVariable Long organizationId) {
        BigDecimal income = transactionService.getTotalIncome(organizationId);
        BigDecimal expense = transactionService.getTotalExpense(organizationId);
        return ResponseEntity.ok(Map.of(
            "totalIncome", income,
            "totalExpense", expense,
            "netProfit", income.subtract(expense)
        ));
    }
    
    @PutMapping("/{id}")
    public ResponseEntity<Transaction> updateTransaction(@PathVariable Long id, @RequestBody Transaction transaction) {
        return ResponseEntity.ok(transactionService.updateTransaction(id, transaction));
    }
    
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteTransaction(@PathVariable Long id) {
        transactionService.deleteTransaction(id);
        return ResponseEntity.noContent().build();
    }
}