package com.moneyops.transactions.repository;

import com.moneyops.transactions.entity.Transaction;
import com.moneyops.transactions.entity.TransactionType;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

public interface TransactionRepositoryCustom {

    List<Transaction> searchByOrgIdWithFilters(UUID orgId, UUID clientId, TransactionType type, String category, LocalDate startDate, LocalDate endDate);
}
