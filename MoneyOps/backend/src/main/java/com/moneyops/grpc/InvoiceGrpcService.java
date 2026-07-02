package com.moneyops.grpc;

import com.moneyops.invoices.service.InvoiceService;
import com.moneyops.invoices.dto.InvoiceDto;
import com.moneyops.invoices.dto.InvoiceItemDto;
import com.moneyops.transactions.dto.TransactionDto;
import io.grpc.stub.StreamObserver;
import net.devh.boot.grpc.server.service.GrpcService;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.stream.Collectors;

@GrpcService
public class InvoiceGrpcService extends InvoiceServiceGrpc.InvoiceServiceImplBase {

    private final InvoiceService invoiceService;

    public InvoiceGrpcService(InvoiceService invoiceService) {
        this.invoiceService = invoiceService;
    }

    @Override
    public void getInvoices(GetInvoicesRequest request,
                            StreamObserver<GetInvoicesResponse> responseObserver) {
        try {
            java.util.List<InvoiceDto> invoices = invoiceService.getAllInvoices(request.getOrgId());

            java.util.List<Invoice> protoInvoices = invoices.stream()
                    .limit(request.getLimit() > 0 ? request.getLimit() : invoices.size())
                    .map(this::toProtoInvoice)
                    .collect(Collectors.toList());

            responseObserver.onNext(GetInvoicesResponse.newBuilder()
                    .setSuccess(true)
                    .addAllInvoices(protoInvoices)
                    .build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            responseObserver.onNext(GetInvoicesResponse.newBuilder()
                    .setSuccess(false)
                    .setError(ErrorResponse.newBuilder()
                            .setCode("INTERNAL")
                            .setMessage(e.getMessage()))
                    .build());
            responseObserver.onCompleted();
        }
    }

    @Override
    public void getInvoice(GetInvoiceRequest request,
                           StreamObserver<GetInvoiceResponse> responseObserver) {
        try {
            InvoiceDto invoice = invoiceService.getInvoiceById(request.getInvoiceId(), request.getOrgId());
            responseObserver.onNext(GetInvoiceResponse.newBuilder()
                    .setSuccess(true)
                    .setInvoice(toProtoInvoice(invoice))
                    .build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            responseObserver.onNext(GetInvoiceResponse.newBuilder()
                    .setSuccess(false)
                    .setError(ErrorResponse.newBuilder()
                            .setCode("NOT_FOUND")
                            .setMessage(e.getMessage()))
                    .build());
            responseObserver.onCompleted();
        }
    }

    @Override
    public void createInvoice(CreateInvoiceRequest request,
                              StreamObserver<CreateInvoiceResponse> responseObserver) {
        try {
            InvoiceDto dto = new InvoiceDto();
            dto.setClientId(request.getClientId());
            dto.setTotalAmount(BigDecimal.valueOf(request.getTotalAmount()));
            dto.setDueDate(LocalDate.parse(request.getDueDate()));
            dto.setNotes(request.getDescription());

            if (request.getItemsCount() > 0) {
                dto.setItems(request.getItemsList().stream()
                        .map(item -> {
                            InvoiceItemDto itemDto = new InvoiceItemDto();
                            itemDto.setDescription(item.getDescription());
                            itemDto.setQuantity((int) item.getQuantity());
                            itemDto.setRate(BigDecimal.valueOf(item.getUnitPrice()));
                            itemDto.setLineTotal(BigDecimal.valueOf(item.getAmount()));
                            return itemDto;
                        })
                        .collect(Collectors.toList()));
            }

            InvoiceDto created = invoiceService.createInvoice(dto, request.getOrgId(), "grpc");
            responseObserver.onNext(CreateInvoiceResponse.newBuilder()
                    .setSuccess(true)
                    .setInvoice(toProtoInvoice(created))
                    .build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            responseObserver.onNext(CreateInvoiceResponse.newBuilder()
                    .setSuccess(false)
                    .setError(ErrorResponse.newBuilder()
                            .setCode("INTERNAL")
                            .setMessage(e.getMessage()))
                    .build());
            responseObserver.onCompleted();
        }
    }

    @Override
    public void markPaid(MarkPaidRequest request,
                         StreamObserver<MarkPaidResponse> responseObserver) {
        try {
            TransactionDto paymentDto = new TransactionDto();
            paymentDto.setAmount(BigDecimal.valueOf(request.getAmount()));
            paymentDto.setDescription(request.getDescription());
            paymentDto.setTransactionDate(LocalDate.parse(request.getPaymentDate()));

            TransactionDto recorded = invoiceService.recordPayment(
                    request.getInvoiceId(), paymentDto, request.getOrgId(), "grpc");

            InvoiceDto invoice = invoiceService.getInvoiceById(request.getInvoiceId(), request.getOrgId());
            responseObserver.onNext(MarkPaidResponse.newBuilder()
                    .setSuccess(true)
                    .setInvoice(toProtoInvoice(invoice))
                    .build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            responseObserver.onNext(MarkPaidResponse.newBuilder()
                    .setSuccess(false)
                    .setError(ErrorResponse.newBuilder()
                            .setCode("INTERNAL")
                            .setMessage(e.getMessage()))
                    .build());
            responseObserver.onCompleted();
        }
    }

    private Invoice toProtoInvoice(InvoiceDto dto) {
        Invoice.Builder builder = Invoice.newBuilder()
                .setId(dto.getId())
                .setInvoiceNumber(dto.getInvoiceNumber() != null ? dto.getInvoiceNumber() : "")
                .setClientId(dto.getClientId() != null ? dto.getClientId() : "")
                .setTotalAmount(dto.getTotalAmount() != null ? dto.getTotalAmount().doubleValue() : 0.0)
                .setStatus(dto.getStatus() != null ? dto.getStatus() : "DRAFT")
                .setDueDate(dto.getDueDate() != null ? dto.getDueDate().toString() : "")
                .setDescription(dto.getNotes() != null ? dto.getNotes() : "");

        if (dto.getItems() != null) {
            dto.getItems().forEach(item -> builder.addItems(InvoiceItem.newBuilder()
                    .setDescription(item.getDescription() != null ? item.getDescription() : "")
                    .setQuantity(item.getQuantity() != null ? item.getQuantity().doubleValue() : 0.0)
                    .setUnitPrice(item.getRate() != null ? item.getRate().doubleValue() : 0.0)
                    .setAmount(item.getLineTotal() != null ? item.getLineTotal().doubleValue() : 0.0)
                    .build()));
        }

        return builder.build();
    }
}
