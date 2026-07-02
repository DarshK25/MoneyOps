package com.moneyops.bulk.service;

import com.moneyops.bulk.dto.BulkUploadResponse;
import com.moneyops.clients.entity.Client;
import com.moneyops.clients.repository.ClientRepository;
import com.moneyops.invoices.entity.Invoice;
import com.moneyops.invoices.entity.InvoiceItem;
import com.moneyops.invoices.entity.InvoiceStatus;
import com.moneyops.invoices.repository.InvoiceRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Bulk CSV Upload Service
 * 
 * CSV Format Documentation:
 * - Invoice CSV: clientName,clientEmail,description,quantity,unitPrice,gstRate,dueDate
 * - Client CSV: name,email,phone,gstin,billingAddress,city,state,paymentTerms
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class BulkUploadService {

    private final InvoiceRepository invoiceRepository;
    private final ClientRepository clientRepository;

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    /**
     * Parse and process invoice CSV upload
     * Expected CSV format: clientName,clientEmail,description,quantity,unitPrice,gstRate,dueDate
     */
    public BulkUploadResponse uploadInvoices(MultipartFile file, String orgId) {
        BulkUploadResponse response = new BulkUploadResponse();
        response.setErrors(new ArrayList<>());
        response.setSuccessfulIds(new ArrayList<>());
        int successCount = 0;
        int failureCount = 0;

        try (BufferedReader reader = new BufferedReader(new InputStreamReader(file.getInputStream()))) {
            String line;
            int lineNumber = 0;

            while ((line = reader.readLine()) != null) {
                lineNumber++;
                
                // Skip header row
                if (lineNumber == 1 && line.toLowerCase().contains("clientname")) {
                    continue;
                }

                if (line.trim().isEmpty()) {
                    continue;
                }

                try {
                    Invoice invoice = parseInvoiceLine(line, orgId);
                    if (invoice != null) {
                        invoiceRepository.save(invoice);
                        response.getSuccessfulIds().add(invoice.getId());
                        successCount++;
                    }
                } catch (Exception e) {
                    failureCount++;
                    response.getErrors().add("Line " + lineNumber + ": " + e.getMessage());
                    log.warn("Failed to parse invoice CSV line {}: {}", lineNumber, e.getMessage());
                }
            }
        } catch (Exception e) {
            log.error("Error reading invoice CSV file", e);
            response.getErrors().add("File read error: " + e.getMessage());
        }

        response.setSuccessCount(successCount);
        response.setFailureCount(failureCount);
        return response;
    }

    /**
     * Parse and process client CSV upload
     * Expected CSV format: name,email,phone,gstin,billingAddress,city,state,paymentTerms
     */
    public BulkUploadResponse uploadClients(MultipartFile file, String orgId) {
        BulkUploadResponse response = new BulkUploadResponse();
        response.setErrors(new ArrayList<>());
        response.setSuccessfulIds(new ArrayList<>());
        int successCount = 0;
        int failureCount = 0;

        try (BufferedReader reader = new BufferedReader(new InputStreamReader(file.getInputStream()))) {
            String line;
            int lineNumber = 0;

            while ((line = reader.readLine()) != null) {
                lineNumber++;
                
                // Skip header row
                if (lineNumber == 1 && line.toLowerCase().contains("name")) {
                    continue;
                }

                if (line.trim().isEmpty()) {
                    continue;
                }

                try {
                    Client client = parseClientLine(line, orgId);
                    if (client != null) {
                        clientRepository.save(client);
                        response.getSuccessfulIds().add(client.getId());
                        successCount++;
                    }
                } catch (Exception e) {
                    failureCount++;
                    response.getErrors().add("Line " + lineNumber + ": " + e.getMessage());
                    log.warn("Failed to parse client CSV line {}: {}", lineNumber, e.getMessage());
                }
            }
        } catch (Exception e) {
            log.error("Error reading client CSV file", e);
            response.getErrors().add("File read error: " + e.getMessage());
        }

        response.setSuccessCount(successCount);
        response.setFailureCount(failureCount);
        return response;
    }

    private Invoice parseInvoiceLine(String line, String orgId) {
        // Split by comma, handling quoted values
        String[] parts = parseCsvLine(line);
        
        if (parts.length < 7) {
            throw new IllegalArgumentException("Invalid invoice CSV format. Expected 7 columns, got " + parts.length);
        }

        String clientName = parts[0].trim();
        String clientEmail = parts[1].trim();
        String description = parts[2].trim();
        String quantityStr = parts[3].trim();
        String unitPriceStr = parts[4].trim();
        String gstRateStr = parts[5].trim();
        String dueDateStr = parts[6].trim();

        // Validate required fields
        if (clientName.isEmpty()) {
            throw new IllegalArgumentException("Client name is required");
        }
        if (clientEmail.isEmpty()) {
            throw new IllegalArgumentException("Client email is required");
        }
        if (!isValidEmail(clientEmail)) {
            throw new IllegalArgumentException("Invalid email format: " + clientEmail);
        }

        // Parse numeric values
        BigDecimal quantity;
        BigDecimal unitPrice;
        BigDecimal gstRate;
        
        try {
            quantity = new BigDecimal(quantityStr);
            unitPrice = new BigDecimal(unitPriceStr);
            gstRate = new BigDecimal(gstRateStr);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("Invalid numeric value: " + e.getMessage());
        }

        // Parse due date
        LocalDate dueDate;
        try {
            dueDate = LocalDate.parse(dueDateStr, DATE_FORMATTER);
        } catch (Exception e) {
            throw new IllegalArgumentException("Invalid date format. Expected yyyy-MM-dd, got: " + dueDateStr);
        }

        // Calculate amounts
        BigDecimal lineSubtotal = unitPrice.multiply(quantity);
        BigDecimal lineGst = lineSubtotal.multiply(gstRate.divide(BigDecimal.valueOf(100)));
        BigDecimal lineTotal = lineSubtotal.add(lineGst);

        // Create invoice item
        InvoiceItem item = new InvoiceItem();
        item.setDescription(description);
        item.setQuantity(quantity.intValue());
        item.setRate(unitPrice);
        item.setGstPercent(gstRate);
        item.setLineSubtotal(lineSubtotal);
        item.setLineGst(lineGst);
        item.setLineTotal(lineTotal);
        item.setType(InvoiceItem.ItemType.PRODUCT);

        // Create invoice
        Invoice invoice = new Invoice();
        invoice.setId(UUID.randomUUID().toString());
        invoice.setOrgId(orgId);
        invoice.setClientName(clientName);
        invoice.setClientEmail(clientEmail);
        invoice.setInvoiceNumber(generateInvoiceNumber());
        invoice.setIssueDate(LocalDate.now());
        invoice.setDueDate(dueDate);
        invoice.setStatus(InvoiceStatus.DRAFT);
        invoice.setCurrency("INR");
        
        List<InvoiceItem> items = new ArrayList<>();
        items.add(item);
        invoice.setItems(items);
        
        invoice.setSubtotal(lineSubtotal);
        invoice.setGstTotal(lineGst);
        invoice.setTotalAmount(lineTotal);
        invoice.setAmountPaid(BigDecimal.ZERO);
        invoice.setBalanceDue(lineTotal);
        invoice.setCreatedAt(java.time.LocalDateTime.now());
        invoice.setUpdatedAt(java.time.LocalDateTime.now());

        return invoice;
    }

    private Client parseClientLine(String line, String orgId) {
        // Split by comma, handling quoted values
        String[] parts = parseCsvLine(line);
        
        if (parts.length < 8) {
            throw new IllegalArgumentException("Invalid client CSV format. Expected 8 columns, got " + parts.length);
        }

        String name = parts[0].trim();
        String email = parts[1].trim();
        String phone = parts[2].trim();
        String gstin = parts[3].trim();
        String billingAddress = parts[4].trim();
        String city = parts[5].trim();
        String state = parts[6].trim();
        String paymentTermsStr = parts[7].trim();

        // Validate required fields
        if (name.isEmpty()) {
            throw new IllegalArgumentException("Client name is required");
        }
        if (!email.isEmpty() && !isValidEmail(email)) {
            throw new IllegalArgumentException("Invalid email format: " + email);
        }
        if (!gstin.isEmpty() && !isValidGstin(gstin)) {
            throw new IllegalArgumentException("Invalid GSTIN format: " + gstin);
        }

        // Check for duplicate email within org
        if (!email.isEmpty() && clientRepository.existsByEmailAndOrgIdAndDeletedAtIsNull(email, orgId)) {
            throw new IllegalArgumentException("Client with email " + email + " already exists");
        }

        // Parse payment terms
        Integer paymentTerms = null;
        if (!paymentTermsStr.isEmpty()) {
            try {
                paymentTerms = Integer.parseInt(paymentTermsStr);
            } catch (NumberFormatException e) {
                throw new IllegalArgumentException("Invalid payment terms: " + paymentTermsStr);
            }
        }

        // Create client
        Client client = new Client();
        client.setId(UUID.randomUUID().toString());
        client.setOrgId(orgId);
        client.setName(name);
        client.setEmail(email);
        client.setPhoneNumber(phone);
        client.setGstin(gstin);
        client.setPaymentTerms(paymentTerms);
        client.setStatus(Client.Status.ACTIVE);
        client.setCurrency("INR");
        client.setCreatedAt(java.time.LocalDateTime.now());
        client.setUpdatedAt(java.time.LocalDateTime.now());

        // Set billing address
        if (!billingAddress.isEmpty() || !city.isEmpty() || !state.isEmpty()) {
            Client.Address address = new Client.Address();
            address.setLine1(billingAddress);
            address.setCity(city);
            address.setState(state);
            address.setCountry("India");
            client.setBillingAddress(address);
        }

        return client;
    }

    private String[] parseCsvLine(String line) {
        List<String> result = new ArrayList<>();
        StringBuilder current = new StringBuilder();
        boolean inQuotes = false;
        
        for (int i = 0; i < line.length(); i++) {
            char c = line.charAt(i);
            if (c == '"') {
                inQuotes = !inQuotes;
            } else if (c == ',' && !inQuotes) {
                result.add(current.toString().trim());
                current = new StringBuilder();
            } else {
                current.append(c);
            }
        }
        result.add(current.toString().trim());
        
        return result.toArray(new String[0]);
    }

    private String generateInvoiceNumber() {
        String dateStamp = java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd").format(java.time.LocalDate.now());
        String randomStr = UUID.randomUUID().toString().substring(0, 4).toUpperCase();
        return "INV-" + dateStamp + "-" + randomStr;
    }

    private boolean isValidEmail(String email) {
        return email != null && email.matches("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$");
    }

    private boolean isValidGstin(String gstin) {
        // GSTIN format: 15 characters (2 state + 10 PAN + 1 entity + 1 check + 1 optional)
        return gstin != null && gstin.matches("^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$");
    }
}
