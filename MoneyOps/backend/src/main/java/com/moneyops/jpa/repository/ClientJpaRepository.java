package com.moneyops.jpa.repository;

import com.moneyops.jpa.entity.ClientEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ClientJpaRepository extends JpaRepository<ClientEntity, String> {
    List<ClientEntity> findByOrgId(String orgId);
    List<ClientEntity> findByOrgIdAndDeletedAtIsNull(String orgId);
    Optional<ClientEntity> findByIdAndOrgId(String id, String orgId);
    Optional<ClientEntity> findByIdAndOrgIdAndDeletedAtIsNull(String id, String orgId);
    boolean existsByEmailAndOrgId(String email, String orgId);
    boolean existsByEmailAndOrgIdAndDeletedAtIsNull(String email, String orgId);
    Optional<ClientEntity> findByEmailAndOrgId(String email, String orgId);
}
