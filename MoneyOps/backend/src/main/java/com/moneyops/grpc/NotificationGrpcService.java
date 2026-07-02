package com.moneyops.grpc;

import com.moneyops.email.EmailService;
import io.grpc.stub.StreamObserver;
import net.devh.boot.grpc.server.service.GrpcService;

@GrpcService
public class NotificationGrpcService extends NotificationServiceGrpc.NotificationServiceImplBase {

    private final EmailService emailService;

    public NotificationGrpcService(EmailService emailService) {
        this.emailService = emailService;
    }

    @Override
    public void sendCollectionEmail(SendCollectionEmailRequest request,
                                    StreamObserver<SendCollectionEmailResponse> responseObserver) {
        try {
            String subject = "Payment Reminder: Invoice " + request.getInvoiceNumber();
            String htmlContent = String.format(
                    "<p>Dear %s,</p><p>This is a reminder for Invoice %s of Rs.%.2f due on %s.</p>",
                    request.getClientName(), request.getInvoiceNumber(),
                    request.getAmount(), request.getDueDate());

            emailService.sendInvoiceFollowUp(
                    request.getClientEmail(),
                    request.getInvoiceNumber(),
                    request.getClientName(),
                    "MoneyOps",
                    request.getDueDate(),
                    String.format("%.2f", request.getAmount()));

            responseObserver.onNext(SendCollectionEmailResponse.newBuilder()
                    .setSuccess(true)
                    .setSent(true)
                    .setRecipient(request.getClientEmail())
                    .build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            responseObserver.onNext(SendCollectionEmailResponse.newBuilder()
                    .setSuccess(false)
                    .setSent(false)
                    .setError(ErrorResponse.newBuilder()
                            .setCode("EMAIL_FAILED")
                            .setMessage(e.getMessage()))
                    .build());
            responseObserver.onCompleted();
        }
    }
}
