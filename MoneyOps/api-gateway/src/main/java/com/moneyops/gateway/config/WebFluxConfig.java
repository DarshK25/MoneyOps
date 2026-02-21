package com.moneyops.gateway.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
/**
 * WebFluxConfig - Additional WebFlux Configuration
 * 
 * PURPOSE:
 * - Configure ObjectMapper for JSON processing
 * - Define KeyResolvers for rate limiting (Phase 3)
 * - Register additional beans for gateway filters
 */
@Configuration
public class WebFluxConfig {
    /**
     * ObjectMapper for JSON processing in filters
     * Configured with Java 8 time support
     */
    @Bean
    public ObjectMapper objectMapper(){
        ObjectMapper mapper = new ObjectMapper();
        mapper.registerModule(new JavaTimeModule());
        return mapper;
    }
}