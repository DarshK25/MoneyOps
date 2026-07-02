package com.moneyops.grpc;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.62.2)",
    comments = "Source: moneyops.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class InvoiceServiceGrpc {

  private InvoiceServiceGrpc() {}

  public static final java.lang.String SERVICE_NAME = "moneyops.InvoiceService";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<com.moneyops.grpc.GetInvoicesRequest,
      com.moneyops.grpc.GetInvoicesResponse> getGetInvoicesMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetInvoices",
      requestType = com.moneyops.grpc.GetInvoicesRequest.class,
      responseType = com.moneyops.grpc.GetInvoicesResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.moneyops.grpc.GetInvoicesRequest,
      com.moneyops.grpc.GetInvoicesResponse> getGetInvoicesMethod() {
    io.grpc.MethodDescriptor<com.moneyops.grpc.GetInvoicesRequest, com.moneyops.grpc.GetInvoicesResponse> getGetInvoicesMethod;
    if ((getGetInvoicesMethod = InvoiceServiceGrpc.getGetInvoicesMethod) == null) {
      synchronized (InvoiceServiceGrpc.class) {
        if ((getGetInvoicesMethod = InvoiceServiceGrpc.getGetInvoicesMethod) == null) {
          InvoiceServiceGrpc.getGetInvoicesMethod = getGetInvoicesMethod =
              io.grpc.MethodDescriptor.<com.moneyops.grpc.GetInvoicesRequest, com.moneyops.grpc.GetInvoicesResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetInvoices"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.GetInvoicesRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.GetInvoicesResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InvoiceServiceMethodDescriptorSupplier("GetInvoices"))
              .build();
        }
      }
    }
    return getGetInvoicesMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.moneyops.grpc.GetInvoiceRequest,
      com.moneyops.grpc.GetInvoiceResponse> getGetInvoiceMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetInvoice",
      requestType = com.moneyops.grpc.GetInvoiceRequest.class,
      responseType = com.moneyops.grpc.GetInvoiceResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.moneyops.grpc.GetInvoiceRequest,
      com.moneyops.grpc.GetInvoiceResponse> getGetInvoiceMethod() {
    io.grpc.MethodDescriptor<com.moneyops.grpc.GetInvoiceRequest, com.moneyops.grpc.GetInvoiceResponse> getGetInvoiceMethod;
    if ((getGetInvoiceMethod = InvoiceServiceGrpc.getGetInvoiceMethod) == null) {
      synchronized (InvoiceServiceGrpc.class) {
        if ((getGetInvoiceMethod = InvoiceServiceGrpc.getGetInvoiceMethod) == null) {
          InvoiceServiceGrpc.getGetInvoiceMethod = getGetInvoiceMethod =
              io.grpc.MethodDescriptor.<com.moneyops.grpc.GetInvoiceRequest, com.moneyops.grpc.GetInvoiceResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetInvoice"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.GetInvoiceRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.GetInvoiceResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InvoiceServiceMethodDescriptorSupplier("GetInvoice"))
              .build();
        }
      }
    }
    return getGetInvoiceMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.moneyops.grpc.CreateInvoiceRequest,
      com.moneyops.grpc.CreateInvoiceResponse> getCreateInvoiceMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "CreateInvoice",
      requestType = com.moneyops.grpc.CreateInvoiceRequest.class,
      responseType = com.moneyops.grpc.CreateInvoiceResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.moneyops.grpc.CreateInvoiceRequest,
      com.moneyops.grpc.CreateInvoiceResponse> getCreateInvoiceMethod() {
    io.grpc.MethodDescriptor<com.moneyops.grpc.CreateInvoiceRequest, com.moneyops.grpc.CreateInvoiceResponse> getCreateInvoiceMethod;
    if ((getCreateInvoiceMethod = InvoiceServiceGrpc.getCreateInvoiceMethod) == null) {
      synchronized (InvoiceServiceGrpc.class) {
        if ((getCreateInvoiceMethod = InvoiceServiceGrpc.getCreateInvoiceMethod) == null) {
          InvoiceServiceGrpc.getCreateInvoiceMethod = getCreateInvoiceMethod =
              io.grpc.MethodDescriptor.<com.moneyops.grpc.CreateInvoiceRequest, com.moneyops.grpc.CreateInvoiceResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "CreateInvoice"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.CreateInvoiceRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.CreateInvoiceResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InvoiceServiceMethodDescriptorSupplier("CreateInvoice"))
              .build();
        }
      }
    }
    return getCreateInvoiceMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.moneyops.grpc.MarkPaidRequest,
      com.moneyops.grpc.MarkPaidResponse> getMarkPaidMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "MarkPaid",
      requestType = com.moneyops.grpc.MarkPaidRequest.class,
      responseType = com.moneyops.grpc.MarkPaidResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.moneyops.grpc.MarkPaidRequest,
      com.moneyops.grpc.MarkPaidResponse> getMarkPaidMethod() {
    io.grpc.MethodDescriptor<com.moneyops.grpc.MarkPaidRequest, com.moneyops.grpc.MarkPaidResponse> getMarkPaidMethod;
    if ((getMarkPaidMethod = InvoiceServiceGrpc.getMarkPaidMethod) == null) {
      synchronized (InvoiceServiceGrpc.class) {
        if ((getMarkPaidMethod = InvoiceServiceGrpc.getMarkPaidMethod) == null) {
          InvoiceServiceGrpc.getMarkPaidMethod = getMarkPaidMethod =
              io.grpc.MethodDescriptor.<com.moneyops.grpc.MarkPaidRequest, com.moneyops.grpc.MarkPaidResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "MarkPaid"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.MarkPaidRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.MarkPaidResponse.getDefaultInstance()))
              .setSchemaDescriptor(new InvoiceServiceMethodDescriptorSupplier("MarkPaid"))
              .build();
        }
      }
    }
    return getMarkPaidMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static InvoiceServiceStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<InvoiceServiceStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<InvoiceServiceStub>() {
        @java.lang.Override
        public InvoiceServiceStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new InvoiceServiceStub(channel, callOptions);
        }
      };
    return InvoiceServiceStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static InvoiceServiceBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<InvoiceServiceBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<InvoiceServiceBlockingStub>() {
        @java.lang.Override
        public InvoiceServiceBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new InvoiceServiceBlockingStub(channel, callOptions);
        }
      };
    return InvoiceServiceBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static InvoiceServiceFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<InvoiceServiceFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<InvoiceServiceFutureStub>() {
        @java.lang.Override
        public InvoiceServiceFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new InvoiceServiceFutureStub(channel, callOptions);
        }
      };
    return InvoiceServiceFutureStub.newStub(factory, channel);
  }

  /**
   */
  public interface AsyncService {

    /**
     */
    default void getInvoices(com.moneyops.grpc.GetInvoicesRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.GetInvoicesResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetInvoicesMethod(), responseObserver);
    }

    /**
     */
    default void getInvoice(com.moneyops.grpc.GetInvoiceRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.GetInvoiceResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetInvoiceMethod(), responseObserver);
    }

    /**
     */
    default void createInvoice(com.moneyops.grpc.CreateInvoiceRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.CreateInvoiceResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getCreateInvoiceMethod(), responseObserver);
    }

    /**
     */
    default void markPaid(com.moneyops.grpc.MarkPaidRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.MarkPaidResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getMarkPaidMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service InvoiceService.
   */
  public static abstract class InvoiceServiceImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return InvoiceServiceGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service InvoiceService.
   */
  public static final class InvoiceServiceStub
      extends io.grpc.stub.AbstractAsyncStub<InvoiceServiceStub> {
    private InvoiceServiceStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected InvoiceServiceStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new InvoiceServiceStub(channel, callOptions);
    }

    /**
     */
    public void getInvoices(com.moneyops.grpc.GetInvoicesRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.GetInvoicesResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetInvoicesMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void getInvoice(com.moneyops.grpc.GetInvoiceRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.GetInvoiceResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetInvoiceMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void createInvoice(com.moneyops.grpc.CreateInvoiceRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.CreateInvoiceResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getCreateInvoiceMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void markPaid(com.moneyops.grpc.MarkPaidRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.MarkPaidResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getMarkPaidMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service InvoiceService.
   */
  public static final class InvoiceServiceBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<InvoiceServiceBlockingStub> {
    private InvoiceServiceBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected InvoiceServiceBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new InvoiceServiceBlockingStub(channel, callOptions);
    }

    /**
     */
    public com.moneyops.grpc.GetInvoicesResponse getInvoices(com.moneyops.grpc.GetInvoicesRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetInvoicesMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.moneyops.grpc.GetInvoiceResponse getInvoice(com.moneyops.grpc.GetInvoiceRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetInvoiceMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.moneyops.grpc.CreateInvoiceResponse createInvoice(com.moneyops.grpc.CreateInvoiceRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getCreateInvoiceMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.moneyops.grpc.MarkPaidResponse markPaid(com.moneyops.grpc.MarkPaidRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getMarkPaidMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service InvoiceService.
   */
  public static final class InvoiceServiceFutureStub
      extends io.grpc.stub.AbstractFutureStub<InvoiceServiceFutureStub> {
    private InvoiceServiceFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected InvoiceServiceFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new InvoiceServiceFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.moneyops.grpc.GetInvoicesResponse> getInvoices(
        com.moneyops.grpc.GetInvoicesRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetInvoicesMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.moneyops.grpc.GetInvoiceResponse> getInvoice(
        com.moneyops.grpc.GetInvoiceRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetInvoiceMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.moneyops.grpc.CreateInvoiceResponse> createInvoice(
        com.moneyops.grpc.CreateInvoiceRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getCreateInvoiceMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.moneyops.grpc.MarkPaidResponse> markPaid(
        com.moneyops.grpc.MarkPaidRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getMarkPaidMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_GET_INVOICES = 0;
  private static final int METHODID_GET_INVOICE = 1;
  private static final int METHODID_CREATE_INVOICE = 2;
  private static final int METHODID_MARK_PAID = 3;

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
        case METHODID_GET_INVOICES:
          serviceImpl.getInvoices((com.moneyops.grpc.GetInvoicesRequest) request,
              (io.grpc.stub.StreamObserver<com.moneyops.grpc.GetInvoicesResponse>) responseObserver);
          break;
        case METHODID_GET_INVOICE:
          serviceImpl.getInvoice((com.moneyops.grpc.GetInvoiceRequest) request,
              (io.grpc.stub.StreamObserver<com.moneyops.grpc.GetInvoiceResponse>) responseObserver);
          break;
        case METHODID_CREATE_INVOICE:
          serviceImpl.createInvoice((com.moneyops.grpc.CreateInvoiceRequest) request,
              (io.grpc.stub.StreamObserver<com.moneyops.grpc.CreateInvoiceResponse>) responseObserver);
          break;
        case METHODID_MARK_PAID:
          serviceImpl.markPaid((com.moneyops.grpc.MarkPaidRequest) request,
              (io.grpc.stub.StreamObserver<com.moneyops.grpc.MarkPaidResponse>) responseObserver);
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
          getGetInvoicesMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.moneyops.grpc.GetInvoicesRequest,
              com.moneyops.grpc.GetInvoicesResponse>(
                service, METHODID_GET_INVOICES)))
        .addMethod(
          getGetInvoiceMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.moneyops.grpc.GetInvoiceRequest,
              com.moneyops.grpc.GetInvoiceResponse>(
                service, METHODID_GET_INVOICE)))
        .addMethod(
          getCreateInvoiceMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.moneyops.grpc.CreateInvoiceRequest,
              com.moneyops.grpc.CreateInvoiceResponse>(
                service, METHODID_CREATE_INVOICE)))
        .addMethod(
          getMarkPaidMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.moneyops.grpc.MarkPaidRequest,
              com.moneyops.grpc.MarkPaidResponse>(
                service, METHODID_MARK_PAID)))
        .build();
  }

  private static abstract class InvoiceServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    InvoiceServiceBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return com.moneyops.grpc.Moneyops.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("InvoiceService");
    }
  }

  private static final class InvoiceServiceFileDescriptorSupplier
      extends InvoiceServiceBaseDescriptorSupplier {
    InvoiceServiceFileDescriptorSupplier() {}
  }

  private static final class InvoiceServiceMethodDescriptorSupplier
      extends InvoiceServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final java.lang.String methodName;

    InvoiceServiceMethodDescriptorSupplier(java.lang.String methodName) {
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
      synchronized (InvoiceServiceGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new InvoiceServiceFileDescriptorSupplier())
              .addMethod(getGetInvoicesMethod())
              .addMethod(getGetInvoiceMethod())
              .addMethod(getCreateInvoiceMethod())
              .addMethod(getMarkPaidMethod())
              .build();
        }
      }
    }
    return result;
  }
}
