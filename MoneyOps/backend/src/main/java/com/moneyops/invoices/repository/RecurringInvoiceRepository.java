package com.moneyops.invoices.repository;

import com.moneyops.invoices.entity.RecurringInvoice;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.time.LocalDate;
import java.util.List;

public interface RecurringInvoiceRepository extends MongoRepository<RecurringInvoice, String> {

    List<RecurringInvoice> findByOrgIdAndIsActiveTrue(String orgId);

    List<RecurringInvoice> findByIsActiveTrueAndLastGeneratedLessThanEqual(LocalDate date);

    List<RecurringInvoice> findByIdAndOrgId(String id, String orgId);
}
