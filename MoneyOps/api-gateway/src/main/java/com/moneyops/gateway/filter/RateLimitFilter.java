package com.moneyops.gateway.filter;

import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.gateway.filter.GatewayFilter;
import org.springframework.cloud.gateway.filter.factory.AbstractGatewayFilterFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class RateLimitFilter extends AbstractGatewayFilterFactory<RateLimitFilter.Config> {
    
    public RateLimitFilter() {
        super(Config.class);
    }
    
    @Override
    public GatewayFilter apply(Config config) {
        return (exchange, chain) -> {
            // Custom rate limiting logic can be added here
            log.debug("Rate limit check for: {}", exchange.getRequest().getPath());
            return chain.filter(exchange);
        };
    }
    
    public static class Config {
        private int limit;
        private int duration;
        
        public int getLimit() { return limit; }
        public void setLimit(int limit) { this.limit = limit; }
        public int getDuration() { return duration; }
        public void setDuration(int duration) { this.duration = duration; }
    }
}