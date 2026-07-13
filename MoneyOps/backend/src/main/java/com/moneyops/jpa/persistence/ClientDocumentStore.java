package com.moneyops.jpa.persistence;

import com.moneyops.clients.entity.Client;
import com.moneyops.jpa.entity.ClientEntity;
import com.moneyops.jpa.repository.ClientJpaRepository;
import com.moneyops.jpa.util.DocumentJsonMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

@Component
@RequiredArgsConstructor
public class ClientDocumentStore {

    private final ClientJpaRepository clientJpaRepository;
    private final DocumentJsonMapper documentJsonMapper;

    public Client save(Client client) {
        if (client.getId() == null || client.getId().isBlank()) {
            client.setId(UUID.randomUUID().toString());
        }
        if (client.getCreatedAt() == null) {
            client.setCreatedAt(LocalDateTime.now());
        }
        client.setUpdatedAt(LocalDateTime.now());

        ClientEntity entity = new ClientEntity();
        syncColumns(entity, client);
        entity.setDocumentData(documentJsonMapper.toJson(client));
        clientJpaRepository.save(entity);
        return client;
    }

    public Optional<Client> findByIdAndOrgId(String id, String orgId) {
        return clientJpaRepository.findByIdAndOrgIdAndDeletedAtIsNull(id, orgId)
                .map(this::toDocument);
    }

    public List<Client> findAllByOrgId(String orgId) {
        return clientJpaRepository.findByOrgIdAndDeletedAtIsNull(orgId).stream()
                .map(this::toDocument)
                .collect(Collectors.toList());
    }

    public boolean existsByEmailAndOrgId(String email, String orgId) {
        return clientJpaRepository.existsByEmailAndOrgIdAndDeletedAtIsNull(email, orgId);
    }

    public void softDelete(String id, String orgId) {
        clientJpaRepository.findByIdAndOrgIdAndDeletedAtIsNull(id, orgId).ifPresent(entity -> {
            entity.setDeletedAt(LocalDateTime.now());
            Client doc = toDocument(entity);
            if (doc != null) {
                doc.setDeletedAt(entity.getDeletedAt());
                entity.setDocumentData(documentJsonMapper.toJson(doc));
            }
            clientJpaRepository.save(entity);
        });
    }

    private Client toDocument(ClientEntity entity) {
        Client doc = documentJsonMapper.fromJson(entity.getDocumentData(), Client.class);
        if (doc == null) {
            doc = new Client();
        }
        syncDocumentFromColumns(doc, entity);
        return doc;
    }

    private void syncColumns(ClientEntity entity, Client client) {
        entity.setId(client.getId());
        entity.setOrgId(client.getOrgId());
        entity.setName(client.getName());
        entity.setGstin(client.getGstin());
        entity.setEmail(client.getEmail());
        entity.setPhoneNumber(client.getPhoneNumber());
        entity.setCompany(client.getCompany());
        entity.setCurrency(client.getCurrency());
        entity.setNotes(client.getNotes());
        entity.setStatus(client.getStatus() != null ? client.getStatus().name() : "ACTIVE");
        entity.setCreatedAt(client.getCreatedAt());
        entity.setUpdatedAt(client.getUpdatedAt());
        entity.setCreatedBy(client.getCreatedBy());
        entity.setUpdatedBy(client.getUpdatedBy());
        entity.setDeletedAt(client.getDeletedAt());
    }

    private void syncDocumentFromColumns(Client doc, ClientEntity entity) {
        doc.setId(entity.getId());
        doc.setOrgId(entity.getOrgId());
        doc.setName(entity.getName());
        doc.setGstin(entity.getGstin());
        doc.setEmail(entity.getEmail());
        doc.setPhoneNumber(entity.getPhoneNumber());
        doc.setCompany(entity.getCompany());
        doc.setCurrency(entity.getCurrency());
        doc.setNotes(entity.getNotes());
        if (entity.getStatus() != null) {
            doc.setStatus(Client.Status.valueOf(entity.getStatus()));
        }
        doc.setCreatedAt(entity.getCreatedAt());
        doc.setUpdatedAt(entity.getUpdatedAt());
        doc.setCreatedBy(entity.getCreatedBy());
        doc.setUpdatedBy(entity.getUpdatedBy());
        doc.setDeletedAt(entity.getDeletedAt());
    }
}
