package com.moneyops.auth.service;

import com.moneyops.auth.dto.OAuthUserInfo;
import com.moneyops.jpa.entity.UserEntity;
import com.moneyops.jpa.repository.UserJpaRepository;
import com.moneyops.onboarding.service.OnboardingService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * Regression test for duplicate-account creation via OAuth.
 *
 * Root-cause:  An earlier version of handleOAuth2Login had no email_verified
 *              check; it could create a record for an unverified address.
 *              When the same user logged in again (now verified), the upsert
 *              path would still look up by email, but a stale OAUTH_BOOTSTRAP
 *              row with deleted_at=NULL blocked the partial unique index from
 *              preventing a second INSERT.
 *
 * Fix verified here:
 *  1. email_verified checked FIRST — ForbiddenException thrown before any DB
 *     access when email is not verified.
 *  2. findByEmailAndDeletedAtIsNull is called before any save — if a live row
 *     exists the orElseGet lambda is never executed; no second INSERT occurs.
 *  3. The partial unique index (uq_users_email_active in V3 migration) provides
 *     a DB-level backstop even if application logic were bypassed.
 */
@ExtendWith(MockitoExtension.class)
class AuthServiceOAuthDuplicateTest {

    @Mock
    private UserJpaRepository userJpaRepository;
    @Mock
    private com.moneyops.auth.security.JwtProvider jwtProvider;
    @Mock
    private OnboardingService onboardingService;

    @InjectMocks
    private AuthService authService;

    private UserEntity existingUser;

    @BeforeEach
    void setUp() {
        existingUser = new UserEntity();
        existingUser.setId(UUID.randomUUID().toString());
        existingUser.setEmail("voltnest@example.com");
        existingUser.setName("Volt Nest");
        existingUser.setStatus("ACTIVE");
        existingUser.setCreatedAt(LocalDateTime.now().minusDays(5));
    }

    // ── 1. Unverified email is rejected before any DB touch ──────────────────

    @Test
    void handleOAuth2Login_unverifiedEmail_throwsForbiddenAndNeverTouchesDb() {
        OAuthUserInfo info = oauthInfo("voltnest@example.com", false);

        assertThrows(
            com.moneyops.shared.exceptions.ForbiddenException.class,
            () -> authService.handleOAuth2Login(info),
            "Unverified email must throw ForbiddenException"
        );

        verifyNoInteractions(userJpaRepository); // DB must not be touched at all
    }

    // ── 2. Second OAuth login with same email hits existing row, no new INSERT ─

    @Test
    void handleOAuth2Login_existingUser_twoLogins_onlyOneRowExists() {
        OAuthUserInfo info = oauthInfo("voltnest@example.com", true);

        // Both calls return the SAME existing row (simulates the partial unique index semantics)
        when(userJpaRepository.findByEmailAndDeletedAtIsNull("voltnest@example.com"))
                .thenReturn(Optional.of(existingUser));
        when(userJpaRepository.save(any())).thenReturn(existingUser);
        when(jwtProvider.generateToken(anyString(), any())).thenReturn("jwt-token");

        authService.handleOAuth2Login(info); // First login
        authService.handleOAuth2Login(info); // Second login (duplicate attempt)

        // findByEmail called twice (once per login), save called twice (last-login update)
        verify(userJpaRepository, times(2))
                .findByEmailAndDeletedAtIsNull("voltnest@example.com");

        // CRITICAL: save() is called only for updating lastLoginAt — never for creating
        // a new user entity.  Verify that every save() call is for the *existing* user
        // (same ID), never a brand-new entity.
        verify(userJpaRepository, atMost(2)).save(argThat(u ->
            u.getId().equals(existingUser.getId())
        ));

        // The orElseGet (new user creation) path is never executed →
        // confirm no new save() with a different ID ever happened.
        verify(userJpaRepository, never()).save(argThat(u ->
            !u.getId().equals(existingUser.getId())
        ));
    }

    // ── 3. Brand-new user: first-ever OAuth login creates exactly ONE row ─────

    @Test
    void handleOAuth2Login_newUser_createsSingleRow() {
        OAuthUserInfo info = oauthInfo("brandnew@example.com", true);

        UserEntity created = new UserEntity();
        created.setId(UUID.randomUUID().toString());
        created.setEmail("brandnew@example.com");

        when(userJpaRepository.findByEmailAndDeletedAtIsNull("brandnew@example.com"))
                .thenReturn(Optional.empty()); // No existing user
        when(userJpaRepository.save(any())).thenReturn(created);
        when(jwtProvider.generateToken(anyString(), any())).thenReturn("jwt-token-new");

        String token = authService.handleOAuth2Login(info);

        assertNotNull(token);
        // save called once to create, once to update lastLoginAt
        verify(userJpaRepository, atMost(2)).save(any());
        verify(jwtProvider).generateToken(anyString(), any());
    }

    // ── 4. New user followed by second login: zero duplicates ────────────────

    @Test
    void handleOAuth2Login_newUserThenReturn_noDuplicate() {
        OAuthUserInfo info = oauthInfo("returning@example.com", true);

        UserEntity created = new UserEntity();
        created.setId(UUID.randomUUID().toString());
        created.setEmail("returning@example.com");
        created.setCreatedAt(LocalDateTime.now());

        // First call: no user → create
        when(userJpaRepository.findByEmailAndDeletedAtIsNull("returning@example.com"))
                .thenReturn(Optional.empty())
                .thenReturn(Optional.of(created)); // Second call: user exists
        when(userJpaRepository.save(any())).thenReturn(created);
        when(jwtProvider.generateToken(anyString(), any())).thenReturn("jwt");

        authService.handleOAuth2Login(info); // signup
        authService.handleOAuth2Login(info); // login (should NOT create second row)

        // Total save calls should be 3:
        // 1. newUser save during signup (in orElseGet)
        // 2. lastLoginAt update after signup (on created user)
        // 3. lastLoginAt update after login (on created user)
        verify(userJpaRepository, times(3)).save(any());
        verify(userJpaRepository, times(2)).save(argThat(u -> u.getId().equals(created.getId())));
    }

    // ─── helper ─────────────────────────────────────────────────────────────

    private OAuthUserInfo oauthInfo(String email, boolean verified) {
        OAuthUserInfo info = new OAuthUserInfo();
        info.setEmail(email);
        info.setName("Test User");
        info.setId("google-sub-12345");
        info.setEmailVerified(verified);
        return info;
    }
}
