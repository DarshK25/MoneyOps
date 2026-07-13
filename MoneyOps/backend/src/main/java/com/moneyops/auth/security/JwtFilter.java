// src/main/java/com/moneyops/auth/security/JwtFilter.java
package com.moneyops.auth.security;

import com.moneyops.jpa.entity.UserEntity;
import com.moneyops.jpa.repository.UserJpaRepository;
import com.moneyops.shared.utils.OrgContext;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Optional;

@Component
@Slf4j
public class JwtFilter extends OncePerRequestFilter {

    @Autowired
    private JwtProvider jwtProvider;

    @Autowired
    private UserJpaRepository userJpaRepository;

    @Autowired
    private UserDetailsService userDetailsService;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        if (SecurityContextHolder.getContext().getAuthentication() != null
                && SecurityContextHolder.getContext().getAuthentication().isAuthenticated()) {
            filterChain.doFilter(request, response);
            return;
        }

        String token = getJwtFromRequest(request);

        if (token != null && jwtProvider.validateToken(token)) {
            final String userId = jwtProvider.getUserIdFromToken(token);
            UserDetails userDetails = userDetailsService.loadUserByUsername(userId);

            UsernamePasswordAuthenticationToken authentication =
                    new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
            authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));

            SecurityContextHolder.getContext().setAuthentication(authentication);

            try {
                Optional<UserEntity> userOpt = userJpaRepository.findById(userId);

                userOpt.ifPresentOrElse(user -> {
                    if (user.getDeletedAt() != null) {
                        log.warn("Authenticated user {} is soft-deleted", user.getId());
                        return;
                    }
                    OrgContext.setUserId(user.getId());
                    if (user.getOrgId() != null) {
                        OrgContext.setOrgId(user.getOrgId());
                    }
                }, () -> {
                    OrgContext.setUserId(userId);
                });

                log.debug("Final context - User: {}, Org: {}", OrgContext.getUserId(), OrgContext.getOrgId());
                filterChain.doFilter(request, response);
            } finally {
                OrgContext.clear();
            }
        } else {
            filterChain.doFilter(request, response);
        }
    }

    private String getJwtFromRequest(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }
}
