package com.moneyops.transactions.repository;

import com.moneyops.transactions.entity.Transaction;
import com.moneyops.transactions.entity.TransactionType;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

@Repository
public class TransactionRepositoryImpl implements TransactionRepositoryCustom {

    private final MongoTemplate mongoTemplate;

    public TransactionRepositoryImpl(MongoTemplate mongoTemplate) {
        this.mongoTemplate = mongoTemplate;
    }

    @Override
    public List<Transaction> searchByOrgIdWithFilters(UUID orgId, UUID clientId, TransactionType type, String category, LocalDate startDate, LocalDate endDate) {
        Criteria c = Criteria.where("orgId").is(orgId);
        if (clientId != null) c.and("clientId").is(clientId);
        if (type != null) c.and("type").is(type.name());
        if (category != null && !category.isBlank()) c.and("category").is(category);
        if (startDate != null) c.and("transactionDate").gte(startDate);
        if (endDate != null) c.and("transactionDate").lte(endDate);
        return mongoTemplate.find(new Query(c), Transaction.class);
    }
}
