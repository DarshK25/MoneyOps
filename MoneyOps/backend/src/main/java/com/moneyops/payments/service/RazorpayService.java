package com.moneyops.payments.service;

import com.moneyops.invoices.entity.Invoice;
import com.moneyops.invoices.repository.InvoiceRepository;
import com.moneyops.payments.dto.CreateOrderRequest;
import com.moneyops.payments.dto.RazorpayOrderResponse;
import com.moneyops.shared.exceptions.BusinessRuleException;
import com.razorpay.Order;
import com.razorpay.RazorpayClient;
import com.razorpay.Utils;
import org.json.JSONObject;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Service
public class RazorpayService {

    @Autowired(required = false)
    private RazorpayClient razorpayClient;

    @Value("${RAZORPAY_KEY_SECRET:}")
    private String keySecret;

    public RazorpayOrderResponse createOrder(CreateOrderRequest request) {
        if (razorpayClient == null) {
            throw new BusinessRuleException("Razorpay not configured");
        }

        try {
            JSONObject options = new JSONObject();
            options.put("amount", (int) (request.getAmount() * 100)); // paise
            options.put("currency", request.getCurrency() != null ? request.getCurrency() : "INR");
            options.put("receipt", request.getReceipt() != null ? request.getReceipt() : "rcpt_" + System.currentTimeMillis());
            options.put("payment_capture", 1);

            Order order = razorpayClient.orders.create(options);
            JSONObject orderJson = order.toJson();

            RazorpayOrderResponse response = new RazorpayOrderResponse();
            response.setId(orderJson.optString("id", null));
            response.setEntity(orderJson.optString("entity", null));
            response.setAmount(orderJson.has("amount") ? orderJson.optInt("amount") : null);
            response.setCurrency(orderJson.optString("currency", null));
            response.setReceipt(orderJson.optString("receipt", null));
            response.setStatus(orderJson.optString("status", null));
            response.setCreatedAt(orderJson.has("created_at") ? orderJson.optLong("created_at") : null);

            return response;
        } catch (Exception e) {
            throw new BusinessRuleException("Failed to create Razorpay order: " + e.getMessage(), e);
        }
    }

    public boolean verifyPayment(String orderId, String paymentId, String signature) {
        try {
            JSONObject attributes = new JSONObject();
            attributes.put("razorpay_order_id", orderId);
            attributes.put("razorpay_payment_id", paymentId);
            attributes.put("razorpay_signature", signature);

            return Utils.verifyPaymentSignature(attributes, keySecret);
        } catch (Exception e) {
            return false;
        }
    }
}
