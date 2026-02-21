package com.moneyops.users.repository;

import com.moneyops.users.entity.Invite;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface InviteRepository extends MongoRepository<Invite, UUID> {

    Optional<Invite> findByToken(String token);
    List<Invite> findAllByOrgId(UUID orgId);
    List<Invite> findAllByOrgIdAndStatus(UUID orgId, Invite.InviteStatus status);
    void deleteAllByExpiresAtBefore(LocalDateTime now);
    boolean existsByEmailAndOrgIdAndStatus(String email, UUID orgId, Invite.InviteStatus status);
}
