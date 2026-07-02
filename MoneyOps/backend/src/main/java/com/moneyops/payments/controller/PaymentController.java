package com.moneyops.payments.controller;

import com.moneyops.invoices.entity.Invoice;
import com.moneyops.invoices.repository.InvoiceRepository;
import com.moneyops.payments.dto.CreateOrderRequest;
import com.moneyops.payments.dto.RazorpayOrderResponse;
import com.moneyops.payments.service.RazorpayService;
import com.moneyops.shared.utils.OrgContext;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/payments")
@RequiredArgsConstructor
public class PaymentController {

    private final RazorpayService razorpayService;
    private final InvoiceRepository invoiceRepository;

    @PostMapping("/create-order")
    public ResponseEntity<RazorpayOrderResponse> createOrder(@RequestBody CreateOrderRequest request) {
        try {
            RazorpayOrderResponse order = razorpayService.createOrder(request);
            return ResponseEntity.ok(order);
        } catch (Exception e) {
            return ResponseEntity.status(500).body(null);
        }
    }

    @PostMapping("/verify")
    public ResponseEntity<Boolean> verifyPayment(
            @RequestParam String orderId,
            @RequestParam String paymentId,
            @RequestParam String signature) {
        boolean valid = razorpayService.verifyPayment(orderId, paymentId, signature);
        return ResponseEntity.ok(valid);
    }

    @PostMapping("/invoices/{id}/pay-via-razorpay")
    public ResponseEntity<RazorpayOrderResponse> payInvoiceViaRazorpay(@PathVariable String id) {
        try {
            String orgId = OrgContext.getOrgId();
            Invoice invoice = invoiceRepository.findByIdAndOrgIdAndDeletedAtIsNull(id, orgId)
                    .orElseThrow(() -> new RuntimeException("Invoice not found"));

            CreateOrderRequest orderRequest = new CreateOrderRequest();
            orderRequest.setAmount(invoice.getTotalAmount().doubleValue());
            orderRequest.setCurrency("INR");
            orderRequest.setReceipt("inv_" + id);

            RazorpayOrderResponse order = razorpayService.createOrder(orderRequest);
            return ResponseEntity.ok(order);
        } catch (Exception e) {
            return ResponseEntity.status(500).body(null);
        }
    }
}
