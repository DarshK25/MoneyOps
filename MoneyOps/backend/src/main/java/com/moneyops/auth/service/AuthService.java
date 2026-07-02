// src/main/java/com/moneyops/auth/service/AuthService.java
package com.moneyops.auth.service;

import com.moneyops.auth.dto.LoginRequest;
import com.moneyops.auth.dto.OAuthUserInfo;
import com.moneyops.auth.dto.RegisterRequest;
import com.moneyops.auth.dto.TokenResponse;
import com.moneyops.auth.security.JwtProvider;
import com.moneyops.shared.exceptions.UnauthorizedException;
import com.moneyops.shared.exceptions.ValidationException;
import com.moneyops.users.entity.User;
import com.moneyops.users.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
public class AuthService {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private JwtProvider jwtProvider;

    @Autowired
    private PasswordEncoder passwordEncoder;

    public TokenResponse login(LoginRequest request) {
        User user = userRepository.findByEmailAndDeletedAtIsNull(request.getEmail())
                .orElseThrow(() -> new UnauthorizedException("Invalid email or password"));

        if (user.getPasswordHash() == null || !passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
            throw new UnauthorizedException("Invalid email or password");
        }

        String token = jwtProvider.generateToken(user.getId(), user.getOrgId());
        TokenResponse response = new TokenResponse();
        response.setToken(token);
        response.setUserId(user.getId());
        response.setEmail(user.getEmail());
        response.setName(user.getName());
        response.setOrgId(user.getOrgId());
        return response;
    }

    public TokenResponse register(RegisterRequest request) {
        if (userRepository.findByEmailAndDeletedAtIsNull(request.getEmail()).isPresent()) {
            throw new ValidationException("Email already registered");
        }

        User user = new User();
        ensureUuid(user);
        user.setName(request.getName());
        user.setEmail(request.getEmail());
        user.setPasswordHash(passwordEncoder.encode(request.getPassword()));
        user.setRole(User.Role.STAFF);
        user.setStatus(User.Status.ACTIVE);
        user.setCreatedBy("self");
        user.setUpdatedBy("self");
        user = userRepository.save(user);

        String token = jwtProvider.generateToken(user.getId(), user.getOrgId());
        TokenResponse response = new TokenResponse();
        response.setToken(token);
        response.setUserId(user.getId());
        response.setEmail(user.getEmail());
        response.setName(user.getName());
        response.setOrgId(user.getOrgId());
        return response;
    }

    public String handleOAuth2Login(OAuthUserInfo userInfo) {
        User user = userRepository.findByEmailAndDeletedAtIsNull(userInfo.getEmail())
                .orElseGet(() -> {
                    User newUser = new User();
                    ensureUuid(newUser);
                    newUser.setName(userInfo.getName());
                    newUser.setEmail(userInfo.getEmail());
                    newUser.setRole(User.Role.STAFF);
                    newUser.setStatus(User.Status.ACTIVE);
                    newUser.setCreatedBy("oauth");
                    newUser.setUpdatedBy("oauth");
                    return userRepository.save(newUser);
                });

        return jwtProvider.generateToken(user.getId(), user.getOrgId());
    }

    private void ensureUuid(User user) {
        if (user.getId() == null || user.getId().isBlank()) {
            user.setId(UUID.randomUUID().toString());
        }
    }
}
