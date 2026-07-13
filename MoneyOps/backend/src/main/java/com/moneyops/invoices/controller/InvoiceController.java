package com.moneyops.invoices.controller;

import com.moneyops.invoices.dto.InvoiceDto;
import com.moneyops.invoices.service.InvoiceService;
import com.moneyops.shared.exceptions.BusinessRuleException;
import com.moneyops.shared.utils.OrgContext;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/invoices")
@RequiredArgsConstructor
public class InvoiceController {

    private final InvoiceService invoiceService;

    @PostMapping
    public ResponseEntity<InvoiceDto> createInvoice(@RequestBody InvoiceDto dto) {
        String orgId = OrgContext.getOrgId();
        String userId = OrgContext.getUserId();
        
        if (orgId == null) throw new BusinessRuleException("Organization context missing");
        
        InvoiceDto created = invoiceService.createInvoice(dto, orgId, userId);
        return ResponseEntity.ok(created);
    }

    @PostMapping("/preview")
    public ResponseEntity<InvoiceDto> previewInvoice(@RequestBody InvoiceDto dto) {
        invoiceService.validateAndCalculate(dto);
        return ResponseEntity.ok(dto);
    }

    @PutMapping("/{id}")
    public ResponseEntity<InvoiceDto> updateInvoice(@PathVariable String id, @RequestBody InvoiceDto dto) {
        String orgId = OrgContext.getOrgId();
        InvoiceDto updated = invoiceService.updateInvoice(id, dto, orgId);
        return ResponseEntity.ok(updated);
    }

    @GetMapping
    public ResponseEntity<Page<InvoiceDto>> getAllInvoices(
            @RequestParam(required = false) String status,
            @RequestParam(required = false, name = "client_name") String clientName,
            @RequestParam(required = false, name = "clientId") String clientId,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        String orgId = OrgContext.getOrgId();
        if (orgId == null) return ResponseEntity.ok(new PageImpl<>(List.of(), PageRequest.of(0, 20), 0));
        Page<InvoiceDto> invoices = invoiceService.searchInvoices(orgId, status, clientName, clientId, page, size);
        return ResponseEntity.ok(invoices);
    }

    @GetMapping("/{id}")
    public ResponseEntity<InvoiceDto> getInvoice(@PathVariable String id) {
        String orgId = OrgContext.getOrgId();
        if (orgId == null) return ResponseEntity.status(403).build();
        InvoiceDto invoice = invoiceService.getInvoiceById(id, orgId);
        return ResponseEntity.ok(invoice);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteInvoice(@PathVariable String id) {
        String orgId = OrgContext.getOrgId();
        invoiceService.deleteInvoice(id, orgId);
        return ResponseEntity.noContent().build();
    }

    @PatchMapping("/{id}/send")
    public ResponseEntity<InvoiceDto> sendInvoice(@PathVariable String id) {
        String orgId = OrgContext.getOrgId();
        InvoiceDto sent = invoiceService.sendInvoice(id, orgId);
        return ResponseEntity.ok(sent);
    }

    @PostMapping("/{id}/send-followup")
    public ResponseEntity<com.moneyops.shared.dto.ApiResponse<Void>> sendFollowUp(@PathVariable String id) {
        String orgId = OrgContext.getOrgId();
        invoiceService.sendFollowUpEmail(id, orgId);
        return ResponseEntity.ok(com.moneyops.shared.dto.ApiResponse.success("Follow-up email sent", null));
    }

    @PatchMapping("/{id}/mark-paid")
    public ResponseEntity<InvoiceDto> markPaid(@PathVariable String id) {
        String orgId = OrgContext.getOrgId();
        InvoiceDto paid = invoiceService.markPaid(id, orgId);
        return ResponseEntity.ok(paid);
    }

    @GetMapping("/overdue")
    public ResponseEntity<List<InvoiceDto>> getOverdueInvoices() {
        String orgId = OrgContext.getOrgId();
        List<InvoiceDto> overdue = invoiceService.getOverdueInvoices(orgId);
        return ResponseEntity.ok(overdue);
    }

    @GetMapping("/{id}/download")
    public ResponseEntity<ByteArrayResource> downloadInvoice(@PathVariable String id) {
        String orgId = OrgContext.getOrgId();
        InvoiceDto invoice = invoiceService.getInvoiceById(id, orgId);
        byte[] pdf = invoiceService.generateInvoicePdf(id, orgId);
        ByteArrayResource resource = new ByteArrayResource(pdf);

        return ResponseEntity.ok()
                .contentType(MediaType.APPLICATION_PDF)
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"invoice-" + invoice.getInvoiceNumber() + ".pdf\"")
                .contentLength(pdf.length)
                .body(resource);
    }

    @GetMapping("/{id}/logs")
    public ResponseEntity<List<com.moneyops.audit.entity.AuditLog>> getInvoiceLogs(@PathVariable String id) {
        String orgId = OrgContext.getOrgId();
        return ResponseEntity.ok(invoiceService.getInvoiceLogs(id, orgId));
    }

    @GetMapping("/{id}/payments")
    public ResponseEntity<List<com.moneyops.transactions.dto.TransactionDto>> getInvoicePayments(@PathVariable String id) {
        String orgId = OrgContext.getOrgId();
        return ResponseEntity.ok(invoiceService.getInvoicePayments(id, orgId));
    }

    @PostMapping("/{id}/payment")
    public ResponseEntity<com.moneyops.shared.dto.ApiResponse<com.moneyops.transactions.dto.TransactionDto>> recordPayment(
            @PathVariable String id,
            @RequestBody com.moneyops.transactions.dto.TransactionDto paymentDto) {
        String orgId = OrgContext.getOrgId();
        String userId = OrgContext.getUserId();
        com.moneyops.transactions.dto.TransactionDto saved = invoiceService.recordPayment(id, paymentDto, orgId, userId);
        return ResponseEntity.ok(com.moneyops.shared.dto.ApiResponse.success("Payment recorded successfully", saved));
    }
}
