package com.moneyops.auth.dto;

import lombok.Data;

@Data
public class TokenResponse {
    private String token;
    private String userId;
    private String email;
    private String name;
    private String orgId;
    private long expiresIn;
}
