package com.moneyops.onboarding.service;

import com.moneyops.jpa.entity.OrganizationEntity;
import com.moneyops.jpa.entity.UserEntity;
import com.moneyops.jpa.repository.OrganizationJpaRepository;
import com.moneyops.jpa.repository.UserJpaRepository;
import com.moneyops.onboarding.dto.OnboardingRequest;
import com.moneyops.onboarding.dto.OnboardingStatusResponse;
import com.moneyops.shared.exceptions.ConflictException;
import com.moneyops.shared.exceptions.NotFoundException;
import com.moneyops.shared.exceptions.ValidationException;
import com.moneyops.users.entity.Invite;
import com.moneyops.users.repository.InviteRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class OnboardingService {

    private final UserJpaRepository userJpaRepository;
    private final OrganizationJpaRepository orgJpaRepository;
    private final InviteRepository inviteRepository;
    private final PasswordEncoder passwordEncoder;
    private final ObjectMapper objectMapper;

    // ── Status check (READ ONLY) ───────────────────────────────────

    public OnboardingStatusResponse getStatus(String userId) {
        Optional<UserEntity> userOpt = userJpaRepository.findById(userId);

        if (userOpt.isEmpty()) {
            return new OnboardingStatusResponse(false, null, null, "New user — onboarding required");
        }

        UserEntity user = userOpt.get();
        boolean hasOrg = user.getOrgId() != null;
        boolean isComplete = Boolean.TRUE.equals(user.getOnboardingComplete()) || hasOrg;

        return new OnboardingStatusResponse(
                isComplete,
                user.getId(),
                hasOrg ? user.getOrgId() : null,
                isComplete ? "Onboarding complete" : "Onboarding incomplete"
        );
    }

    // ── Repair (call during login/OAuth) ───────────────────────────

    public void repairOrganizationLink(String userId) {
        UserEntity user = userJpaRepository.findById(userId).orElse(null);
        if (user == null || user.getOrgId() != null) {
            return;
        }
        var createdOrgs = orgJpaRepository.findByCreatedByAndDeletedAtIsNull(user.getId());
        if (!createdOrgs.isEmpty()) {
            String orgId = createdOrgs.get(0).getId();
            user.setOrgId(orgId);
            user.setOnboardingComplete(true);
            userJpaRepository.save(user);
            log.info("Repaired org link for userId={} → orgId={}", userId, orgId);
        }
    }

    // ── Create business ────────────────────────────────────────────

    public OnboardingStatusResponse createBusiness(OnboardingRequest req) {
        log.info("Creating business for userId={}, legalName={}", req.getUserId(), req.getLegalName());

        OrganizationEntity org = new OrganizationEntity();
        org.setId(UUID.randomUUID().toString());
        org.setLegalName(req.getLegalName());
        org.setTradingName(req.getTradingName());
        org.setBusinessType(req.getBusinessType());
        org.setIndustry(req.getIndustry());
        if (req.getRegistrationDate() != null && !req.getRegistrationDate().isEmpty()) {
            org.setRegistrationDate(LocalDate.parse(req.getRegistrationDate()));
        }
        org.setAnnualTurnover(req.getAnnualTurnover());
        org.setPrimaryEmail(req.getPrimaryEmail());
        org.setPrimaryPhone(req.getPrimaryPhone());
        org.setWebsite(req.getWebsite());
        org.setEmployeeCount(req.getNumberOfEmployees());
        org.setRegisteredAddress(req.getRegisteredAddress());

        org.setPanNumber(req.getPanNumber());
        org.setStateOfRegistration(req.getStateOfRegistration());
        org.setGstRegistered(Boolean.TRUE.equals(req.getGstRegistered()));
        org.setGstin(req.getGstin());
        org.setGstFilingFrequency(req.getGstFilingFrequency());
        org.setTanNumber(req.getTanNumber());
        org.setCin(req.getCin());
        org.setLlpin(req.getLlpin());
        org.setMsmeNumber(req.getMsmeNumber());
        org.setIecCode(req.getIecCode());
        org.setProfessionalTaxReg(req.getProfessionalTaxReg());

        // Store non-column fields in settings JSONB
        Map<String, Object> settings = new HashMap<>();
        settings.put("primaryActivity", req.getPrimaryActivity());
        settings.put("targetMarket", req.getTargetMarket());
        settings.put("keyProducts", req.getKeyProducts());
        settings.put("currentChallenges", req.getCurrentChallenges());
        settings.put("accountingMethod", req.getAccountingMethod());
        settings.put("fyStartMonth", req.getFyStartMonth() != null ? req.getFyStartMonth() : 4);
        settings.put("preferredLanguage", req.getPreferredLanguage() != null ? req.getPreferredLanguage() : "en");

        // Team Security Code
        if (req.getTeamActionCode() != null && !req.getTeamActionCode().trim().isEmpty()) {
            settings.put("teamActionCodeHash", passwordEncoder.encode(req.getTeamActionCode()));
            log.info("Team security code set for organization during onboarding");
        }

        try {
            org.setSettings(objectMapper.writeValueAsString(settings));
        } catch (Exception e) {
            log.warn("Failed to serialize settings JSON: {}", e.getMessage());
            org.setSettings("{}");
        }

        org.setCreatedAt(LocalDateTime.now());

        UserEntity user = getOrCreateUser(req);
        org.setCreatedBy(user.getId());

        OrganizationEntity savedOrg = orgJpaRepository.save(org);
        user.setOrgId(savedOrg.getId());
        user.setOnboardingComplete(true);
        user.setRole("OWNER");
        userJpaRepository.save(user);

        return new OnboardingStatusResponse(
                true,
                user.getId(),
                savedOrg.getId(),
                "Business created successfully"
        );
    }

    // ── Join business ──────────────────────────────────────────────

    public Map<String, Object> verifyInvite(String code) {
        Invite invite = inviteRepository.findByTokenAndDeletedAtIsNull(code)
                .orElseThrow(() -> new NotFoundException("Invalid or expired invite code"));

        if (invite.getStatus() != Invite.InviteStatus.PENDING) {
            throw new ConflictException("This invite code has already been used");
        }

        if (invite.getExpiresAt().isBefore(LocalDateTime.now())) {
            throw new ValidationException("This invite code has expired");
        }

        OrganizationEntity org = orgJpaRepository.findById(invite.getOrgId())
                .orElseThrow(() -> new NotFoundException("Organisation no longer exists"));

        return Map.of(
                "valid", true,
                "businessName", org.getLegalName() != null ? org.getLegalName() : org.getName(),
                "role", invite.getRole()
        );
    }

    public OnboardingStatusResponse joinBusiness(OnboardingRequest req) {
        log.info("User userId={} joining via code={}", req.getUserId(), req.getInviteCode());

        Invite invite = inviteRepository.findByTokenAndDeletedAtIsNull(req.getInviteCode())
                .orElseThrow(() -> new NotFoundException("Invalid invite code"));

        if (invite.getStatus() != Invite.InviteStatus.PENDING) {
            throw new ConflictException("Invite code already used");
        }

        OrganizationEntity org = orgJpaRepository.findById(invite.getOrgId())
                .orElseThrow(() -> new NotFoundException("Organisation not found"));

        UserEntity user = getOrCreateUser(req);
        user.setOrgId(org.getId());
        user.setOnboardingComplete(true);
        user.setRole(invite.getRole().name());
        userJpaRepository.save(user);

        invite.setStatus(Invite.InviteStatus.ACCEPTED);
        invite.setUpdatedAt(LocalDateTime.now());
        inviteRepository.save(invite);

        return new OnboardingStatusResponse(
                true,
                user.getId(),
                org.getId(),
                "Joined organisation successfully"
        );
    }

    private UserEntity getOrCreateUser(OnboardingRequest req) {
        if (req.getEmail() != null && !req.getEmail().isBlank()) {
            var byEmail = userJpaRepository.findByEmailAndDeletedAtIsNull(req.getEmail());
            if (byEmail.isPresent()) {
                return byEmail.get();
            }
        }
        return userJpaRepository.findById(req.getUserId()).orElseGet(() -> {
            UserEntity newUser = new UserEntity();
            newUser.setId(UUID.randomUUID().toString());
            newUser.setEmail(req.getEmail());
            newUser.setName(req.getName());
            newUser.setRole("STAFF");
            newUser.setStatus("ACTIVE");
            newUser.setCreatedAt(LocalDateTime.now());
            return userJpaRepository.save(newUser);
        });
    }
}
