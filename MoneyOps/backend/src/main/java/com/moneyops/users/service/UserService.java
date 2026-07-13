package com.moneyops.users.service;

import com.moneyops.audit.service.AuditLogService;
import com.moneyops.email.EmailService;
import com.moneyops.jpa.entity.OrganizationEntity;
import com.moneyops.jpa.entity.UserEntity;
import com.moneyops.jpa.repository.OrganizationJpaRepository;
import com.moneyops.jpa.repository.UserJpaRepository;
import com.moneyops.users.dto.UserDto;
import com.moneyops.users.dto.CreateInviteRequest;
import com.moneyops.users.dto.AcceptInviteRequest;
import com.moneyops.users.entity.Invite;
import com.moneyops.users.repository.InviteRepository;
import com.moneyops.users.validator.UserValidator;
import com.moneyops.users.validator.InviteValidator;
import com.moneyops.shared.exceptions.ConflictException;
import com.moneyops.shared.exceptions.NotFoundException;
import com.moneyops.shared.exceptions.BusinessRuleException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@Transactional
public class UserService {

    private static final Logger log = LoggerFactory.getLogger(UserService.class);

    @Autowired
    private UserJpaRepository userJpaRepository;

    @Autowired
    private InviteRepository inviteRepository;

    @Autowired
    private UserValidator userValidator;

    @Autowired
    private InviteValidator inviteValidator;

    @Autowired
    private AuditLogService auditLogService;

    @Autowired
    private EmailService emailService;

    @Autowired
    private OrganizationJpaRepository orgJpaRepository;

    public List<UserDto> getAllUsers(String orgId) {
        return userJpaRepository.findByOrgIdAndDeletedAtIsNull(orgId)
                .stream()
                .map(this::toUserDto)
                .collect(Collectors.toList());
    }

    public UserDto getUserById(String id, String orgId) {
        UserEntity user = userJpaRepository.findByIdAndOrgId(id, orgId)
                .orElseThrow(() -> new NotFoundException("User not found"));
        return toUserDto(user);
    }

    public UserEntity findUserById(String id) {
        return userJpaRepository.findById(id).orElse(null);
    }

    public UserDto createUser(UserDto dto, String orgId, String createdBy) {
        userValidator.validate(dto);
        if (userJpaRepository.findByEmailAndOrgId(dto.getEmail(), orgId).isPresent()) {
            throw new ConflictException("User with this email already exists");
        }

        UserEntity user = new UserEntity();
        user.setName(dto.getName());
        user.setEmail(dto.getEmail());
        user.setPhone(dto.getPhone());
        user.setRole(dto.getRole());
        user.setStatus("ACTIVE");
        user.setOrgId(orgId);
        user.setCreatedBy(createdBy);
        user.setCreatedAt(LocalDateTime.now());

        UserEntity saved = userJpaRepository.save(user);
        auditLogService.logCreate("User", saved.getId(), saved);
        return toUserDto(saved);
    }

    public UserDto updateUser(String id, UserDto dto, String orgId, String updatedBy) {
        userValidator.validate(dto);
        UserEntity user = userJpaRepository.findByIdAndOrgId(id, orgId)
                .orElseThrow(() -> new NotFoundException("User not found"));

        String oldName = user.getName();
        String oldEmail = user.getEmail();
        String oldRole = user.getRole();
        String oldStatus = user.getStatus();

        user.setName(dto.getName());
        user.setEmail(dto.getEmail());
        user.setRole(dto.getRole());
        user.setStatus(dto.getStatus());
        user.setUpdatedBy(updatedBy);
        user.setUpdatedAt(LocalDateTime.now());

        UserEntity saved = userJpaRepository.save(user);
        UserEntity oldUser = new UserEntity();
        oldUser.setName(oldName);
        oldUser.setEmail(oldEmail);
        oldUser.setRole(oldRole);
        oldUser.setStatus(oldStatus);
        auditLogService.logUpdate("User", saved.getId(), oldUser, saved);
        return toUserDto(saved);
    }

    public void deleteUser(String id, String orgId) {
        UserEntity user = userJpaRepository.findByIdAndOrgId(id, orgId)
                .orElseThrow(() -> new NotFoundException("User not found"));

        user.setDeletedAt(LocalDateTime.now());
        userJpaRepository.save(user);

        auditLogService.logDelete("User", id, user);
    }

    public List<UserDto> searchUsers(String orgId, String search) {
        return userJpaRepository.findByOrgIdAndDeletedAtIsNull(orgId)
                .stream()
                .filter(u -> u.getName() != null && u.getName().toLowerCase().contains(search.toLowerCase())
                        || u.getEmail() != null && u.getEmail().toLowerCase().contains(search.toLowerCase()))
                .map(this::toUserDto)
                .collect(Collectors.toList());
    }

    public Invite createInvite(CreateInviteRequest request, String orgId, String createdBy) {
        userValidator.validateInvite(request);
        if (inviteRepository.existsByEmailAndOrgIdAndStatusAndDeletedAtIsNull(request.getEmail(), orgId, Invite.InviteStatus.PENDING)) {
            throw new ConflictException("Invite already exists for this email");
        }

        Invite invite = new Invite();
        invite.setEmail(request.getEmail());
        invite.setRole(com.moneyops.users.entity.User.Role.valueOf(request.getRole()));
        invite.setToken(UUID.randomUUID().toString().substring(0, 8).toUpperCase());
        invite.setExpiresAt(LocalDateTime.now().plusDays(7));
        invite.setStatus(Invite.InviteStatus.PENDING);
        invite.setOrgId(orgId);
        invite.setCreatedBy(createdBy);

        Invite saved = inviteRepository.save(invite);

        try {
            var org = orgJpaRepository.findById(orgId);
            String orgName = org.map(OrganizationEntity::getName).orElse("MoneyOps");
            emailService.sendInviteEmail(saved.getEmail(), saved.getToken(), orgName, saved.getRole().name());
        } catch (Exception e) {
            log.warn("Failed to send invite email to {}: {}", saved.getEmail(), e.getMessage());
        }

        return saved;
    }

    public UserDto acceptInvite(AcceptInviteRequest request) {
        inviteValidator.validateAcceptInvite(request);

        Invite invite = inviteRepository.findByTokenAndDeletedAtIsNull(request.getToken())
                .orElseThrow(() -> new NotFoundException("Invalid invite token"));

        if (invite.getExpiresAt().isBefore(LocalDateTime.now())) {
            throw new BusinessRuleException("Invite has expired");
        }

        if (Invite.InviteStatus.PENDING != invite.getStatus()) {
            throw new ConflictException("Invite has already been used");
        }

        UserEntity user = new UserEntity();
        user.setName(request.getName());
        user.setEmail(invite.getEmail());
        user.setPhone(request.getPhone());
        user.setRole(invite.getRole().name());
        user.setStatus("ACTIVE");
        user.setOrgId(invite.getOrgId());
        user.setCreatedBy(invite.getCreatedBy());
        user.setCreatedAt(LocalDateTime.now());

        UserEntity saved = userJpaRepository.save(user);

        invite.setStatus(Invite.InviteStatus.ACCEPTED);
        inviteRepository.save(invite);

        return toUserDto(saved);
    }

    public List<Invite> getPendingInvites(String orgId) {
        return inviteRepository.findAllByOrgIdAndStatusAndDeletedAtIsNull(orgId, Invite.InviteStatus.PENDING);
    }

    public Invite getInviteByToken(String token) {
        Invite invite = inviteRepository.findByTokenAndDeletedAtIsNull(token)
                .orElseThrow(() -> new NotFoundException("Invalid invite token"));

        if (invite.getStatus() != Invite.InviteStatus.PENDING) {
            throw new ConflictException("Invite has already been used");
        }

        if (invite.getExpiresAt().isBefore(LocalDateTime.now())) {
            invite.setStatus(Invite.InviteStatus.EXPIRED);
            inviteRepository.save(invite);
            throw new BusinessRuleException("Invite has expired");
        }

        return invite;
    }

    private UserDto toUserDto(UserEntity entity) {
        UserDto dto = new UserDto();
        dto.setId(entity.getId());
        dto.setName(entity.getName());
        dto.setEmail(entity.getEmail());
        dto.setPhone(entity.getPhone());
        dto.setRole(entity.getRole());
        dto.setStatus(entity.getStatus());
        dto.setLastLoginAt(entity.getLastLoginAt());
        dto.setOrgId(entity.getOrgId());
        return dto;
    }
}
