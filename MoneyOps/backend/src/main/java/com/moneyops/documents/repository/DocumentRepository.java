package com.moneyops.documents.repository;

import com.moneyops.documents.entity.Document;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;
import java.util.UUID;

public interface DocumentRepository extends MongoRepository<Document, UUID> {

    List<Document> findByOrgId(UUID orgId);
    List<Document> findByLinkedEntityTypeAndLinkedEntityId(String linkedEntityType, UUID linkedEntityId);
}
