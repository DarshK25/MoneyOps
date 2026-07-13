package com.moneyops.security.team;

import com.moneyops.jpa.entity.UserEntity;
import com.moneyops.jpa.repository.UserJpaRepository;
import com.moneyops.shared.exceptions.ForbiddenException;
import com.moneyops.shared.exceptions.UnauthorizedException;
import com.moneyops.shared.exceptions.ValidationException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class TeamActionAuthorizationService {

    private final UserJpaRepository userJpaRepository;
    private final TeamSecurityCodeService teamSecurityCodeService;

    public CreatorMetadata assertUserCanCreateSensitiveAction(String orgId, String userId, String rawTeamCode) {
        if (orgId == null || orgId.isBlank()) {
            throw new UnauthorizedException("Organization context missing.");
        }
        if (userId == null || userId.isBlank()) {
            throw new UnauthorizedException("User context missing.");
        }

        UserEntity user = userJpaRepository.findByIdAndOrgIdAndDeletedAtIsNull(userId, orgId)
                .orElseThrow(() -> new UnauthorizedException("User not part of this organization."));

        if (!"ACTIVE".equalsIgnoreCase(user.getStatus())) {
            throw new UnauthorizedException("Only active team members can perform this action.");
        }

        String role = user.getRole() != null ? user.getRole().toUpperCase() : "";
        if (!("OWNER".equals(role) || "STAFF".equals(role))) {
            throw new ForbiddenException("You are not authorized to perform this action.");
        }

        teamSecurityCodeService.assertTeamActionCodeValid(orgId, rawTeamCode);

        return new CreatorMetadata(user.getId(), user.getEmail(), user.getRole());
    }

    public void assertOwnerCanSetTeamActionCode(String orgId, String userId) {
        if (orgId == null || orgId.isBlank() || userId == null || userId.isBlank()) {
            throw new UnauthorizedException("Organization or user context missing.");
        }

        UserEntity user = userJpaRepository.findByIdAndOrgIdAndDeletedAtIsNull(userId, orgId)
                .orElseThrow(() -> new UnauthorizedException("User not part of this organization."));

        if (!"ACTIVE".equalsIgnoreCase(user.getStatus())) {
            throw new UnauthorizedException("Only active owners can update the security code.");
        }

        if (!"OWNER".equalsIgnoreCase(user.getRole())) {
            throw new ForbiddenException("Only the owner can update the team security code.");
        }
    }

    public record CreatorMetadata(String userId, String email, String role) {
        public CreatorMetadata {
            if (userId == null || userId.isBlank()) {
                throw new ValidationException("Creator userId missing.");
            }
        }
    }
}
