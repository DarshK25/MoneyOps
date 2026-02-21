package com.moneyops.users.repository;

import com.moneyops.users.entity.User;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface UserRepository extends MongoRepository<User, UUID> {

    Optional<User> findByIdAndOrgId(UUID id, UUID orgId);
    List<User> findAllByOrgId(UUID orgId);
    boolean existsByIdAndOrgId(UUID id, UUID orgId);
    void deleteByIdAndOrgId(UUID id, UUID orgId);
    Optional<User> findByEmailAndOrgId(String email, UUID orgId);
    Optional<User> findByEmail(String email);
    boolean existsByEmailAndOrgId(String email, UUID orgId);
    boolean existsByEmail(String email);

    @Query("{ 'orgId' : ?0, $or: [ { 'name': { $regex: ?1, $options: 'i' } }, { 'email': { $regex: ?1, $options: 'i' } } ] }")
    List<User> searchByOrgIdWithFilters(UUID orgId, String search);

    List<User> findAllByOrgIdAndRole(UUID orgId, String role);
    List<User> findAllByOrgIdAndStatus(UUID orgId, String status);
}
