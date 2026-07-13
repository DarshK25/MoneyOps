package com.moneyops.organizations.service;

import com.moneyops.jpa.entity.OrganizationEntity;
import com.moneyops.jpa.entity.UserEntity;
import com.moneyops.jpa.persistence.OrganizationDocumentStore;
import com.moneyops.jpa.repository.UserJpaRepository;
import com.moneyops.organizations.dto.BusinessOrganizationDto;
import com.moneyops.organizations.dto.RegulatoryProfileDto;
import com.moneyops.organizations.entity.BusinessOrganization;
import com.moneyops.organizations.entity.RegulatoryProfile;
import com.moneyops.organizations.mapper.OrganizationMapper;
import com.moneyops.organizations.repository.BusinessOrganizationRepository;
import com.moneyops.organizations.repository.RegulatoryProfileRepository;
import com.moneyops.organizations.validator.OrganizationValidator;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional
public class OrganizationService {

    private final OrganizationDocumentStore organizationStore;
    private final UserJpaRepository userJpaRepository;
    private final RegulatoryProfileRepository regulatoryRepository;
    private final BusinessOrganizationRepository legacyOrgRepository;
    private final OrganizationMapper mapper;
    private final OrganizationValidator validator;

    private void verifyAccess(String orgId, String userId) {
        if (userJpaRepository.findByIdAndOrgIdAndDeletedAtIsNull(userId, orgId).isPresent()) {
            return;
        }
        if (organizationStore.findByIdAndCreatedBy(orgId, userId).isPresent()) {
            return;
        }
        throw new NotFoundException("User not found or access denied");
    }

    public List<BusinessOrganizationDto> getAllOrganizations(String userId) {
        return organizationStore.findAllByCreatedBy(userId).stream()
                .map(organizationStore::toDto)
                .collect(Collectors.toList());
    }

    public BusinessOrganizationDto getOrganizationById(String id, String userId) {
        verifyAccess(id, userId);
        OrganizationEntity org = organizationStore.findByIdAndCreatedBy(id, userId)
                .orElseThrow(() -> new RuntimeException("Organization not found"));
        return organizationStore.toDto(org);
    }

    public BusinessOrganizationDto getMyOrganization(String userId) {
        UserEntity user = userJpaRepository.findByIdAndDeletedAtIsNull(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));

        String orgId = user.getOrgId();
        if (orgId == null) {
            List<OrganizationEntity> createdOrgs = organizationStore.findAllByCreatedBy(userId);
            if (createdOrgs.isEmpty()) {
                throw new NotFoundException("No organization found for user");
            }
            return organizationStore.toDto(createdOrgs.get(0));
        }

        OrganizationEntity org = organizationStore.findById(orgId)
                .orElseThrow(() -> new RuntimeException("Organization not found"));
        return organizationStore.toDto(org);
    }

    public BusinessOrganizationDto createOrganization(BusinessOrganizationDto dto, String userId) {
        validator.validate(dto);
        OrganizationEntity saved = organizationStore.saveFromDto(dto, userId);

        userJpaRepository.findByIdAndDeletedAtIsNull(userId).ifPresent(u -> {
            if (u.getOrgId() == null) {
                u.setOrgId(saved.getId());
                u.setRole("OWNER");
                u.setOnboardingComplete(true);
                userJpaRepository.save(u);
            }
        });

        return organizationStore.toDto(saved);
    }

    public BusinessOrganizationDto updateOrganization(String id, BusinessOrganizationDto dto, String userId) {
        verifyAccess(id, userId);
        OrganizationEntity existing = organizationStore.findByIdAndCreatedBy(id, userId)
                .orElseThrow(() -> new RuntimeException("Organization not found"));
        dto.setId(existing.getId());
        validator.validate(dto);
        OrganizationEntity saved = organizationStore.saveFromDto(dto, userId);
        return organizationStore.toDto(saved);
    }

    public void deleteOrganization(String id, String userId) {
        organizationStore.findByIdAndCreatedBy(id, userId)
                .orElseThrow(() -> new RuntimeException("Organization not found"));
        organizationStore.softDelete(id);
    }

    public BusinessOrganizationDto getVerificationTier(String orgId, String userId) {
        return getOrganizationById(orgId, userId);
    }

    public BusinessOrganizationDto updateVerificationTier(String orgId, String userId, String tier) {
        verifyAccess(orgId, userId);
        OrganizationEntity org = organizationStore.findByIdAndCreatedBy(orgId, userId)
                .orElseThrow(() -> new RuntimeException("Organization not found"));
        try {
            BusinessOrganization.VerificationTier.valueOf(tier.toUpperCase());
            org.setVerificationTier(tier.toUpperCase());
        } catch (IllegalArgumentException e) {
            throw new BusinessRuleException("Invalid verification tier: " + tier + ". Must be UNVERIFIED, BASIC, or GST_VERIFIED.");
        }
        return organizationStore.toDto(organizationStore.saveEntity(org));
    }

    public RegulatoryProfileDto getRegulatoryProfile(String orgId, String userId) {
        verifyAccess(orgId, userId);
        RegulatoryProfile profile = regulatoryRepository.findByOrgIdAndDeletedAtIsNull(orgId)
                .orElseGet(() -> {
                    OrganizationEntity org = organizationStore.findById(orgId).orElseThrow();
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
        OrganizationEntity org = organizationStore.findById(orgId)
                .orElseThrow(() -> new RuntimeException("Organization not found"));
        validator.validateRegulatory(dto);

        BusinessOrganization legacy = legacyOrgRepository.findById(orgId).orElse(new BusinessOrganization());
        legacy.setId(orgId);
        legacy.setPanNumber(org.getPanNumber());
        legacy.setGstin(org.getGstin());

        RegulatoryProfile profile = mapper.toRegulatoryEntity(dto, legacy);
        RegulatoryProfile saved = regulatoryRepository.save(profile);

        org.setPanNumber(dto.getPanNumber());
        org.setGstRegistered(dto.getGstRegistered());
        org.setGstin(dto.getGstNumber());
        organizationStore.saveEntity(org);

        return mapper.toRegulatoryDto(saved);
    }

    public RegulatoryProfileDto updateRegulatoryProfile(String orgId, RegulatoryProfileDto dto, String userId) {
        verifyAccess(orgId, userId);
        OrganizationEntity org = organizationStore.findById(orgId)
                .orElseThrow(() -> new RuntimeException("Organization not found"));
        validator.validateRegulatory(dto);

        BusinessOrganization legacy = legacyOrgRepository.findById(orgId).orElse(new BusinessOrganization());
        legacy.setId(orgId);

        RegulatoryProfile existing = regulatoryRepository.findByOrgIdAndDeletedAtIsNull(orgId)
                .orElse(new RegulatoryProfile());
        RegulatoryProfile updated = mapper.toRegulatoryEntity(dto, legacy);
        if (existing.getId() != null) {
            updated.setId(existing.getId());
        }
        RegulatoryProfile saved = regulatoryRepository.save(updated);

        org.setPanNumber(dto.getPanNumber());
        org.setGstRegistered(dto.getGstRegistered());
        org.setGstin(dto.getGstNumber());
        organizationStore.saveEntity(org);

        return mapper.toRegulatoryDto(saved);
    }
}
