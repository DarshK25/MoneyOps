package com.moneyops.organizations.service;

import com.moneyops.jpa.entity.OrganizationEntity;
import com.moneyops.jpa.repository.OrganizationJpaRepository;
import com.moneyops.organizations.dto.BusinessOrganizationDto;
import com.moneyops.organizations.dto.RegulatoryProfileDto;
import com.moneyops.organizations.entity.BusinessOrganization;
import com.moneyops.organizations.entity.RegulatoryProfile;
import com.moneyops.organizations.mapper.OrganizationMapper;
import com.moneyops.organizations.repository.BusinessOrganizationRepository;
import com.moneyops.organizations.repository.RegulatoryProfileRepository;
import com.moneyops.organizations.validator.OrganizationValidator;
import com.moneyops.users.entity.User;
import com.moneyops.users.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional
public class OrganizationService {

    private static final Logger log = LoggerFactory.getLogger(OrganizationService.class);

    private final BusinessOrganizationRepository orgRepository;
    private final OrganizationJpaRepository orgJpaRepository;
    private final RegulatoryProfileRepository regulatoryRepository;
    private final OrganizationMapper mapper;
    private final OrganizationValidator validator;
    private final UserRepository userRepository;

    private void verifyAccess(String orgId, String userId) {
        User user = userRepository.findByIdAndOrgIdAndDeletedAtIsNull(userId, orgId)
                .orElseThrow(() -> new RuntimeException("User not found or access denied"));

        if (orgId.equals(user.getOrgId())) {
            return;
        }

        BusinessOrganization org = orgRepository.findByIdAndCreatedByAndDeletedAtIsNull(orgId, userId)
                .orElseThrow(() -> new RuntimeException("Organization not found or access denied"));
    }

    public List<BusinessOrganizationDto> getAllOrganizations(String userId) {
        var jpaOrgs = orgJpaRepository.findByCreatedBy(userId);
        if (!jpaOrgs.isEmpty()) {
            log.debug("Read organizations from PostgreSQL");
            return jpaOrgs.stream()
                    .map(this::toBusinessOrganizationDto)
                    .collect(Collectors.toList());
        }
        log.warn("Falling back to MongoDB for organizations");
        return orgRepository.findAllByCreatedByAndDeletedAtIsNull(userId).stream()
                .map(mapper::toDto)
                .collect(Collectors.toList());
    }

    public BusinessOrganizationDto getOrganizationById(String id, String userId) {
        verifyAccess(id, userId);
        var jpaOrg = orgJpaRepository.findByIdAndCreatedBy(id, userId);
        if (jpaOrg.isPresent()) {
            log.debug("Read organization {} from PostgreSQL", id);
            return toBusinessOrganizationDto(jpaOrg.get());
        }
        log.warn("Falling back to MongoDB for organization {}", id);
        BusinessOrganization org = orgRepository.findByIdAndCreatedByAndDeletedAtIsNull(id, userId)
                .orElseThrow(() -> new RuntimeException("Organization not found"));
        return mapper.toDto(org);
    }

    public BusinessOrganizationDto getMyOrganization(String userId) {
        User user = userRepository.findByIdAndDeletedAtIsNull(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));

        String orgId = user.getOrgId();
        if (orgId == null) {
            List<BusinessOrganization> createdOrgs = orgRepository.findAllByCreatedByAndDeletedAtIsNull(userId);
            if (createdOrgs.isEmpty()) throw new RuntimeException("No organization found for user");
            return mapper.toDto(createdOrgs.get(0));
        }

        var jpaOrg = orgJpaRepository.findByIdAndCreatedBy(orgId, userId);
        if (jpaOrg.isPresent()) {
            log.debug("Read my organization from PostgreSQL");
            return toBusinessOrganizationDto(jpaOrg.get());
        }

        BusinessOrganization org = orgRepository.findByIdAndCreatedByAndDeletedAtIsNull(orgId, userId)
                .orElseThrow(() -> new RuntimeException("Organization not found"));
        return mapper.toDto(org);
    }

    public BusinessOrganizationDto createOrganization(BusinessOrganizationDto dto, String userId) {
        validator.validate(dto);

        BusinessOrganization org = mapper.toEntity(dto);
        org.setCreatedBy(userId);

        BusinessOrganization saved = orgRepository.save(org);
        saveOrganizationJpa(saved);

        userRepository.findByIdAndDeletedAtIsNull(userId).ifPresent(u -> {
            if (u.getOrgId() == null) {
                u.setOrgId(saved.getId());
                u.setRole(User.Role.OWNER);
                userRepository.save(u);
            }
        });

        return mapper.toDto(saved);
    }

    public BusinessOrganizationDto updateOrganization(String id, BusinessOrganizationDto dto, String userId) {
        verifyAccess(id, userId);
        BusinessOrganization existing = orgRepository.findByIdAndCreatedByAndDeletedAtIsNull(id, userId)
                .orElseThrow(() -> new RuntimeException("Organization not found"));

        validator.validate(dto);

        BusinessOrganization updated = mergeOrganization(existing, dto);
        BusinessOrganization saved = orgRepository.save(updated);
        saveOrganizationJpa(saved);
        return mapper.toDto(saved);
    }

    private BusinessOrganization mergeOrganization(BusinessOrganization existing, BusinessOrganizationDto dto) {
        existing.setLegalName(dto.getLegalName());
        existing.setTradingName(dto.getTradingName());
        existing.setBusinessType(dto.getBusinessType());
        existing.setIndustry(dto.getIndustry());
        existing.setRegistrationDate(dto.getRegistrationDate());
        existing.setAnnualTurnover(dto.getAnnualTurnoverRange());
        existing.setPrimaryEmail(dto.getPrimaryEmail());
        existing.setPrimaryPhone(dto.getPrimaryPhone());
        existing.setWebsite(dto.getWebsite());
        existing.setEmployeeCount(dto.getEmployeeCount());
        existing.setRegisteredAddress(dto.getRegisteredAddress());
        existing.setPincode(dto.getPincode());
        existing.setPreferredLanguage(dto.getPreferredLanguage());
        existing.setPrimaryActivity(dto.getPrimaryActivity());
        existing.setTargetMarket(dto.getTargetMarket());
        existing.setAccountingMethod(dto.getAccountingMethod());
        existing.setKeyProducts(dto.getKeyProducts());
        existing.setCurrentChallenges(dto.getCurrentChallenges());
        existing.setPanNumber(dto.getPanNumber());
        existing.setStateOfRegistration(dto.getStateOfRegistration());
        existing.setGstRegistered(dto.getGstRegistered());
        existing.setGstin(dto.getGstin());
        existing.setGstFilingFrequency(dto.getGstFilingFrequency());
        existing.setTanNumber(dto.getTanNumber());
        existing.setCin(dto.getCin());
        existing.setLlpin(dto.getLlpin());
        existing.setMsmeNumber(dto.getMsmeNumber());
        existing.setIecCode(dto.getIecCode());
        existing.setProfessionalTaxReg(dto.getProfessionalTaxReg());

        if (dto.getFinancialYearStartMonth() != null && !dto.getFinancialYearStartMonth().isBlank()) {
            existing.setFyStartMonth(Integer.valueOf(dto.getFinancialYearStartMonth()));
        } else {
            existing.setFyStartMonth(null);
        }

        return existing;
    }

    public void deleteOrganization(String id, String userId) {
        BusinessOrganization org = orgRepository.findByIdAndCreatedByAndDeletedAtIsNull(id, userId)
                .orElseThrow(() -> new RuntimeException("Organization not found"));

        org.setDeletedAt(LocalDateTime.now());
        orgRepository.save(org);
        orgJpaRepository.deleteById(id);
    }

    public BusinessOrganizationDto getVerificationTier(String orgId, String userId) {
        BusinessOrganization org = orgRepository.findByIdAndCreatedByAndDeletedAtIsNull(orgId, userId)
                .orElseThrow(() -> new RuntimeException("Organization not found"));
        return mapper.toDto(org);
    }

    public BusinessOrganizationDto updateVerificationTier(String orgId, String userId, String tier) {
        BusinessOrganization org = orgRepository.findByIdAndCreatedByAndDeletedAtIsNull(orgId, userId)
                .orElseThrow(() -> new RuntimeException("Organization not found"));

        try {
            BusinessOrganization.VerificationTier newTier = BusinessOrganization.VerificationTier.valueOf(tier.toUpperCase());
            org.setVerificationTier(newTier);
        } catch (IllegalArgumentException e) {
            throw new RuntimeException("Invalid verification tier: " + tier + ". Must be UNVERIFIED, BASIC, or GST_VERIFIED.");
        }

        BusinessOrganization saved = orgRepository.save(org);
        saveOrganizationJpa(saved);
        return mapper.toDto(saved);
    }

    public RegulatoryProfileDto getRegulatoryProfile(String orgId, String userId) {
        verifyAccess(orgId, userId);
        RegulatoryProfile profile = regulatoryRepository.findByOrgIdAndDeletedAtIsNull(orgId)
                .orElseGet(() -> {
                    BusinessOrganization org = orgRepository.findByIdAndCreatedByAndDeletedAtIsNull(orgId, userId).orElseThrow();
                    RegulatoryProfile p = new RegulatoryProfile();
                    p.setOrgId(orgId);
                    p.setPanNumber(org.getPanNumber());
                    p.setGstNumber(org.getGstin());
                    return p;
                });
        return mapper.toRegulatoryDto(profile);
    }

    public RegulatoryProfileDto createRegulatoryProfile(String orgId, RegulatoryProfileDto dto, String userId) {
        verifyAccess(orgId, userId);
        BusinessOrganization org = orgRepository.findByIdAndCreatedByAndDeletedAtIsNull(orgId, userId)
                .orElseThrow(() -> new RuntimeException("Organization not found"));

        validator.validateRegulatory(dto);

        RegulatoryProfile profile = mapper.toRegulatoryEntity(dto, org);
        RegulatoryProfile saved = regulatoryRepository.save(profile);

        org.setPanNumber(dto.getPanNumber());
        org.setGstRegistered(dto.getGstRegistered());
        org.setGstin(dto.getGstNumber());
        orgRepository.save(org);

        return mapper.toRegulatoryDto(saved);
    }

    public RegulatoryProfileDto updateRegulatoryProfile(String orgId, RegulatoryProfileDto dto, String userId) {
        verifyAccess(orgId, userId);
        BusinessOrganization org = orgRepository.findByIdAndCreatedByAndDeletedAtIsNull(orgId, userId)
                .orElseThrow(() -> new RuntimeException("Organization not found"));

        validator.validateRegulatory(dto);

        RegulatoryProfile existing = regulatoryRepository.findByOrgIdAndDeletedAtIsNull(orgId)
                .orElse(new RegulatoryProfile());

        RegulatoryProfile updated = mapper.toRegulatoryEntity(dto, org);
        if (existing.getId() != null) {
            updated.setId(existing.getId());
        }

        RegulatoryProfile saved = regulatoryRepository.save(updated);

        org.setPanNumber(dto.getPanNumber());
        org.setGstRegistered(dto.getGstRegistered());
        org.setGstin(dto.getGstNumber());
        orgRepository.save(org);

        return mapper.toRegulatoryDto(saved);
    }

    private void saveOrganizationJpa(BusinessOrganization org) {
        try {
            OrganizationEntity entity = new OrganizationEntity();
            entity.setId(org.getId());
            entity.setName(org.getLegalName() != null ? org.getLegalName() : org.getTradingName());
            entity.setBusinessType(org.getBusinessType());
            entity.setGstin(org.getGstin());
            entity.setPan(org.getPanNumber());
            entity.setCreatedBy(org.getCreatedBy());
            entity.setCreatedAt(org.getCreatedAt());
            entity.setUpdatedAt(org.getUpdatedAt());
            orgJpaRepository.save(entity);
            log.debug("Organization {} written to PostgreSQL", org.getId());
        } catch (Exception e) {
            log.error("Failed to write organization {} to PostgreSQL: {}", org.getId(), e.getMessage());
        }
    }

    private BusinessOrganizationDto toBusinessOrganizationDto(OrganizationEntity entity) {
        BusinessOrganizationDto dto = new BusinessOrganizationDto();
        dto.setId(entity.getId());
        dto.setLegalName(entity.getName());
        dto.setBusinessType(entity.getBusinessType());
        dto.setGstin(entity.getGstin());
        dto.setPanNumber(entity.getPan());
        return dto;
    }
}
