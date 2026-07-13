package com.moneyops.jpa.repository;

import com.moneyops.jpa.entity.UserEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface UserJpaRepository extends JpaRepository<UserEntity, String> {
    Optional<UserEntity> findByEmail(String email);
    Optional<UserEntity> findByEmailAndDeletedAtIsNull(String email);
    boolean existsByEmailAndDeletedAtIsNull(String email);
    Optional<UserEntity> findByIdAndOrgId(String id, String orgId);
    Optional<UserEntity> findByIdAndOrgIdAndDeletedAtIsNull(String id, String orgId);
    Optional<UserEntity> findByIdAndDeletedAtIsNull(String id);
    List<UserEntity> findByOrgId(String orgId);
    List<UserEntity> findByOrgIdAndDeletedAtIsNull(String orgId);
    List<UserEntity> findByOrgIdAndStatusAndDeletedAtIsNull(String orgId, String status);
    boolean existsByEmailAndOrgId(String email, String orgId);
    Optional<UserEntity> findByEmailAndOrgId(String email, String orgId);
}
