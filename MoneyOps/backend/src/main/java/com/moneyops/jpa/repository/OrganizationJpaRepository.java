package com.moneyops.jpa.repository;

import com.moneyops.jpa.entity.OrganizationEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface OrganizationJpaRepository extends JpaRepository<OrganizationEntity, String> {
    Optional<OrganizationEntity> findByGstin(String gstin);
    Optional<OrganizationEntity> findByIdAndCreatedBy(String id, String createdBy);
    Optional<OrganizationEntity> findByIdAndCreatedByAndDeletedAtIsNull(String id, String createdBy);
    List<OrganizationEntity> findByCreatedBy(String createdBy);
    List<OrganizationEntity> findByCreatedByAndDeletedAtIsNull(String createdBy);
}
