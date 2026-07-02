package com.moneyops.users.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class CreateInviteRequest {
    @NotBlank @Email
    private String email;

    @NotBlank
    private String role;
}