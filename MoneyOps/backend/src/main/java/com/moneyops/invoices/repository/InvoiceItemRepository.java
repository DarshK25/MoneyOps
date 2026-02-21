package com.moneyops.invoices.repository;

import com.moneyops.invoices.entity.InvoiceItem;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;
import java.util.UUID;

public interface InvoiceItemRepository extends MongoRepository<InvoiceItem, UUID> {

    List<InvoiceItem> findByInvoiceId(UUID invoiceId);
    void deleteByInvoiceId(UUID invoiceId);
}
