package com.moneyops.auth;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.moneyops.auth.security.JwtProvider;
import com.moneyops.jpa.entity.UserEntity;
import com.moneyops.jpa.repository.UserJpaRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;
import java.util.UUID;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests: JWT → /api/users/me → /api/onboarding/status
 *
 * Uses the real application context with H2 in-memory DB (test profile),
 * Spring Security active, and JwtProvider wired to the test JWT secret.
 *
 * Two scenarios:
 *  A) Existing user who has already completed onboarding (orgId set) →
 *     /api/users/me returns orgId, /api/onboarding/status returns onboardingComplete:true
 *
 *  B) Brand-new user who has never started onboarding →
 *     /api/users/me returns orgId:null, /api/onboarding/status returns onboardingComplete:false
 *
 * NOTE: The browser-redirect OAuth2 flow (OAuth2SuccessHandler → Google → redirect)
 * CANNOT be exercised via MockMvc without a live Google session.  What IS tested here
 * is every step from a valid JWT inward — which is the part that matters for service
 * correctness; the OAuth redirect step is a thin adapter that just calls handleOAuth2Login.
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class AuthOnboardingIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private JwtProvider jwtProvider;

    @Autowired
    private UserJpaRepository userJpaRepository;

    @Autowired
    private ObjectMapper objectMapper;

    private String existingUserId;
    private String existingOrgId;
    private String newUserId;

    @BeforeEach
    void setUp() {
        userJpaRepository.deleteAll();

        // --- Existing user (onboarding complete) ---
        existingOrgId = UUID.randomUUID().toString();
        existingUserId = UUID.randomUUID().toString();

        UserEntity existing = new UserEntity();
        existing.setId(existingUserId);
        existing.setEmail("existing@voltnest.io");
        existing.setName("Volt Nest User");
        existing.setRole("OWNER");
        existing.setStatus("ACTIVE");
        existing.setOrgId(existingOrgId);
        existing.setOnboardingComplete(true);
        existing.setCreatedBy("oauth");
        existing.setUpdatedBy("oauth");
        existing.setCreatedAt(LocalDateTime.now().minusDays(10));
        userJpaRepository.save(existing);

        // --- Brand-new user (onboarding NOT complete) ---
        newUserId = UUID.randomUUID().toString();

        UserEntity newUser = new UserEntity();
        newUser.setId(newUserId);
        newUser.setEmail("newuser@voltnest.io");
        newUser.setName("New User");
        newUser.setRole("STAFF");
        newUser.setStatus("ACTIVE");
        newUser.setOrgId(null);
        newUser.setOnboardingComplete(false);
        newUser.setCreatedBy("oauth");
        newUser.setUpdatedBy("oauth");
        newUser.setCreatedAt(LocalDateTime.now());
        userJpaRepository.save(newUser);
    }

    // ─── Scenario A: existing user with orgId ─────────────────────────────────

    @Test
    void existingUser_usersMe_returnsCorrectOrgId() throws Exception {
        String token = jwtProvider.generateToken(existingUserId, existingOrgId);

        mockMvc.perform(get("/api/users/me")
                        .header("Authorization", "Bearer " + token)
                        .header("X-User-Id", existingUserId)
                        .header("X-Org-Id", existingOrgId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(existingUserId))
                .andExpect(jsonPath("$.orgId").value(existingOrgId))
                .andExpect(jsonPath("$.email").value("existing@voltnest.io"));
    }

    @Test
    void existingUser_onboardingStatus_returnsComplete() throws Exception {
        String token = jwtProvider.generateToken(existingUserId, existingOrgId);

        mockMvc.perform(get("/api/onboarding/status")
                        .header("Authorization", "Bearer " + token)
                        .param("userId", existingUserId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.onboardingComplete").value(true))
                .andExpect(jsonPath("$.data.orgId").value(existingOrgId));
    }

    // ─── Scenario B: brand-new user, no orgId ────────────────────────────────

    @Test
    void newUser_usersMe_returnsNullOrgId() throws Exception {
        String token = jwtProvider.generateToken(newUserId, null);

        mockMvc.perform(get("/api/users/me")
                        .header("Authorization", "Bearer " + token)
                        .header("X-User-Id", newUserId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(newUserId))
                .andExpect(jsonPath("$.orgId").doesNotExist());
    }

    @Test
    void newUser_onboardingStatus_returnsIncomplete() throws Exception {
        String token = jwtProvider.generateToken(newUserId, null);

        mockMvc.perform(get("/api/onboarding/status")
                        .header("Authorization", "Bearer " + token)
                        .param("userId", newUserId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.onboardingComplete").value(false))
                .andExpect(jsonPath("$.data.orgId").doesNotExist());
    }

    // ─── Missing/invalid JWT → 401 ───────────────────────────────────────────

    @Test
    void noToken_usersMe_returns401() throws Exception {
        mockMvc.perform(get("/api/users/me"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void invalidToken_usersMe_returns401() throws Exception {
        mockMvc.perform(get("/api/users/me")
                        .header("Authorization", "Bearer garbage.token.here"))
                .andExpect(status().isUnauthorized());
    }
}
