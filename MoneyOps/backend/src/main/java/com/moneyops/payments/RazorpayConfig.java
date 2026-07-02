package com.moneyops.payments;

import com.razorpay.RazorpayClient;
import com.razorpay.RazorpayException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Configuration
public class RazorpayConfig {

    private static final Logger log = LoggerFactory.getLogger(RazorpayConfig.class);

    @Value("${RAZORPAY_KEY_ID:}")
    private String keyId;

    @Value("${RAZORPAY_KEY_SECRET:}")
    private String keySecret;

    @Bean
    public RazorpayClient razorpayClient() {
        if (keyId.isEmpty() || keySecret.isEmpty()) {
            return null;
        }
        try {
            return new RazorpayClient(keyId, keySecret);
        } catch (RazorpayException e) {
            log.error("Failed to initialize RazorpayClient: {}", e.getMessage());
            return null;
        }
    }
}
