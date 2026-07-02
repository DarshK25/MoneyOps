package com.moneyops.clients.service;

import com.moneyops.clients.dto.ClientDto;
import com.moneyops.clients.entity.Client;
import com.moneyops.clients.mapper.ClientMapper;
import com.moneyops.clients.repository.ClientRepository;
import com.moneyops.clients.validator.ClientValidator;
import com.moneyops.audit.service.AuditLogService;
import com.moneyops.jpa.entity.ClientEntity;
import com.moneyops.jpa.repository.ClientJpaRepository;
import com.moneyops.security.team.TeamActionAuthorizationService;
import com.moneyops.users.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
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

@Service
@Transactional
public class ClientService {

    private static final Logger log = LoggerFactory.getLogger(ClientService.class);

    @Autowired
    private ClientRepository clientRepository;

    @Autowired
    private ClientJpaRepository clientJpaRepository;

    @Autowired
    private ClientMapper clientMapper;

    @Autowired
    private ClientValidator clientValidator;

    @Autowired
    private TeamActionAuthorizationService teamActionAuthorizationService;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private AuditLogService auditLogService;

    public List<ClientDto> getAllClients(String orgId) {
        if (orgId == null || orgId.isBlank()) throw new com.moneyops.shared.exceptions.UnauthorizedException("Missing organization context");
        var jpaClients = clientJpaRepository.findByOrgId(orgId);
        if (!jpaClients.isEmpty()) {
            log.debug("Read clients from PostgreSQL");
            return jpaClients.stream()
                    .map(this::toClientDto)
                    .collect(Collectors.toList());
        }
        log.warn("Falling back to MongoDB for clients");
        return clientRepository.findAllByOrgIdAndDeletedAtIsNull(orgId)
                .stream()
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
        var jpaClient = clientJpaRepository.findByIdAndOrgId(id, orgId);
        if (jpaClient.isPresent()) {
            log.debug("Read client {} from PostgreSQL", id);
            return toClientDto(jpaClient.get());
        }
        log.warn("Falling back to MongoDB for client {}", id);
        Client client = clientRepository.findByIdAndOrgIdAndDeletedAtIsNull(id, orgId)
                .orElseThrow(() -> new RuntimeException("Client not found"));
        return clientMapper.toDto(client);
    }

    public ClientDto createClient(ClientDto dto, String orgId, String createdBy) {
        if (orgId == null || orgId.isBlank()) throw new com.moneyops.shared.exceptions.UnauthorizedException("Missing organization context");

        if (createdBy == null || createdBy.isBlank()) {
            throw new com.moneyops.shared.exceptions.UnauthorizedException("Missing user context");
        }

        var creator = teamActionAuthorizationService.assertUserCanCreateSensitiveAction(
                orgId,
                createdBy,
                dto.getTeamActionCode()
        );

        if (dto.getSource() == null || dto.getSource().isBlank()) {
            dto.setSource("MANUAL");
        }

        if (dto.getIdempotencyKey() != null
            && dto.getEmail() != null
            && !dto.getEmail().isBlank()
            && clientRepository.existsByEmailAndOrgIdAndDeletedAtIsNull(dto.getEmail(), orgId)) {
        }

        if (dto.getStatus() == null || dto.getStatus().trim().isEmpty()) {
            dto.setStatus("ACTIVE");
        }
        clientValidator.validate(dto);

        Client client = clientMapper.toEntity(dto);
        if (client.getEmail() != null && !client.getEmail().isBlank()
            && clientRepository.existsByEmailAndOrgIdAndDeletedAtIsNull(client.getEmail(), orgId)) {
            throw new RuntimeException("Client with this email already exists");
        }

        client.setOrgId(orgId);

        client.setCreatedBy(creator.userId());
        client.setCreatedByEmail(creator.email());
        client.setCreatedByRole(creator.role());
        client.setSource(dto.getSource());
        client.setCreatedAt(LocalDateTime.now());
        client.setUpdatedAt(LocalDateTime.now());

        Client saved = clientRepository.save(client);
        saveClientJpa(saved);
        auditLogService.logCreate("CLIENT", saved.getId(), saved);
        return clientMapper.toDto(saved);
    }

    public ClientDto updateClient(String id, ClientDto dto, String orgId, String updatedBy) {
        clientValidator.validate(dto);
        Client client = clientRepository.findByIdAndOrgIdAndDeletedAtIsNull(id, orgId)
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

        Client saved = clientRepository.save(client);
        saveClientJpa(saved);
        return clientMapper.toDto(saved);
    }

    public void deleteClient(String id, String orgId) {
        Client client = clientRepository.findByIdAndOrgIdAndDeletedAtIsNull(id, orgId)
                .orElseThrow(() -> new RuntimeException("Client not found"));

        client.setDeletedAt(LocalDateTime.now());
        clientRepository.save(client);
        clientJpaRepository.deleteById(id);
    }

    public List<ClientDto> searchClients(String orgId, String search) {
        if (search == null || search.trim().isEmpty()) {
            return List.of();
        }

        String query = search.trim().toLowerCase();

        List<Client> candidates = clientRepository.searchByOrgIdWithFilters(orgId, query);

        if (candidates.isEmpty()) {
            candidates = clientRepository.findAllByOrgIdAndDeletedAtIsNull(orgId);
        }

        final List<com.moneyops.clients.entity.Client> finalCandidates = candidates;
        JaroWinklerSimilarity similarity = new JaroWinklerSimilarity();

        return candidates.stream()
                .map(client -> {
                    ClientDto dto = clientMapper.toDto(client);
                    double nameScore = similarity.apply(query, client.getName().toLowerCase());
                    double emailScore = client.getEmail() != null ?
                            similarity.apply(query, client.getEmail().toLowerCase()) : 0;
                    double bestScore = Math.max(nameScore, emailScore);
                    dto.setSearchScore(bestScore);
                    return new ScoredClient(dto, bestScore);
                })
                .filter(sc -> sc.score > 0.7 || finalCandidates.size() < 10)
                .sorted(Comparator.comparingDouble((ScoredClient sc) -> sc.score).reversed())
                .map(sc -> sc.client)
                .collect(Collectors.toList());
    }

    private static class ScoredClient {
        ClientDto client;
        double score;
        ScoredClient(ClientDto client, double score) {
            this.client = client;
            this.score = score;
        }
    }

    private void saveClientJpa(Client client) {
        try {
            ClientEntity entity = new ClientEntity();
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
            clientJpaRepository.save(entity);
            log.debug("Client {} written to PostgreSQL", client.getId());
        } catch (Exception e) {
            log.error("Failed to write client {} to PostgreSQL: {}", client.getId(), e.getMessage());
        }
    }

    private ClientDto toClientDto(ClientEntity entity) {
        ClientDto dto = new ClientDto();
        dto.setId(entity.getId());
        dto.setOrgId(entity.getOrgId());
        dto.setName(entity.getName());
        dto.setGstin(entity.getGstin());
        dto.setEmail(entity.getEmail());
        dto.setPhoneNumber(entity.getPhoneNumber());
        dto.setCompany(entity.getCompany());
        dto.setCurrency(entity.getCurrency());
        dto.setNotes(entity.getNotes());
        dto.setStatus(entity.getStatus());
        dto.setCreatedAt(entity.getCreatedAt());
        dto.setUpdatedAt(entity.getUpdatedAt());
        return dto;
    }
}
