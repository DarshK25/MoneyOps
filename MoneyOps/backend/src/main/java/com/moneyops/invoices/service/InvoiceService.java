// src/main/java/com/moneyops/invoices/service/InvoiceService.java
package com.moneyops.invoices.service;

import com.moneyops.invoices.dto.InvoiceDto;
import com.moneyops.invoices.dto.InvoiceItemDto;
import com.moneyops.invoices.entity.Invoice;
import com.moneyops.invoices.entity.InvoiceItem;
import com.moneyops.invoices.entity.InvoiceStatus;
import com.moneyops.invoices.mapper.InvoiceMapper;
import com.moneyops.invoices.repository.InvoiceRepository;
import com.moneyops.invoices.repository.InvoiceItemRepository;
import com.moneyops.invoices.validator.InvoiceValidator;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;


@Service
@RequiredArgsConstructor
@Transactional
public class InvoiceService {

    private final InvoiceRepository invoiceRepository;
    private final InvoiceItemRepository invoiceItemRepository;
    private final InvoiceMapper invoiceMapper;
    private final InvoiceValidator invoiceValidator;

    public List<InvoiceDto> getAllInvoices(UUID orgId) {
        return invoiceRepository.findAllByOrgId(orgId).stream()
                .map(invoiceMapper::toDto)
                .collect(Collectors.toList());
    }

    public InvoiceDto getInvoiceById(UUID id, UUID orgId) {
        Invoice invoice = invoiceRepository.findByIdAndOrgId(id, orgId)
                .orElseThrow(() -> new RuntimeException("Invoice not found"));
        InvoiceDto dto = invoiceMapper.toDto(invoice);
        dto.setItems(invoiceItemRepository.findByInvoiceId(id).stream()
                .map(invoiceMapper::toItemDto)
                .collect(Collectors.toList()));
        return dto;
    }

    public InvoiceDto createInvoice(InvoiceDto dto, UUID orgId, UUID userId) {
        dto.setId(null); // Ensure new invoice
        invoiceValidator.validate(dto);

        Invoice invoice = invoiceMapper.toEntity(dto);
        invoice.setOrgId(orgId);
        invoice.setCreatedBy(userId);
        invoice.setCreatedAt(LocalDateTime.now());
        invoice.setUpdatedAt(LocalDateTime.now());

        Invoice saved = invoiceRepository.save(invoice);
        if (dto.getItems() != null) {
            for (InvoiceItemDto itemDto : dto.getItems()) {
                InvoiceItem item = invoiceMapper.toItemEntity(itemDto, saved.getId());
                invoiceItemRepository.save(item);
            }
        }
        return getInvoiceById(saved.getId(), orgId);
    }

    public InvoiceDto updateInvoice(UUID id, InvoiceDto dto, UUID orgId) {
        Invoice existing = invoiceRepository.findByIdAndOrgId(id, orgId)
                .orElseThrow(() -> new RuntimeException("Invoice not found"));

        if (existing.getStatus() != InvoiceStatus.DRAFT) {
            throw new IllegalStateException("Can only update draft invoices");
        }

        invoiceValidator.validate(dto);

        Invoice updated = invoiceMapper.toEntity(dto);
        updated.setId(id);
        updated.setOrgId(orgId);
        updated.setCreatedAt(existing.getCreatedAt());
        updated.setCreatedBy(existing.getCreatedBy());
        updated.setUpdatedAt(LocalDateTime.now());

        invoiceItemRepository.deleteByInvoiceId(id);
        Invoice saved = invoiceRepository.save(updated);
        if (dto.getItems() != null) {
            for (InvoiceItemDto itemDto : dto.getItems()) {
                InvoiceItem item = invoiceMapper.toItemEntity(itemDto, saved.getId());
                invoiceItemRepository.save(item);
            }
        }
        return getInvoiceById(saved.getId(), orgId);
    }

    public void deleteInvoice(UUID id, UUID orgId) {
        Invoice invoice = invoiceRepository.findByIdAndOrgId(id, orgId)
                .orElseThrow(() -> new RuntimeException("Invoice not found"));

        if (invoice.getStatus() == InvoiceStatus.PAID) {
            throw new IllegalStateException("Cannot delete paid invoices");
        }

        invoiceRepository.deleteByIdAndOrgId(id, orgId);
    }

    public InvoiceDto sendInvoice(UUID id, UUID orgId) {
        Invoice invoice = invoiceRepository.findByIdAndOrgId(id, orgId)
                .orElseThrow(() -> new RuntimeException("Invoice not found"));

        if (invoice.getStatus() != InvoiceStatus.DRAFT) {
            throw new IllegalStateException("Can only send draft invoices");
        }

        invoice.setStatus(InvoiceStatus.SENT);
        invoice.setUpdatedAt(LocalDateTime.now());
        Invoice saved = invoiceRepository.save(invoice);
        return invoiceMapper.toDto(saved);
    }

    public InvoiceDto markPaid(UUID id, UUID orgId) {
        Invoice invoice = invoiceRepository.findByIdAndOrgId(id, orgId)
                .orElseThrow(() -> new RuntimeException("Invoice not found"));

        if (invoice.getStatus() != InvoiceStatus.SENT) {
            throw new IllegalStateException("Can only mark sent invoices as paid");
        }

        invoice.setStatus(InvoiceStatus.PAID);
        invoice.setPaymentDate(LocalDate.now());
        invoice.setUpdatedAt(LocalDateTime.now());
        Invoice saved = invoiceRepository.save(invoice);
        return invoiceMapper.toDto(saved);
    }

    public List<InvoiceDto> getOverdueInvoices(UUID orgId) {
        return invoiceRepository.findOverdueByOrgId(orgId, LocalDate.now()).stream()
                .map(invoice -> {
                    invoice.setStatus(InvoiceStatus.OVERDUE);
                    invoiceRepository.save(invoice);
                    return invoiceMapper.toDto(invoice);
                })
                .collect(Collectors.toList());
    }

    // InvoiceItem operations
    public InvoiceItemDto addItem(UUID invoiceId, InvoiceItemDto itemDto, UUID orgId) {
        Invoice invoice = invoiceRepository.findByIdAndOrgId(invoiceId, orgId)
                .orElseThrow(() -> new RuntimeException("Invoice not found"));

        if (invoice.getStatus() != InvoiceStatus.DRAFT) {
            throw new IllegalStateException("Can only add items to draft invoices");
        }

        InvoiceItem item = new InvoiceItem();
        item.setInvoice(invoice);
        item.setType(InvoiceItem.ItemType.valueOf(itemDto.getType()));
        item.setDescription(itemDto.getDescription());
        item.setQuantity(itemDto.getQuantity());
        item.setRate(itemDto.getRate());
        item.setGstPercent(itemDto.getGstPercent());

        // Calculate line amounts
        var qty = item.getType() == InvoiceItem.ItemType.SERVICE ? 1 : item.getQuantity();
        var lineSubtotal = item.getRate().multiply(BigDecimal.valueOf(qty));
        var lineGst = lineSubtotal.multiply(item.getGstPercent().divide(BigDecimal.valueOf(100)));
        var lineTotal = lineSubtotal.add(lineGst);

        item.setLineSubtotal(lineSubtotal);
        item.setLineGst(lineGst);
        item.setLineTotal(lineTotal);

        InvoiceItem saved = invoiceItemRepository.save(item);

        // Recalculate invoice totals
        recalculateInvoiceTotals(invoice);

        return invoiceMapper.toItemDto(saved);
    }

    public void updateItem(UUID itemId, InvoiceItemDto itemDto, UUID orgId) {
        InvoiceItem item = invoiceItemRepository.findById(itemId)
                .orElseThrow(() -> new RuntimeException("Item not found"));

        Invoice invoice = invoiceRepository.findByIdAndOrgId(item.getInvoiceId(), orgId)
                .orElseThrow(() -> new RuntimeException("Invoice not found"));

        if (invoice.getStatus() != InvoiceStatus.DRAFT) {
            throw new IllegalStateException("Can only update items in draft invoices");
        }

        item.setDescription(itemDto.getDescription());
        item.setQuantity(itemDto.getQuantity());
        item.setRate(itemDto.getRate());
        item.setGstPercent(itemDto.getGstPercent());

        var qty = item.getType() == InvoiceItem.ItemType.SERVICE ? 1 : item.getQuantity();
        var lineSubtotal = item.getRate().multiply(BigDecimal.valueOf(qty));
        var lineGst = lineSubtotal.multiply(item.getGstPercent().divide(BigDecimal.valueOf(100)));
        var lineTotal = lineSubtotal.add(lineGst);

        item.setLineSubtotal(lineSubtotal);
        item.setLineGst(lineGst);
        item.setLineTotal(lineTotal);

        invoiceItemRepository.save(item);
        recalculateInvoiceTotals(invoice);
    }

    public void deleteItem(UUID itemId, UUID orgId) {
        InvoiceItem item = invoiceItemRepository.findById(itemId)
                .orElseThrow(() -> new RuntimeException("Item not found"));

        Invoice invoice = invoiceRepository.findByIdAndOrgId(item.getInvoiceId(), orgId)
                .orElseThrow(() -> new RuntimeException("Invoice not found"));

        if (invoice.getStatus() != InvoiceStatus.DRAFT) {
            throw new IllegalStateException("Can only delete items from draft invoices");
        }

        invoiceItemRepository.deleteById(itemId);
        recalculateInvoiceTotals(invoice);
    }

    private void recalculateInvoiceTotals(Invoice invoice) {
        List<InvoiceItem> items = invoiceItemRepository.findByInvoiceId(invoice.getId());

        BigDecimal subtotal = BigDecimal.ZERO;
        BigDecimal gstTotal = BigDecimal.ZERO;
        BigDecimal total = BigDecimal.ZERO;

        for (InvoiceItem item : items) {
            subtotal = subtotal.add(item.getLineSubtotal());
            gstTotal = gstTotal.add(item.getLineGst());
            total = total.add(item.getLineTotal());
        }

        invoice.setSubtotal(subtotal);
        invoice.setGstTotal(gstTotal);
        invoice.setTotalAmount(total);
        invoice.setUpdatedAt(LocalDateTime.now());

        invoiceRepository.save(invoice);
    }
}