package com.moneyops.auth.service;

import com.moneyops.auth.dto.LoginRequest;
import com.moneyops.auth.dto.OAuthUserInfo;
import com.moneyops.auth.dto.RegisterRequest;
import com.moneyops.auth.dto.TokenResponse;
import com.moneyops.auth.security.JwtProvider;
import com.moneyops.jpa.entity.UserEntity;
import com.moneyops.jpa.repository.UserJpaRepository;
import com.moneyops.onboarding.service.OnboardingService;
import com.moneyops.shared.exceptions.UnauthorizedException;
import com.moneyops.shared.exceptions.ValidationException;
import com.moneyops.shared.exceptions.ForbiddenException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.UUID;

@Service
public class AuthService {

    @Autowired
    private UserJpaRepository userJpaRepository;

    @Autowired
    private JwtProvider jwtProvider;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private OnboardingService onboardingService;

    public TokenResponse login(LoginRequest request) {
        UserEntity user = userJpaRepository.findByEmailAndDeletedAtIsNull(request.getEmail())
                .orElseThrow(() -> new UnauthorizedException("Invalid email or password"));

        if (user.getPasswordHash() == null || !passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
            throw new UnauthorizedException("Invalid email or password");
        }

        onboardingService.repairOrganizationLink(user.getId());

        TokenResponse response = new TokenResponse();
        response.setToken(jwtProvider.generateToken(user.getId(), user.getOrgId()));
        response.setUserId(user.getId());
        response.setEmail(user.getEmail());
        response.setName(user.getName());
        response.setOrgId(user.getOrgId());
        return response;
    }

    public TokenResponse register(RegisterRequest request) {
        if (userJpaRepository.findByEmailAndDeletedAtIsNull(request.getEmail()).isPresent()) {
            throw new ValidationException("Email already registered");
        }

        UserEntity user = new UserEntity();
        user.setId(UUID.randomUUID().toString());
        user.setName(request.getName());
        user.setEmail(request.getEmail());
        user.setPasswordHash(passwordEncoder.encode(request.getPassword()));
        user.setRole("STAFF");
        user.setStatus("ACTIVE");
        user.setCreatedBy("self");
        user.setUpdatedBy("self");
        user.setCreatedAt(LocalDateTime.now());
        user = userJpaRepository.save(user);

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
        if (!userInfo.isEmailVerified()) {
            throw new ForbiddenException("Email not verified by OAuth provider");
        }

        UserEntity user = userJpaRepository.findByEmailAndDeletedAtIsNull(userInfo.getEmail())
                .orElseGet(() -> {
                    UserEntity newUser = new UserEntity();
                    newUser.setId(UUID.randomUUID().toString());
                    newUser.setName(userInfo.getName());
                    newUser.setEmail(userInfo.getEmail());
                    newUser.setRole("STAFF");
                    newUser.setStatus("ACTIVE");
                    newUser.setCreatedBy("oauth");
                    newUser.setUpdatedBy("oauth");
                    newUser.setCreatedAt(LocalDateTime.now());
                    return userJpaRepository.save(newUser);
                });

        user.setLastLoginAt(LocalDateTime.now());
        userJpaRepository.save(user);

        onboardingService.repairOrganizationLink(user.getId());

        return jwtProvider.generateToken(user.getId(), user.getOrgId());
    }
}
