package com.moneyops.bulk.dto;

import lombok.Data;
import java.util.List;

@Data
public class BulkUploadResponse {
    private int successCount;
    private int failureCount;
    private List<String> errors;
    private List<String> successfulIds;
}
