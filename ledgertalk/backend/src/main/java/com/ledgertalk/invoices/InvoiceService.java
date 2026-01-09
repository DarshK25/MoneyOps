// src/main/java/com/ledgertalk/invoices/InvoiceService.java
package com.ledgertalk.invoices;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.time.LocalDate;
import java.util.List;

@Service
@RequiredArgsConstructor
public class InvoiceService {
    private final InvoiceRepository invoiceRepository;
    
    public List<Invoice> getAllInvoices() {
        return invoiceRepository.findAll();
    }
    
    public Invoice createInvoice(Invoice invoice) {
        return invoiceRepository.save(invoice);
    }
    
    public Invoice getInvoiceById(Long id) {
        return invoiceRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("Invoice not found"));
    }
    
    public List<Invoice> getInvoicesByOrganization(Long organizationId) {
        return invoiceRepository.findByOrganizationId(organizationId);
    }
    
    public List<Invoice> getInvoicesByClient(Long clientId) {
        return invoiceRepository.findByClientId(clientId);
    }
    
    public List<Invoice> getOverdueInvoices() {
        return invoiceRepository.findOverdueInvoices(LocalDate.now());
    }
    
    public Invoice updateInvoiceStatus(Long id, InvoiceStatus status) {
        Invoice invoice = getInvoiceById(id);
        invoice.setStatus(status);
        if (status == InvoiceStatus.PAID) {
            invoice.setPaidAt(java.time.LocalDateTime.now());
        }
        return invoiceRepository.save(invoice);
    }
    
    public Invoice updateInvoice(Long id, Invoice invoice) {
        Invoice existing = getInvoiceById(id);
        existing.setInvoiceNumber(invoice.getInvoiceNumber());
        existing.setInvoiceDate(invoice.getInvoiceDate());
        existing.setDueDate(invoice.getDueDate());
        existing.setAmount(invoice.getAmount());
        existing.setTaxAmount(invoice.getTaxAmount());
        existing.setTotalAmount(invoice.getTotalAmount());
        existing.setDescription(invoice.getDescription());
        existing.setNotes(invoice.getNotes());
        return invoiceRepository.save(existing);
    }
    
    public void deleteInvoice(Long id) {
        invoiceRepository.deleteById(id);
    }
}