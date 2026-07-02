package com.moneyops.grpc;

import com.moneyops.intelligence.FinanceIntelligenceService;
import com.moneyops.transactions.service.TransactionService;
import com.moneyops.transactions.dto.TransactionDto;
import io.grpc.stub.StreamObserver;
import net.devh.boot.grpc.server.service.GrpcService;
import java.math.BigDecimal;
import java.util.Map;
import java.util.stream.Collectors;

@GrpcService
public class FinanceGrpcService extends FinanceServiceGrpc.FinanceServiceImplBase {

    private final FinanceIntelligenceService intelligenceService;
    private final TransactionService transactionService;

    public FinanceGrpcService(FinanceIntelligenceService intelligenceService,
                              TransactionService transactionService) {
        this.intelligenceService = intelligenceService;
        this.transactionService = transactionService;
    }

    @Override
    public void getFinanceMetrics(FinanceMetricsRequest request,
                                  StreamObserver<GetFinanceMetricsResponse> responseObserver) {
        try {
            Object metrics = intelligenceService.getMetrics(request.getBusinessId());

            FinanceMetrics.Builder builder = FinanceMetrics.newBuilder();
            if (metrics instanceof Map) {
                Map<String, Object> m = (Map<String, Object>) metrics;
                builder.setTotalRevenue(toDouble(m.get("revenue")))
                        .setTotalExpenses(toDouble(m.get("expenses")))
                        .setNetProfit(toDouble(m.get("netProfit")))
                        .setOutstandingInvoices(toInt(m.get("outstandingInvoices")))
                        .setOutstandingAmount(toDouble(m.get("outstandingAmount")));
            }

            responseObserver.onNext(GetFinanceMetricsResponse.newBuilder()
                    .setSuccess(true)
                    .setData(builder)
                    .build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            responseObserver.onNext(GetFinanceMetricsResponse.newBuilder()
                    .setSuccess(false)
                    .setError(ErrorResponse.newBuilder()
                            .setCode("INTERNAL")
                            .setMessage(e.getMessage()))
                    .build());
            responseObserver.onCompleted();
        }
    }

    @Override
    public void getFinancialSummary(FinancialSummaryRequest request,
                                    StreamObserver<GetFinancialSummaryResponse> responseObserver) {
        try {
            BigDecimal totalIncome = transactionService.getTotalIncome(request.getOrgId());
            BigDecimal totalExpense = transactionService.getTotalExpense(request.getOrgId());
            java.util.List<TransactionDto> recent = transactionService.getTransactions(
                    request.getOrgId(), null, null, 10);

            FinancialSummary.Builder summary = FinancialSummary.newBuilder()
                    .setTotalIncome(totalIncome != null ? totalIncome.doubleValue() : 0.0)
                    .setTotalExpense(totalExpense != null ? totalExpense.doubleValue() : 0.0);

            recent.forEach(tx -> summary.addRecentTransactions(Transaction.newBuilder()
                    .setId(tx.getId())
                    .setType(tx.getType() != null ? tx.getType() : "")
                    .setAmount(tx.getAmount() != null ? tx.getAmount().doubleValue() : 0.0)
                    .setDescription(tx.getDescription() != null ? tx.getDescription() : "")
                    .setDate(tx.getTransactionDate() != null ? tx.getTransactionDate().toString() : "")
                    .setCategory(tx.getCategory() != null ? tx.getCategory() : "")
                    .build()));

            responseObserver.onNext(GetFinancialSummaryResponse.newBuilder()
                    .setSuccess(true)
                    .setData(summary)
                    .build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            responseObserver.onNext(GetFinancialSummaryResponse.newBuilder()
                    .setSuccess(false)
                    .setError(ErrorResponse.newBuilder()
                            .setCode("INTERNAL")
                            .setMessage(e.getMessage()))
                    .build());
            responseObserver.onCompleted();
        }
    }

    private double toDouble(Object val) {
        if (val instanceof Number) return ((Number) val).doubleValue();
        if (val instanceof BigDecimal) return ((BigDecimal) val).doubleValue();
        return 0.0;
    }

    private int toInt(Object val) {
        if (val instanceof Number) return ((Number) val).intValue();
        return 0;
    }
}
