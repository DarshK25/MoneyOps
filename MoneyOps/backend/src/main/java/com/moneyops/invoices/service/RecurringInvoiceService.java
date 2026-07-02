package com.moneyops.invoices.service;

import com.moneyops.clients.repository.ClientRepository;
import com.moneyops.invoices.dto.InvoiceDto;
import com.moneyops.invoices.dto.InvoiceItemDto;
import com.moneyops.invoices.dto.RecurringInvoiceDto;
import com.moneyops.invoices.entity.Invoice;
import com.moneyops.invoices.entity.InvoiceItem;
import com.moneyops.invoices.entity.RecurringInvoice;
import com.moneyops.invoices.mapper.RecurringInvoiceMapper;
import com.moneyops.invoices.repository.InvoiceRepository;
import com.moneyops.invoices.repository.RecurringInvoiceRepository;
import com.moneyops.invoices.validator.InvoiceValidator;
import com.moneyops.invoices.mapper.InvoiceMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
@RequiredArgsConstructor
@Transactional
public class RecurringInvoiceService {

    private final RecurringInvoiceRepository recurringInvoiceRepository;
    private final RecurringInvoiceMapper recurringInvoiceMapper;
    private final InvoiceRepository invoiceRepository;
    private final InvoiceService invoiceService;
    private final InvoiceMapper invoiceMapper;
    private final ClientRepository clientRepository;
    private final InvoiceValidator invoiceValidator;

    public RecurringInvoiceDto createRecurringInvoice(RecurringInvoiceDto dto, String orgId, String userId) {
        if (orgId == null || orgId.isBlank()) {
            throw new com.moneyops.shared.exceptions.UnauthorizedException("Missing organization context");
        }

        if (dto.getClientId() != null) {
            clientRepository.findByIdAndOrgIdAndDeletedAtIsNull(dto.getClientId(), orgId)
                    .ifPresentOrElse(client -> {
                        dto.setClientName(client.getName());
                        dto.setClientEmail(client.getEmail());
                        dto.setClientCompany(client.getCompany());
                        dto.setClientPhone(client.getPhoneNumber());
                    }, () -> {
                        throw new ResponseStatusException(NOT_FOUND, "Client not found.");
                    });
        }

        RecurringInvoice entity = recurringInvoiceMapper.toEntity(dto);
        entity.setOrgId(orgId);
        entity.setIsActive(true);
        entity.setLastGenerated(null);
        entity.setCreatedAt(LocalDateTime.now());
        entity.setUpdatedAt(LocalDateTime.now());

        if (entity.getCurrency() == null) {
            entity.setCurrency("INR");
        }
        if (entity.getPaymentTerms() == null) {
            entity.setPaymentTerms(30);
        }
        if (entity.getInterval() == null) {
            entity.setInterval(1);
        }

        RecurringInvoice saved = recurringInvoiceRepository.save(entity);
        return recurringInvoiceMapper.toDto(saved);
    }

    public List<RecurringInvoiceDto> getActiveRecurringInvoices(String orgId) {
        List<RecurringInvoice> entities = recurringInvoiceRepository.findByOrgIdAndIsActiveTrue(orgId);
        return entities.stream()
                .map(recurringInvoiceMapper::toDto)
                .collect(Collectors.toList());
    }

    public RecurringInvoiceDto updateRecurringInvoice(String id, RecurringInvoiceDto dto, String orgId) {
        RecurringInvoice existing = recurringInvoiceRepository.findByIdAndOrgId(id, orgId).stream()
                .findFirst()
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Recurring invoice not found"));

        if (dto.getClientId() != null && !dto.getClientId().equals(existing.getClientId())) {
            clientRepository.findByIdAndOrgIdAndDeletedAtIsNull(dto.getClientId(), orgId)
                    .ifPresentOrElse(client -> {
                        dto.setClientName(client.getName());
                        dto.setClientEmail(client.getEmail());
                        dto.setClientCompany(client.getCompany());
                        dto.setClientPhone(client.getPhoneNumber());
                    }, () -> {
                        throw new ResponseStatusException(NOT_FOUND, "Client not found.");
                    });
        }

        RecurringInvoice updated = recurringInvoiceMapper.toEntity(dto);
        updated.setId(id);
        updated.setOrgId(orgId);
        updated.setCreatedAt(existing.getCreatedAt());
        updated.setUpdatedAt(LocalDateTime.now());

        if (updated.getIsActive() == null) {
            updated.setIsActive(existing.getIsActive());
        }

        RecurringInvoice saved = recurringInvoiceRepository.save(updated);
        return recurringInvoiceMapper.toDto(saved);
    }

    public void deactivateRecurringInvoice(String id, String orgId) {
        RecurringInvoice existing = recurringInvoiceRepository.findByIdAndOrgId(id, orgId).stream()
                .findFirst()
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Recurring invoice not found"));

        existing.setIsActive(false);
        existing.setUpdatedAt(LocalDateTime.now());
        recurringInvoiceRepository.save(existing);
    }

    public Invoice generateInvoiceFromRecurring(String recurringInvoiceId, String orgId, String userId) {
        RecurringInvoice recurring = recurringInvoiceRepository.findByIdAndOrgId(recurringInvoiceId, orgId).stream()
                .findFirst()
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Recurring invoice not found"));

        if (!recurring.getIsActive()) {
            throw new IllegalStateException("Cannot generate invoice from inactive recurring invoice");
        }

        Invoice invoice = new Invoice();
        invoice.setId(UUID.randomUUID().toString());
        invoice.setOrgId(orgId);
        invoice.setClientId(recurring.getClientId());
        invoice.setClientName(recurring.getClientName());
        invoice.setClientEmail(recurring.getClientEmail());
        invoice.setClientCompany(recurring.getClientCompany());
        invoice.setClientPhone(recurring.getClientPhone());

        LocalDate issueDate = LocalDate.now();
        invoice.setIssueDate(issueDate);
        invoice.setDueDate(issueDate.plusDays(recurring.getPaymentTerms() != null ? recurring.getPaymentTerms() : 30));

        invoice.setCurrency(recurring.getCurrency() != null ? recurring.getCurrency() : "INR");
        invoice.setNotes(recurring.getNotes());
        invoice.setStatus(com.moneyops.invoices.entity.InvoiceStatus.DRAFT);

        if (recurring.getItems() != null) {
            List<InvoiceItem> items = recurring.getItems().stream().map(item -> {
                InvoiceItem newItem = new InvoiceItem();
                newItem.setType(item.getType());
                newItem.setDescription(item.getDescription());
                newItem.setQuantity(item.getQuantity());
                newItem.setRate(item.getRate());
                newItem.setGstPercent(item.getGstPercent());
                newItem.setLineSubtotal(item.getLineSubtotal());
                newItem.setLineGst(item.getLineGst());
                newItem.setLineTotal(item.getLineTotal());
                return newItem;
            }).collect(Collectors.toList());
            invoice.setItems(items);
        }

        invoice.setAmountPaid(BigDecimal.ZERO);
        invoice.setBalanceDue(BigDecimal.ZERO);

        calculateInvoiceTotals(invoice);

        String dateStamp = java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd").format(issueDate);
        String randomStr = UUID.randomUUID().toString().substring(0, 4).toUpperCase();
        invoice.setInvoiceNumber("INV-" + dateStamp + "-" + randomStr);

        invoice.setCreatedAt(LocalDateTime.now());
        invoice.setUpdatedAt(LocalDateTime.now());

        Invoice saved = invoiceRepository.save(invoice);

        recurring.setLastGenerated(issueDate);
        recurring.setUpdatedAt(LocalDateTime.now());
        recurringInvoiceRepository.save(recurring);

        return saved;
    }

    public InvoiceDto generateInvoiceFromRecurringDto(String recurringInvoiceId, String orgId, String userId) {
        return invoiceMapper.toDto(generateInvoiceFromRecurring(recurringInvoiceId, orgId, userId));
    }

    public void processDueRecurringInvoices() {
        LocalDate now = LocalDate.now();
        List<RecurringInvoice> activeInvoices = recurringInvoiceRepository.findByIsActiveTrueAndLastGeneratedLessThanEqual(now);

        for (RecurringInvoice recurring : activeInvoices) {
            try {
                if (isDue(recurring, now)) {
                    generateInvoiceFromRecurring(recurring.getId(), recurring.getOrgId(), null);
                }
            } catch (Exception e) {
                System.err.println("Failed to generate invoice for recurring invoice " + recurring.getId() + ": " + e.getMessage());
            }
        }
    }

    private boolean isDue(RecurringInvoice recurring, LocalDate now) {
        if (recurring.getEndDate() != null && now.isAfter(recurring.getEndDate())) {
            return false;
        }

        LocalDate lastGen = recurring.getLastGenerated();
        if (lastGen == null) {
            return !now.isBefore(recurring.getStartDate());
        }

        int interval = recurring.getInterval() != null ? recurring.getInterval() : 1;
        LocalDate nextDate = switch (recurring.getFrequency()) {
            case "DAILY" -> lastGen.plusDays(interval);
            case "WEEKLY" -> lastGen.plusWeeks(interval);
            case "MONTHLY" -> lastGen.plusMonths(interval);
            case "YEARLY" -> lastGen.plusYears(interval);
            default -> lastGen;
        };

        return !now.isBefore(nextDate);
    }

    private void calculateInvoiceTotals(Invoice invoice) {
        BigDecimal subtotal = BigDecimal.ZERO;
        BigDecimal gstTotal = BigDecimal.ZERO;
        BigDecimal totalAmount = BigDecimal.ZERO;

        if (invoice.getItems() != null) {
            for (InvoiceItem item : invoice.getItems()) {
                subtotal = subtotal.add(item.getLineSubtotal());
                gstTotal = gstTotal.add(item.getLineGst());
                totalAmount = totalAmount.add(item.getLineTotal());
            }
        }

        invoice.setSubtotal(subtotal);
        invoice.setGstTotal(gstTotal);
        invoice.setTotalAmount(totalAmount);
        invoice.setBalanceDue(totalAmount.subtract(
                invoice.getAmountPaid() != null ? invoice.getAmountPaid() : BigDecimal.ZERO));
    }
}
