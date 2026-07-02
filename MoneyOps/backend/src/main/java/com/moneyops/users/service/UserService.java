package com.moneyops.users.service;

import com.moneyops.audit.service.AuditLogService;
import com.moneyops.email.EmailService;
import com.moneyops.jpa.entity.UserEntity;
import com.moneyops.jpa.repository.UserJpaRepository;
import com.moneyops.organizations.repository.BusinessOrganizationRepository;
import com.moneyops.users.dto.UserDto;
import com.moneyops.users.dto.CreateInviteRequest;
import com.moneyops.users.dto.AcceptInviteRequest;
import com.moneyops.users.entity.User;
import com.moneyops.users.entity.Invite;
import com.moneyops.users.mapper.UserMapper;
import com.moneyops.users.repository.UserRepository;
import com.moneyops.users.repository.InviteRepository;
import com.moneyops.users.validator.UserValidator;
import com.moneyops.users.validator.InviteValidator;
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
    private UserRepository userRepository;

    @Autowired
    private UserJpaRepository userJpaRepository;

    @Autowired
    private InviteRepository inviteRepository;

    @Autowired
    private UserMapper userMapper;

    @Autowired
    private UserValidator userValidator;

    @Autowired
    private InviteValidator inviteValidator;

    @Autowired
    private AuditLogService auditLogService;

    @Autowired
    private EmailService emailService;

    @Autowired
    private BusinessOrganizationRepository orgRepository;

    public List<UserDto> getAllUsers(String orgId) {
        var jpaUsers = userJpaRepository.findByOrgId(orgId);
        if (!jpaUsers.isEmpty()) {
            log.debug("Read users from PostgreSQL");
            return jpaUsers.stream()
                    .map(this::toUserDto)
                    .collect(Collectors.toList());
        }
        log.warn("Falling back to MongoDB for users");
        return userRepository.findAllByOrgIdAndDeletedAtIsNull(orgId)
                .stream()
                .map(userMapper::toDto)
                .collect(Collectors.toList());
    }

    public UserDto getUserById(String id, String orgId) {
        try {
            var jpaUser = userJpaRepository.findByIdAndOrgId(id, orgId);
            if (jpaUser.isPresent()) {
                log.debug("Read user {} from PostgreSQL", id);
                return toUserDto(jpaUser.get());
            }
        } catch (IllegalArgumentException ex) {
            log.warn("Skipping PostgreSQL user lookup for non-UUID id {}", id);
        }
        log.warn("Falling back to MongoDB for user {}", id);
        User user = userRepository.findByIdAndOrgIdAndDeletedAtIsNull(id, orgId)
                .orElseThrow(() -> new RuntimeException("User not found"));
        return userMapper.toDto(user);
    }

    public User findUserById(String id) {
        try {
            var jpaUser = userJpaRepository.findById(id);
            if (jpaUser.isPresent()) {
                log.debug("Read user {} from PostgreSQL", id);
                return toUser(jpaUser.get());
            }
        } catch (IllegalArgumentException ex) {
            log.warn("Skipping PostgreSQL user lookup for non-UUID id {}", id);
        }
        return userRepository.findById(id).orElse(null);
    }

    public UserDto createUser(UserDto dto, String orgId, String createdBy) {
        userValidator.validate(dto);
        if (userRepository.existsByEmailAndOrgIdAndDeletedAtIsNull(dto.getEmail(), orgId)) {
            throw new RuntimeException("User with this email already exists");
        }

        User user = userMapper.toEntity(dto);
        user.setOrgId(orgId);
        user.setCreatedBy(createdBy);

        User saved = userRepository.save(user);
        saveUserJpa(saved);
        auditLogService.logCreate("User", saved.getId(), saved);
        return userMapper.toDto(saved);
    }

    public UserDto updateUser(String id, UserDto dto, String orgId, String updatedBy) {
        userValidator.validate(dto);
        User user = userRepository.findByIdAndOrgIdAndDeletedAtIsNull(id, orgId)
                .orElseThrow(() -> new RuntimeException("User not found"));

        User oldUser = new User();
        oldUser.setName(user.getName());
        oldUser.setEmail(user.getEmail());
        oldUser.setRole(user.getRole());
        oldUser.setStatus(user.getStatus());

        user.setName(dto.getName());
        user.setEmail(dto.getEmail());
        user.setRole(User.Role.valueOf(dto.getRole()));
        user.setStatus(User.Status.valueOf(dto.getStatus()));
        user.setUpdatedBy(updatedBy);

        User saved = userRepository.save(user);
        saveUserJpa(saved);
        auditLogService.logUpdate("User", saved.getId(), oldUser, saved);
        return userMapper.toDto(saved);
    }

    public void deleteUser(String id, String orgId) {
        User user = userRepository.findByIdAndOrgIdAndDeletedAtIsNull(id, orgId)
                .orElseThrow(() -> new RuntimeException("User not found"));

        user.setDeletedAt(LocalDateTime.now());
        userRepository.save(user);
        userJpaRepository.deleteById(id);

        auditLogService.logDelete("User", id, user);
    }

    public List<UserDto> searchUsers(String orgId, String search) {
        return userRepository.searchByOrgIdWithFilters(orgId, search)
                .stream()
                .map(userMapper::toDto)
                .collect(Collectors.toList());
    }

    public Invite createInvite(CreateInviteRequest request, String orgId, String createdBy) {
        userValidator.validateInvite(request);
        if (inviteRepository.existsByEmailAndOrgIdAndStatusAndDeletedAtIsNull(request.getEmail(), orgId, Invite.InviteStatus.PENDING)) {
            throw new RuntimeException("Invite already exists for this email");
        }

        Invite invite = new Invite();
        invite.setEmail(request.getEmail());
        invite.setRole(User.Role.valueOf(request.getRole()));
        invite.setToken(UUID.randomUUID().toString().substring(0, 8).toUpperCase());
        invite.setExpiresAt(LocalDateTime.now().plusDays(7));
        invite.setStatus(Invite.InviteStatus.PENDING);
        invite.setOrgId(orgId);
        invite.setCreatedBy(createdBy);

        Invite saved = inviteRepository.save(invite);

        try {
            var org = orgRepository.findByIdAndDeletedAtIsNull(orgId).orElse(null);
            String orgName = org != null ? org.getLegalName() : "MoneyOps";
            emailService.sendInviteEmail(saved.getEmail(), saved.getToken(), orgName, saved.getRole().name());
        } catch (Exception e) {
            log.warn("Failed to send invite email to {}: {}", saved.getEmail(), e.getMessage());
        }

        return saved;
    }

    public UserDto acceptInvite(AcceptInviteRequest request) {
        inviteValidator.validateAcceptInvite(request);

        Invite invite = inviteRepository.findByTokenAndDeletedAtIsNull(request.getToken())
                .orElseThrow(() -> new RuntimeException("Invalid invite token"));

        if (invite.getExpiresAt().isBefore(LocalDateTime.now())) {
            throw new RuntimeException("Invite has expired");
        }

        if (Invite.InviteStatus.PENDING != invite.getStatus()) {
            throw new RuntimeException("Invite has already been used");
        }

        User user = new User();
        user.setName(request.getName());
        user.setEmail(invite.getEmail());
        user.setPhone(request.getPhone());
        user.setRole(invite.getRole());
        user.setStatus(User.Status.ACTIVE);
        user.setOrgId(invite.getOrgId());
        user.setCreatedBy(invite.getCreatedBy());

        User saved = userRepository.save(user);
        saveUserJpa(saved);

        invite.setStatus(Invite.InviteStatus.ACCEPTED);
        inviteRepository.save(invite);

        return userMapper.toDto(saved);
    }

    public List<Invite> getPendingInvites(String orgId) {
        return inviteRepository.findAllByOrgIdAndStatusAndDeletedAtIsNull(orgId, Invite.InviteStatus.PENDING);
    }

    public Invite getInviteByToken(String token) {
        Invite invite = inviteRepository.findByTokenAndDeletedAtIsNull(token)
                .orElseThrow(() -> new RuntimeException("Invalid invite token"));

        if (invite.getStatus() != Invite.InviteStatus.PENDING) {
            throw new RuntimeException("Invite has already been used");
        }

        if (invite.getExpiresAt().isBefore(LocalDateTime.now())) {
            invite.setStatus(Invite.InviteStatus.EXPIRED);
            inviteRepository.save(invite);
            throw new RuntimeException("Invite has expired");
        }

        return invite;
    }

    private void saveUserJpa(User user) {
        try {
            UserEntity entity = new UserEntity();
            entity.setId(user.getId());
            entity.setClerkUserId(user.getId());
            entity.setEmail(user.getEmail());
            entity.setName(user.getName());
            entity.setOrgId(user.getOrgId());
            entity.setRole(user.getRole() != null ? user.getRole().name() : null);
            entity.setCreatedAt(user.getCreatedAt());
            entity.setUpdatedAt(user.getUpdatedAt());
            userJpaRepository.save(entity);
            log.debug("User {} written to PostgreSQL", user.getId());
        } catch (Exception e) {
            log.error("Failed to write user {} to PostgreSQL: {}", user.getId(), e.getMessage());
        }
    }

    private UserDto toUserDto(UserEntity entity) {
        UserDto dto = new UserDto();
        dto.setId(entity.getId());
        dto.setName(entity.getName());
        dto.setEmail(entity.getEmail());
        dto.setRole(entity.getRole());
        return dto;
    }

    private User toUser(UserEntity entity) {
        User user = new User();
        user.setId(entity.getId());
        user.setName(entity.getName());
        user.setEmail(entity.getEmail());
        user.setOrgId(entity.getOrgId());
        if (entity.getRole() != null) {
            user.setRole(User.Role.valueOf(entity.getRole()));
        }
        return user;
    }
}
