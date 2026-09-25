package com.moneyops.clients.service;

import com.moneyops.clients.dto.ClientDto;
import com.moneyops.clients.entity.Client;
import com.moneyops.clients.mapper.ClientMapper;
import com.moneyops.clients.validator.ClientValidator;
import com.moneyops.audit.service.AuditLogService;
import com.moneyops.events.producer.IEventPublisher;
import com.moneyops.jpa.persistence.ClientDocumentStore;
import com.moneyops.security.team.TeamActionAuthorizationService;
import com.moneyops.shared.exceptions.BusinessRuleException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;
import org.apache.commons.text.similarity.JaroWinklerSimilarity;

@Slf4j
@Service
@Transactional
public class ClientService {

    @Autowired
    private ClientDocumentStore clientStore;

    @Autowired
    private ClientMapper clientMapper;

    @Autowired
    private ClientValidator clientValidator;

    @Autowired
    private TeamActionAuthorizationService teamActionAuthorizationService;

    @Autowired
    private AuditLogService auditLogService;

    @Autowired(required = false)
    private IEventPublisher eventPublisher;

    private static final String TOPIC_CLIENT_EVENTS = "moneyops.client.events";

    public List<ClientDto> getAllClients(String orgId) {
        if (orgId == null || orgId.isBlank()) {
            throw new com.moneyops.shared.exceptions.UnauthorizedException("Missing organization context");
        }
        return clientStore.findAllByOrgId(orgId).stream()
                .map(clientMapper::toDto)
                .collect(Collectors.toList());
    }

    public Page<ClientDto> getClients(String orgId, String status, int page, int size) {
        List<ClientDto> clients = getAllClients(orgId);
        if (status != null && !status.isBlank()) {
            clients = clients.stream()
                    .filter(client -> status.equalsIgnoreCase(client.getStatus()))
                    .collect(Collectors.toList());
        }

        Pageable pageable = PageRequest.of(page, size);
        int start = Math.min((int) pageable.getOffset(), clients.size());
        int end = Math.min(start + pageable.getPageSize(), clients.size());
        return new PageImpl<>(clients.subList(start, end), pageable, clients.size());
    }

    public ClientDto getClientById(String id, String orgId) {
        Client client = clientStore.findByIdAndOrgId(id, orgId)
                .orElseThrow(() -> new RuntimeException("Client not found"));
        return clientMapper.toDto(client);
    }

    public ClientDto createClient(ClientDto dto, String orgId, String createdBy) {
        if (orgId == null || orgId.isBlank()) {
            throw new com.moneyops.shared.exceptions.UnauthorizedException("Missing organization context");
        }
        if (createdBy == null || createdBy.isBlank()) {
            throw new com.moneyops.shared.exceptions.UnauthorizedException("Missing user context");
        }

        var creator = teamActionAuthorizationService.assertUserCanCreateSensitiveAction(
                orgId, createdBy, dto.getTeamActionCode());

        if (dto.getSource() == null || dto.getSource().isBlank()) {
            dto.setSource("MANUAL");
        }

        if (dto.getStatus() == null || dto.getStatus().trim().isEmpty()) {
            dto.setStatus("ACTIVE");
        }
        clientValidator.validate(dto);

        Client client = clientMapper.toEntity(dto);
        if (client.getEmail() != null && !client.getEmail().isBlank()
                && clientStore.existsByEmailAndOrgId(client.getEmail(), orgId)) {
            throw new BusinessRuleException("Client with this email already exists");
        }

        client.setOrgId(orgId);
        client.setCreatedBy(creator.userId());
        client.setCreatedByEmail(creator.email());
        client.setCreatedByRole(creator.role());
        client.setSource(dto.getSource());
        client.setCreatedAt(LocalDateTime.now());
        client.setUpdatedAt(LocalDateTime.now());

        Client saved = clientStore.save(client);
        auditLogService.logCreate("CLIENT", saved.getId(), saved);
        
        // Publish Kafka event
        publishClientEvent(saved, "CLIENT_CREATED", "Client created via " + dto.getSource());
        
        return clientMapper.toDto(saved);
    }

    public ClientDto updateClient(String id, ClientDto dto, String orgId, String updatedBy) {
        clientValidator.validate(dto);
        Client client = clientStore.findByIdAndOrgId(id, orgId)
                .orElseThrow(() -> new RuntimeException("Client not found"));

        client.setName(dto.getName());
        client.setGstin(dto.getGstin());
        client.setEmail(dto.getEmail());
        client.setPhoneNumber(dto.getPhoneNumber());

        if (dto.getBillingAddress() != null) {
            client.setBillingAddress(clientMapper.toEntity(dto).getBillingAddress());
        }
        if (dto.getShippingAddress() != null) {
            client.setShippingAddress(clientMapper.toEntity(dto).getShippingAddress());
        }

        client.setPaymentTerms(dto.getPaymentTerms());
        client.setCurrency(dto.getCurrency());
        client.setCompany(dto.getCompany());
        client.setNotes(dto.getNotes());

        if (dto.getStatus() != null) {
            client.setStatus(Client.Status.valueOf(dto.getStatus()));
        }
        client.setUpdatedBy(updatedBy);

        Client saved = clientStore.save(client);
        
        // Publish Kafka event
        publishClientEvent(saved, "CLIENT_UPDATED", "Client updated");
        
        return clientMapper.toDto(saved);
    }

    public void deleteClient(String id, String orgId) {
        clientStore.findByIdAndOrgId(id, orgId)
                .orElseThrow(() -> new RuntimeException("Client not found"));
        clientStore.softDelete(id, orgId);
        
        // Publish Kafka event
        publishClientEvent(id, orgId, "CLIENT_DELETED", "Client deleted", null);
    }

    public List<ClientDto> searchClients(String orgId, String search) {
        if (search == null || search.trim().isEmpty()) {
            return List.of();
        }

        String query = search.trim().toLowerCase();
        List<Client> candidates = clientStore.findAllByOrgId(orgId).stream()
                .filter(c -> matchesQuery(c, query))
                .collect(Collectors.toList());

        if (candidates.isEmpty()) {
            candidates = clientStore.findAllByOrgId(orgId);
        }

        final List<Client> finalCandidates = candidates;
        JaroWinklerSimilarity similarity = new JaroWinklerSimilarity();

        return candidates.stream()
                .map(client -> {
                    ClientDto dto = clientMapper.toDto(client);
                    double nameScore = similarity.apply(query, client.getName().toLowerCase());
                    double emailScore = client.getEmail() != null
                            ? similarity.apply(query, client.getEmail().toLowerCase()) : 0;
                    double bestScore = Math.max(nameScore, emailScore);
                    dto.setSearchScore(bestScore);
                    return new ScoredClient(dto, bestScore);
                })
                .filter(sc -> sc.score > 0.7 || finalCandidates.size() < 10)
                .sorted(Comparator.comparingDouble((ScoredClient sc) -> sc.score).reversed())
                .map(sc -> sc.client)
                .collect(Collectors.toList());
    }

    private boolean matchesQuery(Client client, String query) {
        return (client.getName() != null && client.getName().toLowerCase().contains(query))
                || (client.getEmail() != null && client.getEmail().toLowerCase().contains(query))
                || (client.getCompany() != null && client.getCompany().toLowerCase().contains(query));
    }

    private static class ScoredClient {
        ClientDto client;
        double score;
        ScoredClient(ClientDto client, double score) {
            this.client = client;
            this.score = score;
        }
    }

    private void publishClientEvent(Client client, String eventType, String description) {
        if (eventPublisher == null) return;
        try {
            String payload = String.format(
                "{\"eventType\":\"%s\",\"clientId\":\"%s\",\"orgId\":\"%s\",\"name\":\"%s\",\"email\":\"%s\",\"description\":\"%s\",\"timestamp\":%d}",
                eventType, client.getId(), client.getOrgId(), 
                client.getName() != null ? client.getName().replace("\"", "\\\"") : "",
                client.getEmail() != null ? client.getEmail().replace("\"", "\\\"") : "",
                description, System.currentTimeMillis()
            );
            com.moneyops.events.dto.DomainEvent event = new com.moneyops.events.dto.DomainEvent(
                TOPIC_CLIENT_EVENTS, client.getId(), payload
            );
            eventPublisher.publish(event);
        } catch (Exception e) {
            log.warn("Failed to publish client event", e);
        }
    }

    private void publishClientEvent(String clientId, String orgId, String eventType, String description, Client client) {
        if (eventPublisher == null) return;
        try {
            String payload = String.format(
                "{\"eventType\":\"%s\",\"clientId\":\"%s\",\"orgId\":\"%s\",\"description\":\"%s\",\"timestamp\":%d}",
                eventType, clientId, orgId, description, System.currentTimeMillis()
            );
            com.moneyops.events.dto.DomainEvent event = new com.moneyops.events.dto.DomainEvent(
                TOPIC_CLIENT_EVENTS, clientId, payload
            );
            eventPublisher.publish(event);
        } catch (Exception e) {
            log.warn("Failed to publish client event", e);
        }
    }
}
