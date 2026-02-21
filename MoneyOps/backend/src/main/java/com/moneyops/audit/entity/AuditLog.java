package com.moneyops.audit.entity;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.LocalDateTime;
import java.util.UUID;

@Document(collection = "audit_logs")
@Data
public class AuditLog {
    @Id
    private UUID id = UUID.randomUUID();

    private UUID orgId;
    private UUID userId;
    private String entityType;
    private String entityId;
    private Operation operation;
    private String oldValues;
    private String newValues;
    private String changes;
    private String ipAddress;
    private String userAgent;
    private LocalDateTime timestamp = LocalDateTime.now();

    public enum Operation {
        CREATE, UPDATE, DELETE
    }
}
