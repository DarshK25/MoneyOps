package com.moneyops.gateway.filter;

import com.moneyops.gateway.security.JwtTokenProvider;
import io.jsonwebtoken.Claims;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.ReactiveSecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.AntPathMatcher;
import org.springframework.util.PathMatcher;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;
import reactor.core.publisher.Mono;

import jakarta.annotation.PostConstruct;
import java.util.Arrays;
import java.util.List;

@Slf4j
@Component
@RequiredArgsConstructor
public class AuthenticationFilter implements WebFilter {
    
    private final JwtTokenProvider jwtTokenProvider;
    
    @Value("${gateway.public-endpoints}")
    private String publicEndpointsRaw;

    private List<String> publicEndpoints;

    private final PathMatcher pathMatcher = new AntPathMatcher();

    @PostConstruct
    void initPublicEndpoints() {
        this.publicEndpoints = Arrays.asList(publicEndpointsRaw.split(","));
    }
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getPath().value();
        
        // Allow public endpoints
        if (isPublicEndpoint(path)) {
            return chain.filter(exchange);
        }
        
        // Extract token
        String token = extractToken(request);
        if (token == null) {
            log.warn("No authorization token found for path: {}", path);
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }
        
        try {
            // Validate token and extract claims FROM THE TOKEN
            Claims claims = jwtTokenProvider.validateToken(token);
            String userId = jwtTokenProvider.getUserIdFromToken(token);
            String orgId = jwtTokenProvider.getOrgIdFromToken(token);
            
            // CRITICAL: Don't trust headers - extract from token
            // This prevents header spoofing attacks
            ServerHttpRequest.Builder mutatedBuilder = request.mutate()
                .header("X-User-Id", userId)
                .header("X-Auth-Token", token);
            if (orgId != null) {
                mutatedBuilder.header("X-Org-Id", orgId);
            }
            // Explicitly set Authorization header to ensure it reaches the backend
            // (replaces any original value to avoid duplicates)
            mutatedBuilder.headers(httpHeaders ->
                httpHeaders.set(HttpHeaders.AUTHORIZATION, "Bearer " + token));
            ServerHttpRequest mutatedRequest = mutatedBuilder.build();
            
            log.debug("Authenticated request for userId={}, orgId={}", userId, orgId);
            
            // Populate Spring Security context so anyExchange().authenticated() works
            UsernamePasswordAuthenticationToken auth =
                new UsernamePasswordAuthenticationToken(userId, token, List.of(new SimpleGrantedAuthority("ROLE_USER")));
            
            return chain.filter(exchange.mutate().request(mutatedRequest).build())
                .contextWrite(ReactiveSecurityContextHolder.withAuthentication(auth));
            
        } catch (SecurityException e) {
            log.error("Security validation failed: {}", e.getMessage());
            exchange.getResponse().setStatusCode(HttpStatus.FORBIDDEN);
            return exchange.getResponse().setComplete();
        } catch (Exception e) {
            log.error("Authentication error: {}", e.getMessage());
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }
    }
    
    private boolean isPublicEndpoint(String path) {
        return publicEndpoints.stream()
            .anyMatch(endpoint -> pathMatcher.match(endpoint.trim(), path));
    }
    
    private String extractToken(ServerHttpRequest request) {
        String bearerToken = request.getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
        if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }
}