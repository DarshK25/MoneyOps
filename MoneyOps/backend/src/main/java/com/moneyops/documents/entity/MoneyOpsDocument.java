package com.moneyops.documents.entity;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.LocalDateTime;
import java.util.UUID;

@Document(collection = "documents")
@Data
public class MoneyOpsDocument {

    @Id
    private String id = UUID.randomUUID().toString();

    private String orgId;
    private String name;
    private String type;
    private Long size;
    private String firebasePath;
    private String downloadUrl;
    private String mimeType;
    private String uploadedBy;
    private String linkedEntityType;
    private String linkedEntityId;
    private LocalDateTime createdAt = LocalDateTime.now();
    private boolean isConfidential = false;
    private String category;
    private String contentSummary;
    private java.util.List<String> detectedDeadlines;
}
