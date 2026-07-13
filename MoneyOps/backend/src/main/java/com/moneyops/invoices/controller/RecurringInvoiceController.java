package com.moneyops.invoices.controller;

import com.moneyops.invoices.dto.InvoiceDto;
import com.moneyops.invoices.dto.RecurringInvoiceDto;
import com.moneyops.invoices.service.RecurringInvoiceService;
import com.moneyops.shared.exceptions.BusinessRuleException;
import com.moneyops.shared.utils.OrgContext;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/recurring-invoices")
@RequiredArgsConstructor
public class RecurringInvoiceController {

    private final RecurringInvoiceService recurringInvoiceService;

    @PostMapping
    public ResponseEntity<RecurringInvoiceDto> createRecurringInvoice(@RequestBody RecurringInvoiceDto dto) {
        String orgId = OrgContext.getOrgId();
        String userId = OrgContext.getUserId();
        if (orgId == null) throw new BusinessRuleException("Organization context missing");

        RecurringInvoiceDto created = recurringInvoiceService.createRecurringInvoice(dto, orgId, userId);
        return ResponseEntity.ok(created);
    }

    @GetMapping
    public ResponseEntity<List<RecurringInvoiceDto>> getActiveRecurringInvoices() {
        String orgId = OrgContext.getOrgId();
        if (orgId == null) return ResponseEntity.ok(java.util.Collections.emptyList());

        List<RecurringInvoiceDto> invoices = recurringInvoiceService.getActiveRecurringInvoices(orgId);
        return ResponseEntity.ok(invoices);
    }

    @PutMapping("/{id}")
    public ResponseEntity<RecurringInvoiceDto> updateRecurringInvoice(
            @PathVariable String id,
            @RequestBody RecurringInvoiceDto dto) {
        String orgId = OrgContext.getOrgId();
        RecurringInvoiceDto updated = recurringInvoiceService.updateRecurringInvoice(id, dto, orgId);
        return ResponseEntity.ok(updated);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deactivateRecurringInvoice(@PathVariable String id) {
        String orgId = OrgContext.getOrgId();
        recurringInvoiceService.deactivateRecurringInvoice(id, orgId);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/{id}/generate")
    public ResponseEntity<InvoiceDto> generateInvoice(@PathVariable String id) {
        String orgId = OrgContext.getOrgId();
        String userId = OrgContext.getUserId();

        InvoiceDto invoice = recurringInvoiceService.generateInvoiceFromRecurringDto(id, orgId, userId);
        return ResponseEntity.ok(invoice);
    }
}
