package com.moneyops.clients.repository;

import com.moneyops.clients.entity.Client;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ClientRepository extends MongoRepository<Client, String> {

    boolean existsByEmailAndDeletedAtIsNull(String email);

    Optional<Client> findByIdAndOrgIdAndDeletedAtIsNull(String id, String orgId);

    Page<Client> findAllByOrgIdAndDeletedAtIsNull(String orgId, Pageable pageable);

    boolean existsByIdAndOrgIdAndDeletedAtIsNull(String id, String orgId);

    Optional<Client> findByEmailAndOrgIdAndDeletedAtIsNull(String email, String orgId);

    boolean existsByEmailAndOrgIdAndDeletedAtIsNull(String email, String orgId);

    Page<Client> findAllByOrgIdAndStatusAndDeletedAtIsNull(String orgId, Client.Status status, Pageable pageable);

    // Keep non-paginated for internal use
    List<Client> findAllByOrgIdAndDeletedAtIsNull(String orgId);
    List<Client> findAllByOrgIdAndStatusAndDeletedAtIsNull(String orgId, Client.Status status);

    @org.springframework.data.mongodb.repository.Query("{ 'orgId': ?0, 'deletedAt': null, $or: [ { 'name': { $regex: ?1, $options: 'i' } }, { 'email': { $regex: ?1, $options: 'i' } } ] }")
    List<Client> searchByOrgIdWithFilters(String orgId, String query);
}