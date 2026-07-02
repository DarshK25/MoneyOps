package com.moneyops.auth.config;

import org.springframework.boot.autoconfigure.security.oauth2.client.OAuth2ClientProperties;
import org.springframework.boot.autoconfigure.security.oauth2.client.OAuth2ClientPropertiesRegistrationAdapter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.oauth2.client.registration.ClientRegistration;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;
import org.springframework.security.oauth2.client.registration.InMemoryClientRegistrationRepository;

import java.util.ArrayList;
import java.util.List;

@Configuration
public class OAuth2Config {

    @Bean
    public ClientRegistrationRepository clientRegistrationRepository(
            OAuth2ClientProperties properties) {
        List<ClientRegistration> registrations = new ArrayList<>(
            OAuth2ClientPropertiesRegistrationAdapter.getClientRegistrations(properties).values()
        );
        List<ClientRegistration> trimmed = new ArrayList<>();
        for (ClientRegistration reg : registrations) {
            trimmed.add(ClientRegistration.withClientRegistration(reg)
                .clientId(reg.getClientId().strip())
                .clientSecret(reg.getClientSecret() != null ? reg.getClientSecret().strip() : null)
                .build());
        }
        return new InMemoryClientRegistrationRepository(trimmed);
    }
}
