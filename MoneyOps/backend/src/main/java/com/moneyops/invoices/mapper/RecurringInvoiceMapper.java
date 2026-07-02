package com.moneyops.invoices.mapper;

import com.moneyops.invoices.dto.InvoiceItemDto;
import com.moneyops.invoices.dto.RecurringInvoiceDto;
import com.moneyops.invoices.entity.InvoiceItem;
import com.moneyops.invoices.entity.RecurringInvoice;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.util.List;
import java.util.stream.Collectors;

@Component
public class RecurringInvoiceMapper {

    public RecurringInvoiceDto toDto(RecurringInvoice entity) {
        RecurringInvoiceDto dto = new RecurringInvoiceDto();
        dto.setId(entity.getId());
        dto.setOrgId(entity.getOrgId());
        dto.setClientId(entity.getClientId());
        dto.setClientName(entity.getClientName());
        dto.setClientEmail(entity.getClientEmail());
        dto.setClientCompany(entity.getClientCompany());
        dto.setClientPhone(entity.getClientPhone());
        dto.setFrequency(entity.getFrequency());
        dto.setInterval(entity.getInterval());
        dto.setStartDate(entity.getStartDate());
        dto.setEndDate(entity.getEndDate());
        dto.setLastGenerated(entity.getLastGenerated());
        dto.setIsActive(entity.getIsActive());
        dto.setCurrency(entity.getCurrency());
        dto.setPaymentTerms(entity.getPaymentTerms());
        dto.setNotes(entity.getNotes());
        dto.setCreatedAt(entity.getCreatedAt());
        dto.setUpdatedAt(entity.getUpdatedAt());

        if (entity.getItems() != null) {
            dto.setItems(entity.getItems().stream()
                    .map(this::toItemDto)
                    .collect(Collectors.toList()));
        }

        dto.setNextGenerationDate(calculateNextGenerationDate(entity));
        return dto;
    }

    public RecurringInvoice toEntity(RecurringInvoiceDto dto) {
        RecurringInvoice entity = new RecurringInvoice();
        entity.setId(dto.getId());
        entity.setOrgId(dto.getOrgId());
        entity.setClientId(dto.getClientId());
        entity.setClientName(dto.getClientName());
        entity.setClientEmail(dto.getClientEmail());
        entity.setClientCompany(dto.getClientCompany());
        entity.setClientPhone(dto.getClientPhone());
        entity.setFrequency(dto.getFrequency());
        entity.setInterval(dto.getInterval() != null ? dto.getInterval() : 1);
        entity.setStartDate(dto.getStartDate());
        entity.setEndDate(dto.getEndDate());
        entity.setLastGenerated(dto.getLastGenerated());
        entity.setIsActive(dto.getIsActive() != null ? dto.getIsActive() : true);
        entity.setCurrency(dto.getCurrency());
        entity.setPaymentTerms(dto.getPaymentTerms() != null ? dto.getPaymentTerms() : 30);
        entity.setNotes(dto.getNotes());

        if (dto.getItems() != null) {
            entity.setItems(dto.getItems().stream()
                    .map(this::toItemEntity)
                    .collect(Collectors.toList()));
        }
        return entity;
    }

    private InvoiceItemDto toItemDto(InvoiceItem item) {
        InvoiceItemDto dto = new InvoiceItemDto();
        dto.setType(item.getType().name());
        dto.setDescription(item.getDescription());
        dto.setQuantity(item.getQuantity());
        dto.setRate(item.getRate());
        dto.setGstPercent(item.getGstPercent());
        dto.setLineSubtotal(item.getLineSubtotal());
        dto.setLineGst(item.getLineGst());
        dto.setLineTotal(item.getLineTotal());
        return dto;
    }

    private InvoiceItem toItemEntity(InvoiceItemDto dto) {
        InvoiceItem item = new InvoiceItem();
        item.setType(InvoiceItem.ItemType.valueOf(dto.getType()));
        item.setDescription(dto.getDescription());
        item.setQuantity(dto.getQuantity());
        item.setRate(dto.getRate());
        item.setGstPercent(dto.getGstPercent());
        item.setLineSubtotal(dto.getLineSubtotal());
        item.setLineGst(dto.getLineGst());
        item.setLineTotal(dto.getLineTotal());
        return item;
    }

    private LocalDate calculateNextGenerationDate(RecurringInvoice entity) {
        if (entity.getLastGenerated() == null) {
            return entity.getStartDate();
        }

        LocalDate from = entity.getLastGenerated();
        int interval = entity.getInterval() != null ? entity.getInterval() : 1;

        return switch (entity.getFrequency()) {
            case "DAILY" -> from.plusDays(interval);
            case "WEEKLY" -> from.plusWeeks(interval);
            case "MONTHLY" -> from.plusMonths(interval);
            case "YEARLY" -> from.plusYears(interval);
            default -> from;
        };
    }
}
