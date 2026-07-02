package com.moneyops.payments.dto;

import lombok.Data;

@Data
public class RazorpayOrderResponse {
    private String id;
    private String entity;
    private Integer amount;
    private String currency;
    private String receipt;
    private String status;
    private Long createdAt;
}
