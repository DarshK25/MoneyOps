package com.moneyops.jpa.persistence;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.moneyops.jpa.entity.OrganizationEntity;
import com.moneyops.jpa.repository.OrganizationJpaRepository;
import com.moneyops.jpa.util.DocumentJsonMapper;
import com.moneyops.organizations.dto.BusinessOrganizationDto;
import com.moneyops.organizations.entity.BusinessOrganization;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

@Component
@RequiredArgsConstructor
@Slf4j
public class OrganizationDocumentStore {

    private final OrganizationJpaRepository organizationJpaRepository;
    private final DocumentJsonMapper documentJsonMapper;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public OrganizationEntity saveFromDto(BusinessOrganizationDto dto, String userId) {
        OrganizationEntity entity = dto.getId() != null
                ? organizationJpaRepository.findById(dto.getId()).orElse(new OrganizationEntity())
                : new OrganizationEntity();

        if (entity.getId() == null || entity.getId().isBlank()) {
            entity.setId(UUID.randomUUID().toString());
        }
        applyDto(entity, dto, userId);
        if (entity.getCreatedAt() == null) {
            entity.setCreatedAt(LocalDateTime.now());
        }
        entity.setUpdatedAt(LocalDateTime.now());
        return organizationJpaRepository.save(entity);
    }

    public OrganizationEntity saveEntity(OrganizationEntity entity) {
        if (entity.getCreatedAt() == null) {
            entity.setCreatedAt(LocalDateTime.now());
        }
        entity.setUpdatedAt(LocalDateTime.now());
        return organizationJpaRepository.save(entity);
    }

    public Optional<OrganizationEntity> findByIdAndCreatedBy(String id, String userId) {
        return organizationJpaRepository.findByIdAndCreatedByAndDeletedAtIsNull(id, userId);
    }

    public Optional<OrganizationEntity> findById(String id) {
        return organizationJpaRepository.findById(id)
                .filter(o -> o.getDeletedAt() == null);
    }

    public List<OrganizationEntity> findAllByCreatedBy(String userId) {
        return organizationJpaRepository.findByCreatedByAndDeletedAtIsNull(userId);
    }

    public void softDelete(String id) {
        organizationJpaRepository.findById(id).ifPresent(entity -> {
            entity.setDeletedAt(LocalDateTime.now());
            organizationJpaRepository.save(entity);
        });
    }

    public String getTeamActionCodeHash(OrganizationEntity entity) {
        if (entity.getTeamActionCodeHash() != null && !entity.getTeamActionCodeHash().isBlank()) {
            return entity.getTeamActionCodeHash();
        }
        return readSettingsString(entity, "teamActionCodeHash");
    }

    public void setTeamActionCodeHash(OrganizationEntity entity, String hash) {
        entity.setTeamActionCodeHash(hash);
        Map<String, Object> settings = readSettings(entity);
        settings.put("teamActionCodeHash", hash);
        entity.setSettings(documentJsonMapper.toJson(settings));
    }

    public BusinessOrganizationDto toDto(OrganizationEntity entity) {
        if (entity == null) {
            return null;
        }
        BusinessOrganizationDto dto = new BusinessOrganizationDto();
        dto.setId(entity.getId());
        dto.setLegalName(entity.getLegalName() != null ? entity.getLegalName() : entity.getName());
        dto.setTradingName(entity.getTradingName());
        dto.setBusinessType(entity.getBusinessType());
        dto.setIndustry(entity.getIndustry());
        dto.setRegistrationDate(entity.getRegistrationDate());
        dto.setAnnualTurnoverRange(entity.getAnnualTurnover());
        dto.setPrimaryEmail(entity.getPrimaryEmail());
        dto.setPrimaryPhone(entity.getPrimaryPhone());
        dto.setWebsite(entity.getWebsite());
        dto.setEmployeeCount(entity.getEmployeeCount());
        dto.setRegisteredAddress(entity.getRegisteredAddress());
        dto.setPincode(entity.getPincode());
        dto.setPanNumber(entity.getPanNumber());
        dto.setStateOfRegistration(entity.getStateOfRegistration());
        dto.setGstRegistered(entity.getGstRegistered());
        dto.setGstin(entity.getGstin());
        dto.setGstFilingFrequency(entity.getGstFilingFrequency());
        dto.setTanNumber(entity.getTanNumber());
        dto.setCin(entity.getCin());
        dto.setLlpin(entity.getLlpin());
        dto.setMsmeNumber(entity.getMsmeNumber());
        dto.setIecCode(entity.getIecCode());
        dto.setProfessionalTaxReg(entity.getProfessionalTaxReg());
        dto.setVerificationTier(entity.getVerificationTier() != null ? entity.getVerificationTier() : "UNVERIFIED");
        dto.setTeamSecurityCodeConfigured(getTeamActionCodeHash(entity) != null);

        Map<String, Object> settings = readSettings(entity);
        dto.setPrimaryActivity((String) settings.get("primaryActivity"));
        dto.setTargetMarket((String) settings.get("targetMarket"));
        dto.setAccountingMethod((String) settings.get("accountingMethod"));
        dto.setPreferredLanguage((String) settings.getOrDefault("preferredLanguage", "en").toString());
        if (settings.get("fyStartMonth") != null) {
            dto.setFinancialYearStartMonth(settings.get("fyStartMonth").toString());
        }
        if (settings.get("keyProducts") instanceof List<?> list) {
            dto.setKeyProducts(list.stream().map(Object::toString).collect(Collectors.toList()));
        }
        if (settings.get("currentChallenges") instanceof List<?> list) {
            dto.setCurrentChallenges(list.stream().map(Object::toString).collect(Collectors.toList()));
        }
        return dto;
    }

    public OrganizationEntity fromLegacyMongo(BusinessOrganization org) {
        OrganizationEntity entity = new OrganizationEntity();
        entity.setId(org.getId());
        entity.setName(org.getLegalName() != null ? org.getLegalName() : org.getTradingName());
        entity.setLegalName(org.getLegalName());
        entity.setTradingName(org.getTradingName());
        entity.setBusinessType(org.getBusinessType());
        entity.setIndustry(org.getIndustry());
        entity.setPrimaryEmail(org.getPrimaryEmail());
        entity.setPrimaryPhone(org.getPrimaryPhone());
        entity.setWebsite(org.getWebsite());
        entity.setRegisteredAddress(org.getRegisteredAddress());
        entity.setRegistrationDate(org.getRegistrationDate());
        entity.setEmployeeCount(org.getEmployeeCount());
        entity.setAnnualTurnover(org.getAnnualTurnover());
        entity.setPincode(org.getPincode());
        entity.setGstRegistered(org.getGstRegistered());
        entity.setGstin(org.getGstin());
        entity.setGstFilingFrequency(org.getGstFilingFrequency());
        entity.setPanNumber(org.getPanNumber());
        entity.setTanNumber(org.getTanNumber());
        entity.setCin(org.getCin());
        entity.setLlpin(org.getLlpin());
        entity.setMsmeNumber(org.getMsmeNumber());
        entity.setIecCode(org.getIecCode());
        entity.setProfessionalTaxReg(org.getProfessionalTaxReg());
        entity.setStateOfRegistration(org.getStateOfRegistration());
        entity.setCreatedBy(org.getCreatedBy());
        entity.setCreatedAt(org.getCreatedAt());
        entity.setUpdatedAt(org.getUpdatedAt());
        entity.setDeletedAt(org.getDeletedAt());
        if (org.getVerificationTier() != null) {
            entity.setVerificationTier(org.getVerificationTier().name());
        }
        if (org.getTeamActionCodeHash() != null) {
            setTeamActionCodeHash(entity, org.getTeamActionCodeHash());
        }
        return entity;
    }

    private void applyDto(OrganizationEntity entity, BusinessOrganizationDto dto, String userId) {
        entity.setLegalName(dto.getLegalName());
        entity.setTradingName(dto.getTradingName());
        entity.setName(dto.getLegalName() != null ? dto.getLegalName() : dto.getTradingName());
        entity.setBusinessType(dto.getBusinessType());
        entity.setIndustry(dto.getIndustry());
        entity.setRegistrationDate(dto.getRegistrationDate());
        entity.setAnnualTurnover(dto.getAnnualTurnoverRange());
        entity.setPrimaryEmail(dto.getPrimaryEmail());
        entity.setPrimaryPhone(dto.getPrimaryPhone());
        entity.setWebsite(dto.getWebsite());
        entity.setEmployeeCount(dto.getEmployeeCount());
        entity.setRegisteredAddress(dto.getRegisteredAddress());
        entity.setPincode(dto.getPincode());
        entity.setPanNumber(dto.getPanNumber());
        entity.setStateOfRegistration(dto.getStateOfRegistration());
        entity.setGstRegistered(dto.getGstRegistered());
        entity.setGstin(dto.getGstin());
        entity.setGstFilingFrequency(dto.getGstFilingFrequency());
        entity.setTanNumber(dto.getTanNumber());
        entity.setCin(dto.getCin());
        entity.setLlpin(dto.getLlpin());
        entity.setMsmeNumber(dto.getMsmeNumber());
        entity.setIecCode(dto.getIecCode());
        entity.setProfessionalTaxReg(dto.getProfessionalTaxReg());
        if (dto.getVerificationTier() != null) {
            entity.setVerificationTier(dto.getVerificationTier());
        }
        if (entity.getCreatedBy() == null) {
            entity.setCreatedBy(userId);
        }
        entity.setUpdatedBy(userId);

        Map<String, Object> settings = readSettings(entity);
        settings.put("primaryActivity", dto.getPrimaryActivity());
        settings.put("targetMarket", dto.getTargetMarket());
        settings.put("accountingMethod", dto.getAccountingMethod());
        settings.put("preferredLanguage", dto.getPreferredLanguage());
        settings.put("keyProducts", dto.getKeyProducts());
        settings.put("currentChallenges", dto.getCurrentChallenges());
        if (dto.getFinancialYearStartMonth() != null) {
            settings.put("fyStartMonth", dto.getFinancialYearStartMonth());
        }
        entity.setSettings(documentJsonMapper.toJson(settings));
    }

    private Map<String, Object> readSettings(OrganizationEntity entity) {
        if (entity.getSettings() == null || entity.getSettings().isBlank()) {
            return new HashMap<>();
        }
        try {
            return objectMapper.readValue(entity.getSettings(), new TypeReference<>() {});
        } catch (Exception e) {
            log.warn("Failed to parse org settings for {}: {}", entity.getId(), e.getMessage());
            return new HashMap<>();
        }
    }

    private String readSettingsString(OrganizationEntity entity, String key) {
        Object val = readSettings(entity).get(key);
        return val != null ? val.toString() : null;
    }
}
