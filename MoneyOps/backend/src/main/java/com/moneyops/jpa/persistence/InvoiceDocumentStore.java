package com.moneyops.jpa.persistence;

import com.moneyops.invoices.entity.Invoice;
import com.moneyops.invoices.entity.InvoiceStatus;
import com.moneyops.jpa.entity.InvoiceEntity;
import com.moneyops.jpa.repository.InvoiceJpaRepository;
import com.moneyops.jpa.util.DocumentJsonMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

@Component
@RequiredArgsConstructor
public class InvoiceDocumentStore {

    private final InvoiceJpaRepository invoiceJpaRepository;
    private final DocumentJsonMapper documentJsonMapper;

    public Invoice save(Invoice invoice) {
        if (invoice.getId() == null || invoice.getId().isBlank()) {
            invoice.setId(UUID.randomUUID().toString());
        }
        if (invoice.getCreatedAt() == null) {
            invoice.setCreatedAt(LocalDateTime.now());
        }
        invoice.setUpdatedAt(LocalDateTime.now());

        InvoiceEntity entity = new InvoiceEntity();
        syncColumns(entity, invoice);
        entity.setDocumentData(documentJsonMapper.toJson(invoice));
        invoiceJpaRepository.save(entity);
        return invoice;
    }

    public Optional<Invoice> findByIdAndOrgId(String id, String orgId) {
        return invoiceJpaRepository.findByIdAndOrgIdAndDeletedAtIsNull(id, orgId)
                .map(this::toDocument);
    }

    public Optional<Invoice> findByOrgIdAndInvoiceNumber(String orgId, String invoiceNumber) {
        return invoiceJpaRepository.findByOrgIdAndInvoiceNumberAndDeletedAtIsNull(orgId, invoiceNumber)
                .map(this::toDocument);
    }

    public Page<Invoice> findAllByOrgId(String orgId, Pageable pageable) {
        return invoiceJpaRepository.findByOrgIdAndDeletedAtIsNull(orgId, pageable)
                .map(this::toDocument);
    }

    public List<Invoice> findAllByOrgId(String orgId) {
        return invoiceJpaRepository.findByOrgIdAndDeletedAtIsNull(orgId).stream()
                .map(this::toDocument)
                .collect(Collectors.toList());
    }

    public Page<Invoice> findByOrgIdAndStatus(String orgId, InvoiceStatus status, Pageable pageable) {
        return invoiceJpaRepository.findByOrgIdAndStatusAndDeletedAtIsNull(orgId, status.name(), pageable)
                .map(this::toDocument);
    }

    public Page<Invoice> findByOrgIdAndClientId(String orgId, String clientId, Pageable pageable) {
        return invoiceJpaRepository.findByOrgIdAndClientIdAndDeletedAtIsNull(orgId, clientId, pageable)
                .map(this::toDocument);
    }

    public List<Invoice> findOverdueByOrgId(String orgId, LocalDate now) {
        return invoiceJpaRepository.findOverdueByOrgId(orgId, now).stream()
                .map(this::toDocument)
                .collect(Collectors.toList());
    }

    public void softDelete(String id, String orgId) {
        invoiceJpaRepository.findByIdAndOrgIdAndDeletedAtIsNull(id, orgId).ifPresent(entity -> {
            entity.setDeletedAt(LocalDateTime.now());
            Invoice doc = toDocument(entity);
            if (doc != null) {
                doc.setDeletedAt(entity.getDeletedAt());
                entity.setDocumentData(documentJsonMapper.toJson(doc));
            }
            invoiceJpaRepository.save(entity);
        });
    }

    private Invoice toDocument(InvoiceEntity entity) {
        Invoice doc = documentJsonMapper.fromJson(entity.getDocumentData(), Invoice.class);
        if (doc == null) {
            doc = new Invoice();
        }
        syncDocumentFromColumns(doc, entity);
        return doc;
    }

    private void syncColumns(InvoiceEntity entity, Invoice invoice) {
        entity.setId(invoice.getId());
        entity.setOrgId(invoice.getOrgId());
        entity.setClientId(invoice.getClientId());
        entity.setInvoiceNumber(invoice.getInvoiceNumber());
        entity.setStatus(invoice.getStatus() != null ? invoice.getStatus().name() : "DRAFT");
        entity.setTotalAmount(invoice.getTotalAmount());
        entity.setDueDate(invoice.getDueDate());
        entity.setIssueDate(invoice.getIssueDate());
        entity.setCreatedAt(invoice.getCreatedAt());
        entity.setUpdatedAt(invoice.getUpdatedAt());
        entity.setDeletedAt(invoice.getDeletedAt());
    }

    private void syncDocumentFromColumns(Invoice doc, InvoiceEntity entity) {
        doc.setId(entity.getId());
        doc.setOrgId(entity.getOrgId());
        doc.setClientId(entity.getClientId());
        doc.setInvoiceNumber(entity.getInvoiceNumber());
        if (entity.getStatus() != null) {
            doc.setStatus(InvoiceStatus.valueOf(entity.getStatus()));
        }
        doc.setTotalAmount(entity.getTotalAmount());
        doc.setDueDate(entity.getDueDate());
        doc.setIssueDate(entity.getIssueDate());
        doc.setCreatedAt(entity.getCreatedAt());
        doc.setDeletedAt(entity.getDeletedAt());
    }
}
