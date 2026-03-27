package com.moneyops.invoices.repository;

import com.moneyops.invoices.entity.Invoice;
import com.moneyops.invoices.entity.InvoiceStatus;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

public interface InvoiceRepositoryCustom {

    List<Invoice> searchByOrgIdWithFilters(UUID orgId, UUID clientId, InvoiceStatus status, LocalDate startDate, LocalDate endDate);
}
