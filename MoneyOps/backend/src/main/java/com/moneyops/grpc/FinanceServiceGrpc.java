package com.moneyops.grpc;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.62.2)",
    comments = "Source: moneyops.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class FinanceServiceGrpc {

  private FinanceServiceGrpc() {}

  public static final java.lang.String SERVICE_NAME = "moneyops.FinanceService";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<com.moneyops.grpc.FinanceMetricsRequest,
      com.moneyops.grpc.GetFinanceMetricsResponse> getGetFinanceMetricsMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetFinanceMetrics",
      requestType = com.moneyops.grpc.FinanceMetricsRequest.class,
      responseType = com.moneyops.grpc.GetFinanceMetricsResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.moneyops.grpc.FinanceMetricsRequest,
      com.moneyops.grpc.GetFinanceMetricsResponse> getGetFinanceMetricsMethod() {
    io.grpc.MethodDescriptor<com.moneyops.grpc.FinanceMetricsRequest, com.moneyops.grpc.GetFinanceMetricsResponse> getGetFinanceMetricsMethod;
    if ((getGetFinanceMetricsMethod = FinanceServiceGrpc.getGetFinanceMetricsMethod) == null) {
      synchronized (FinanceServiceGrpc.class) {
        if ((getGetFinanceMetricsMethod = FinanceServiceGrpc.getGetFinanceMetricsMethod) == null) {
          FinanceServiceGrpc.getGetFinanceMetricsMethod = getGetFinanceMetricsMethod =
              io.grpc.MethodDescriptor.<com.moneyops.grpc.FinanceMetricsRequest, com.moneyops.grpc.GetFinanceMetricsResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetFinanceMetrics"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.FinanceMetricsRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.GetFinanceMetricsResponse.getDefaultInstance()))
              .setSchemaDescriptor(new FinanceServiceMethodDescriptorSupplier("GetFinanceMetrics"))
              .build();
        }
      }
    }
    return getGetFinanceMetricsMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.moneyops.grpc.FinancialSummaryRequest,
      com.moneyops.grpc.GetFinancialSummaryResponse> getGetFinancialSummaryMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetFinancialSummary",
      requestType = com.moneyops.grpc.FinancialSummaryRequest.class,
      responseType = com.moneyops.grpc.GetFinancialSummaryResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.moneyops.grpc.FinancialSummaryRequest,
      com.moneyops.grpc.GetFinancialSummaryResponse> getGetFinancialSummaryMethod() {
    io.grpc.MethodDescriptor<com.moneyops.grpc.FinancialSummaryRequest, com.moneyops.grpc.GetFinancialSummaryResponse> getGetFinancialSummaryMethod;
    if ((getGetFinancialSummaryMethod = FinanceServiceGrpc.getGetFinancialSummaryMethod) == null) {
      synchronized (FinanceServiceGrpc.class) {
        if ((getGetFinancialSummaryMethod = FinanceServiceGrpc.getGetFinancialSummaryMethod) == null) {
          FinanceServiceGrpc.getGetFinancialSummaryMethod = getGetFinancialSummaryMethod =
              io.grpc.MethodDescriptor.<com.moneyops.grpc.FinancialSummaryRequest, com.moneyops.grpc.GetFinancialSummaryResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetFinancialSummary"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.FinancialSummaryRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.GetFinancialSummaryResponse.getDefaultInstance()))
              .setSchemaDescriptor(new FinanceServiceMethodDescriptorSupplier("GetFinancialSummary"))
              .build();
        }
      }
    }
    return getGetFinancialSummaryMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static FinanceServiceStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<FinanceServiceStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<FinanceServiceStub>() {
        @java.lang.Override
        public FinanceServiceStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new FinanceServiceStub(channel, callOptions);
        }
      };
    return FinanceServiceStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static FinanceServiceBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<FinanceServiceBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<FinanceServiceBlockingStub>() {
        @java.lang.Override
        public FinanceServiceBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new FinanceServiceBlockingStub(channel, callOptions);
        }
      };
    return FinanceServiceBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static FinanceServiceFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<FinanceServiceFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<FinanceServiceFutureStub>() {
        @java.lang.Override
        public FinanceServiceFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new FinanceServiceFutureStub(channel, callOptions);
        }
      };
    return FinanceServiceFutureStub.newStub(factory, channel);
  }

  /**
   */
  public interface AsyncService {

    /**
     */
    default void getFinanceMetrics(com.moneyops.grpc.FinanceMetricsRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.GetFinanceMetricsResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetFinanceMetricsMethod(), responseObserver);
    }

    /**
     */
    default void getFinancialSummary(com.moneyops.grpc.FinancialSummaryRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.GetFinancialSummaryResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetFinancialSummaryMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service FinanceService.
   */
  public static abstract class FinanceServiceImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return FinanceServiceGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service FinanceService.
   */
  public static final class FinanceServiceStub
      extends io.grpc.stub.AbstractAsyncStub<FinanceServiceStub> {
    private FinanceServiceStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected FinanceServiceStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new FinanceServiceStub(channel, callOptions);
    }

    /**
     */
    public void getFinanceMetrics(com.moneyops.grpc.FinanceMetricsRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.GetFinanceMetricsResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetFinanceMetricsMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void getFinancialSummary(com.moneyops.grpc.FinancialSummaryRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.GetFinancialSummaryResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetFinancialSummaryMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service FinanceService.
   */
  public static final class FinanceServiceBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<FinanceServiceBlockingStub> {
    private FinanceServiceBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected FinanceServiceBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new FinanceServiceBlockingStub(channel, callOptions);
    }

    /**
     */
    public com.moneyops.grpc.GetFinanceMetricsResponse getFinanceMetrics(com.moneyops.grpc.FinanceMetricsRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetFinanceMetricsMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.moneyops.grpc.GetFinancialSummaryResponse getFinancialSummary(com.moneyops.grpc.FinancialSummaryRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetFinancialSummaryMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service FinanceService.
   */
  public static final class FinanceServiceFutureStub
      extends io.grpc.stub.AbstractFutureStub<FinanceServiceFutureStub> {
    private FinanceServiceFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected FinanceServiceFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new FinanceServiceFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.moneyops.grpc.GetFinanceMetricsResponse> getFinanceMetrics(
        com.moneyops.grpc.FinanceMetricsRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetFinanceMetricsMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.moneyops.grpc.GetFinancialSummaryResponse> getFinancialSummary(
        com.moneyops.grpc.FinancialSummaryRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetFinancialSummaryMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_GET_FINANCE_METRICS = 0;
  private static final int METHODID_GET_FINANCIAL_SUMMARY = 1;

  private static final class MethodHandlers<Req, Resp> implements
      io.grpc.stub.ServerCalls.UnaryMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ServerStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ClientStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.BidiStreamingMethod<Req, Resp> {
    private final AsyncService serviceImpl;
    private final int methodId;

    MethodHandlers(AsyncService serviceImpl, int methodId) {
      this.serviceImpl = serviceImpl;
      this.methodId = methodId;
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public void invoke(Req request, io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        case METHODID_GET_FINANCE_METRICS:
          serviceImpl.getFinanceMetrics((com.moneyops.grpc.FinanceMetricsRequest) request,
              (io.grpc.stub.StreamObserver<com.moneyops.grpc.GetFinanceMetricsResponse>) responseObserver);
          break;
        case METHODID_GET_FINANCIAL_SUMMARY:
          serviceImpl.getFinancialSummary((com.moneyops.grpc.FinancialSummaryRequest) request,
              (io.grpc.stub.StreamObserver<com.moneyops.grpc.GetFinancialSummaryResponse>) responseObserver);
          break;
        default:
          throw new AssertionError();
      }
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public io.grpc.stub.StreamObserver<Req> invoke(
        io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        default:
          throw new AssertionError();
      }
    }
  }

  public static final io.grpc.ServerServiceDefinition bindService(AsyncService service) {
    return io.grpc.ServerServiceDefinition.builder(getServiceDescriptor())
        .addMethod(
          getGetFinanceMetricsMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.moneyops.grpc.FinanceMetricsRequest,
              com.moneyops.grpc.GetFinanceMetricsResponse>(
                service, METHODID_GET_FINANCE_METRICS)))
        .addMethod(
          getGetFinancialSummaryMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.moneyops.grpc.FinancialSummaryRequest,
              com.moneyops.grpc.GetFinancialSummaryResponse>(
                service, METHODID_GET_FINANCIAL_SUMMARY)))
        .build();
  }

  private static abstract class FinanceServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    FinanceServiceBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return com.moneyops.grpc.Moneyops.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("FinanceService");
    }
  }

  private static final class FinanceServiceFileDescriptorSupplier
      extends FinanceServiceBaseDescriptorSupplier {
    FinanceServiceFileDescriptorSupplier() {}
  }

  private static final class FinanceServiceMethodDescriptorSupplier
      extends FinanceServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final java.lang.String methodName;

    FinanceServiceMethodDescriptorSupplier(java.lang.String methodName) {
      this.methodName = methodName;
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.MethodDescriptor getMethodDescriptor() {
      return getServiceDescriptor().findMethodByName(methodName);
    }
  }

  private static volatile io.grpc.ServiceDescriptor serviceDescriptor;

  public static io.grpc.ServiceDescriptor getServiceDescriptor() {
    io.grpc.ServiceDescriptor result = serviceDescriptor;
    if (result == null) {
      synchronized (FinanceServiceGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new FinanceServiceFileDescriptorSupplier())
              .addMethod(getGetFinanceMetricsMethod())
              .addMethod(getGetFinancialSummaryMethod())
              .build();
        }
      }
    }
    return result;
  }
}
