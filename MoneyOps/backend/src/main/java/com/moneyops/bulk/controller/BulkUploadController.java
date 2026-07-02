package com.moneyops.bulk.controller;

import com.moneyops.bulk.dto.BulkUploadResponse;
import com.moneyops.bulk.service.BulkUploadService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

/**
 * Bulk CSV Upload Controller
 * 
 * Endpoints:
 * - POST /api/bulk/upload/invoices - Upload invoices via CSV
 * - POST /api/bulk/upload/clients - Upload clients via CSV
 * 
 * CSV Format Documentation:
 * - Invoice CSV: clientName,clientEmail,description,quantity,unitPrice,gstRate,dueDate
 * - Client CSV: name,email,phone,gstin,billingAddress,city,state,paymentTerms
 */
@RestController
@RequestMapping("/api/bulk")
@RequiredArgsConstructor
@Slf4j
public class BulkUploadController {

    private final BulkUploadService bulkUploadService;

    /**
     * Upload invoices via CSV file
     * Expected CSV format: clientName,clientEmail,description,quantity,unitPrice,gstRate,dueDate
     */
    @PostMapping("/upload/invoices")
    public ResponseEntity<BulkUploadResponse> uploadInvoices(
            @RequestParam("file") MultipartFile file,
            @RequestHeader("X-Org-Id") String orgId) {
        
        log.info("Received invoice bulk upload request for org: {}, file: {}", orgId, file.getOriginalFilename());
        
        if (file.isEmpty()) {
            BulkUploadResponse response = new BulkUploadResponse();
            response.setErrors(List.of("File is empty"));
            response.setSuccessCount(0);
            response.setFailureCount(0);
            response.setSuccessfulIds(List.of());
            return ResponseEntity.badRequest().body(response);
        }

        BulkUploadResponse response = bulkUploadService.uploadInvoices(file, orgId);
        return ResponseEntity.ok(response);
    }

    /**
     * Upload clients via CSV file
     * Expected CSV format: name,email,phone,gstin,billingAddress,city,state,paymentTerms
     */
    @PostMapping("/upload/clients")
    public ResponseEntity<BulkUploadResponse> uploadClients(
            @RequestParam("file") MultipartFile file,
            @RequestHeader("X-Org-Id") String orgId) {
        
        log.info("Received client bulk upload request for org: {}, file: {}", orgId, file.getOriginalFilename());
        
        if (file.isEmpty()) {
            BulkUploadResponse response = new BulkUploadResponse();
            response.setErrors(List.of("File is empty"));
            response.setSuccessCount(0);
            response.setFailureCount(0);
            response.setSuccessfulIds(List.of());
            return ResponseEntity.badRequest().body(response);
        }

        BulkUploadResponse response = bulkUploadService.uploadClients(file, orgId);
        return ResponseEntity.ok(response);
    }
}
