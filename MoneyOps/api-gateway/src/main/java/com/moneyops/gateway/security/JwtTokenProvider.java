package com.moneyops.gateway.security;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;


@Slf4j
@Component
public class JwtTokenProvider {
    
    private final SecretKey secretKey;
    private final long validityInMilliseconds;
    
    public JwtTokenProvider(
            @Value("${jwt.secret}") String secret,
            @Value("${jwt.expiration}") long validityInMilliseconds) {
        this.secretKey = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        this.validityInMilliseconds = validityInMilliseconds;
    }
    
    /**
     * Generate JWT token with userId and orgId claims
     */
    public String generateToken(String userId, String orgId) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("userId", userId);
        claims.put("orgId", orgId);
        
        Date now = new Date();
        Date validity = new Date(now.getTime() + validityInMilliseconds);
        
        return Jwts.builder()
            .claims(claims)
            .subject(userId)
            .issuedAt(now)
            .expiration(validity)
            .signWith(secretKey)
            .compact();
    }
    
    /**
     * Validate JWT and return claims
     */
    public Claims validateToken(String token) {
        try {
            return Jwts.parser()
                .verifyWith(secretKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
        } catch (ExpiredJwtException e) {
            log.error("JWT token expired: {}", e.getMessage());
            throw new IllegalArgumentException("JWT token expired");
        } catch (JwtException | IllegalArgumentException e) {
            log.error("JWT validation error: {}", e.getMessage());
            throw new IllegalArgumentException("Invalid JWT token");
        }
    }
    
    public String getUserIdFromToken(String token) {
        Claims claims = validateToken(token);
        String userId = claims.get("userId", String.class);
        if (userId == null) {
            // Fall back to subject claim (backends may use subject instead of userId claim)
            userId = claims.getSubject();
        }
        if (userId == null) {
            throw new IllegalArgumentException("JWT token missing userId claim and subject");
        }
        return userId;
    }
    
    public String getOrgIdFromToken(String token) {
        try {
            Claims claims = validateToken(token);
            String orgId = claims.get("orgId", String.class);
            if (orgId == null) {
                // orgId is optional — some flows (OAuth) may not include it
                return null;
            }
            return orgId;
        } catch (Exception e) {
            return null;
        }
    }
    
    /**
     * CRITICAL: Validate that X-Org-Id and X-User-Id headers match JWT claims
     */
    public void validateHeadersAgainstToken(String token, String headerOrgId, String headerUserId) {
        String tokenUserId = getUserIdFromToken(token);
        
        if (!tokenUserId.equals(headerUserId)) {
            log.error("Header userId {} doesn't match token userId {}", headerUserId, tokenUserId);
            throw new SecurityException("User ID mismatch between header and token");
        }
        
        // orgId validation is optional — skip if token or header lacks it
        String tokenOrgId = getOrgIdFromToken(token);
        if (tokenOrgId != null && headerOrgId != null && !tokenOrgId.equals(headerOrgId)) {
            log.error("Header orgId {} doesn't match token orgId {}", headerOrgId, tokenOrgId);
            throw new SecurityException("Organization ID mismatch between header and token");
        }
    }
    
    public boolean isTokenExpired(String token) {
        try {
            Claims claims = validateToken(token);
            return claims.getExpiration().before(new Date());
        } catch (Exception e) {
            return true;
        }
    }
}

