package com.moneyops.invoices.repository;

import com.moneyops.invoices.entity.Invoice;
import com.moneyops.invoices.entity.InvoiceStatus;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

@Repository
public class InvoiceRepositoryImpl implements InvoiceRepositoryCustom {

    private final MongoTemplate mongoTemplate;

    public InvoiceRepositoryImpl(MongoTemplate mongoTemplate) {
        this.mongoTemplate = mongoTemplate;
    }

    @Override
    public List<Invoice> searchByOrgIdWithFilters(UUID orgId, UUID clientId, InvoiceStatus status, LocalDate startDate, LocalDate endDate) {
        Criteria c = Criteria.where("orgId").is(orgId);
        if (clientId != null) c.and("clientId").is(clientId);
        if (status != null) c.and("status").is(status.name());
        if (startDate != null) c.and("issueDate").gte(startDate);
        if (endDate != null) c.and("issueDate").lte(endDate);
        return mongoTemplate.find(new Query(c), Invoice.class);
    }
}
