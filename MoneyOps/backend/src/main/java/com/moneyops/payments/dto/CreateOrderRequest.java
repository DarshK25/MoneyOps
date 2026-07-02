package com.moneyops.payments.dto;

import lombok.Data;

@Data
public class CreateOrderRequest {
    private String invoiceId;
    private Double amount;
    private String currency;
    private String receipt;
}
