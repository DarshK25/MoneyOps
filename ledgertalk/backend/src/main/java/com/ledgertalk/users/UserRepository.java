// src/main/java/com/ledgertalk/users/UserRepository.java
package com.ledgertalk.users;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
}