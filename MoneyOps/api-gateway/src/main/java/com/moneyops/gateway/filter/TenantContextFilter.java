package com.moneyops.gateway.filter;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.util.AntPathMatcher;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;
import reactor.core.publisher.Mono;

import jakarta.annotation.PostConstruct;
import java.util.Arrays;
import java.util.List;

import org.springframework.security.core.context.ReactiveSecurityContextHolder;

/**
 * TenantContextFilter - Enforces Multi-Tenant Isolation
 * 
 * PURPOSE:
 * - Ensures every tenant-scoped request has a valid X-Org-Id header
 * - Prevents tenant data leakage by validating org context exists
 * - Runs AFTER AuthenticationFilter (which sets X-Org-Id from JWT)
 * 
 * BUSINESS LOGIC:
 * - For tenant-required paths (/api/clients/**, /api/invoices/**, etc.):
 *   → MUST have X-Org-Id header (set by AuthenticationFilter)
 *   → If missing, reject with 403 Forbidden
 * - For other paths:
 *   → Allow without org context
 * 
 * SECURITY:
 * - X-Org-Id comes from JWT (validated by AuthenticationFilter)
 * - Cannot be spoofed by client headers
 * - Backend services trust this header for tenant filtering
 */
@Slf4j
@Component
@Order(Ordered.LOWEST_PRECEDENCE)  // Run after Security chain (AuthenticationFilter sets X-Org-Id from JWT)
@RequiredArgsConstructor
public class TenantContextFilter implements WebFilter {
    
    @Value("${gateway.tenant.enforce-isolation:true}")
    private boolean enforceTenantIsolation;
    
    @Value("${gateway.tenant.required-paths}")
    private String tenantRequiredPathsRaw;

    private List<String> tenantRequiredPaths;

    @PostConstruct
    void initTenantPaths() {
        this.tenantRequiredPaths = Arrays.asList(tenantRequiredPathsRaw.split(","));
    }
    
    private final AntPathMatcher pathMatcher = new AntPathMatcher();
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getPath().value();
        
        // Skip tenant check if enforcement is disabled (e.g., dev environment)
        if (!enforceTenantIsolation) {
            log.debug("Tenant isolation disabled - allowing request to {}", path);
            return chain.filter(exchange);
        }
        
        // Check if this path requires tenant context
        if (requiresTenantContext(path)) {
            String orgId = request.getHeaders().getFirst("X-Org-Id");
            
            if (orgId == null || orgId.isBlank()) {
                log.warn("Tenant isolation violation: Missing X-Org-Id for path {}", path);
                exchange.getResponse().setStatusCode(HttpStatus.FORBIDDEN);
                return exchange.getResponse().setComplete();
            }
            
            log.debug("Tenant context validated: orgId={} for path={}", orgId, path);
        }
        
        return chain.filter(exchange);
    }
    
    /**
     * Check if the given path requires tenant context
     */
    private boolean requiresTenantContext(String path) {
        return tenantRequiredPaths.stream()
            .map(String::trim)
            .anyMatch(pattern -> pathMatcher.match(pattern, path));
    }
}