package com.moneyops.audit.repository;

import com.moneyops.audit.entity.AuditLog;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Repository
public interface AuditLogRepository extends MongoRepository<AuditLog, UUID> {

    List<AuditLog> findByOrgIdOrderByTimestampDesc(UUID orgId);
    List<AuditLog> findByOrgIdAndEntityTypeOrderByTimestampDesc(UUID orgId, String entityType);
    List<AuditLog> findByOrgIdAndEntityIdOrderByTimestampDesc(UUID orgId, String entityId);
    List<AuditLog> findByOrgIdAndUserIdOrderByTimestampDesc(UUID orgId, UUID userId);
    List<AuditLog> findByOrgIdAndTimestampBetweenOrderByTimestampDesc(UUID orgId, LocalDateTime start, LocalDateTime end);
    List<AuditLog> findByOrgIdAndOperationOrderByTimestampDesc(UUID orgId, AuditLog.Operation operation);
}
