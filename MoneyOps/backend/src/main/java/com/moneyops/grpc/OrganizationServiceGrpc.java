package com.moneyops.grpc;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.62.2)",
    comments = "Source: moneyops.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class OrganizationServiceGrpc {

  private OrganizationServiceGrpc() {}

  public static final java.lang.String SERVICE_NAME = "moneyops.OrganizationService";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<com.moneyops.grpc.UserIdRequest,
      com.moneyops.grpc.GetOnboardingStatusResponse> getGetOnboardingStatusMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetOnboardingStatus",
      requestType = com.moneyops.grpc.UserIdRequest.class,
      responseType = com.moneyops.grpc.GetOnboardingStatusResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.moneyops.grpc.UserIdRequest,
      com.moneyops.grpc.GetOnboardingStatusResponse> getGetOnboardingStatusMethod() {
    io.grpc.MethodDescriptor<com.moneyops.grpc.UserIdRequest, com.moneyops.grpc.GetOnboardingStatusResponse> getGetOnboardingStatusMethod;
    if ((getGetOnboardingStatusMethod = OrganizationServiceGrpc.getGetOnboardingStatusMethod) == null) {
      synchronized (OrganizationServiceGrpc.class) {
        if ((getGetOnboardingStatusMethod = OrganizationServiceGrpc.getGetOnboardingStatusMethod) == null) {
          OrganizationServiceGrpc.getGetOnboardingStatusMethod = getGetOnboardingStatusMethod =
              io.grpc.MethodDescriptor.<com.moneyops.grpc.UserIdRequest, com.moneyops.grpc.GetOnboardingStatusResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetOnboardingStatus"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.UserIdRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.GetOnboardingStatusResponse.getDefaultInstance()))
              .setSchemaDescriptor(new OrganizationServiceMethodDescriptorSupplier("GetOnboardingStatus"))
              .build();
        }
      }
    }
    return getGetOnboardingStatusMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.moneyops.grpc.OrgIdRequest,
      com.moneyops.grpc.GetOrganizationResponse> getGetOrganizationMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetOrganization",
      requestType = com.moneyops.grpc.OrgIdRequest.class,
      responseType = com.moneyops.grpc.GetOrganizationResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.moneyops.grpc.OrgIdRequest,
      com.moneyops.grpc.GetOrganizationResponse> getGetOrganizationMethod() {
    io.grpc.MethodDescriptor<com.moneyops.grpc.OrgIdRequest, com.moneyops.grpc.GetOrganizationResponse> getGetOrganizationMethod;
    if ((getGetOrganizationMethod = OrganizationServiceGrpc.getGetOrganizationMethod) == null) {
      synchronized (OrganizationServiceGrpc.class) {
        if ((getGetOrganizationMethod = OrganizationServiceGrpc.getGetOrganizationMethod) == null) {
          OrganizationServiceGrpc.getGetOrganizationMethod = getGetOrganizationMethod =
              io.grpc.MethodDescriptor.<com.moneyops.grpc.OrgIdRequest, com.moneyops.grpc.GetOrganizationResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetOrganization"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.OrgIdRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.GetOrganizationResponse.getDefaultInstance()))
              .setSchemaDescriptor(new OrganizationServiceMethodDescriptorSupplier("GetOrganization"))
              .build();
        }
      }
    }
    return getGetOrganizationMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static OrganizationServiceStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<OrganizationServiceStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<OrganizationServiceStub>() {
        @java.lang.Override
        public OrganizationServiceStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new OrganizationServiceStub(channel, callOptions);
        }
      };
    return OrganizationServiceStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static OrganizationServiceBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<OrganizationServiceBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<OrganizationServiceBlockingStub>() {
        @java.lang.Override
        public OrganizationServiceBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new OrganizationServiceBlockingStub(channel, callOptions);
        }
      };
    return OrganizationServiceBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static OrganizationServiceFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<OrganizationServiceFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<OrganizationServiceFutureStub>() {
        @java.lang.Override
        public OrganizationServiceFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new OrganizationServiceFutureStub(channel, callOptions);
        }
      };
    return OrganizationServiceFutureStub.newStub(factory, channel);
  }

  /**
   */
  public interface AsyncService {

    /**
     */
    default void getOnboardingStatus(com.moneyops.grpc.UserIdRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.GetOnboardingStatusResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetOnboardingStatusMethod(), responseObserver);
    }

    /**
     */
    default void getOrganization(com.moneyops.grpc.OrgIdRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.GetOrganizationResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetOrganizationMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service OrganizationService.
   */
  public static abstract class OrganizationServiceImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return OrganizationServiceGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service OrganizationService.
   */
  public static final class OrganizationServiceStub
      extends io.grpc.stub.AbstractAsyncStub<OrganizationServiceStub> {
    private OrganizationServiceStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected OrganizationServiceStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new OrganizationServiceStub(channel, callOptions);
    }

    /**
     */
    public void getOnboardingStatus(com.moneyops.grpc.UserIdRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.GetOnboardingStatusResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetOnboardingStatusMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void getOrganization(com.moneyops.grpc.OrgIdRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.GetOrganizationResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetOrganizationMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service OrganizationService.
   */
  public static final class OrganizationServiceBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<OrganizationServiceBlockingStub> {
    private OrganizationServiceBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected OrganizationServiceBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new OrganizationServiceBlockingStub(channel, callOptions);
    }

    /**
     */
    public com.moneyops.grpc.GetOnboardingStatusResponse getOnboardingStatus(com.moneyops.grpc.UserIdRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetOnboardingStatusMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.moneyops.grpc.GetOrganizationResponse getOrganization(com.moneyops.grpc.OrgIdRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetOrganizationMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service OrganizationService.
   */
  public static final class OrganizationServiceFutureStub
      extends io.grpc.stub.AbstractFutureStub<OrganizationServiceFutureStub> {
    private OrganizationServiceFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected OrganizationServiceFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new OrganizationServiceFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.moneyops.grpc.GetOnboardingStatusResponse> getOnboardingStatus(
        com.moneyops.grpc.UserIdRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetOnboardingStatusMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.moneyops.grpc.GetOrganizationResponse> getOrganization(
        com.moneyops.grpc.OrgIdRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetOrganizationMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_GET_ONBOARDING_STATUS = 0;
  private static final int METHODID_GET_ORGANIZATION = 1;

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
        case METHODID_GET_ONBOARDING_STATUS:
          serviceImpl.getOnboardingStatus((com.moneyops.grpc.UserIdRequest) request,
              (io.grpc.stub.StreamObserver<com.moneyops.grpc.GetOnboardingStatusResponse>) responseObserver);
          break;
        case METHODID_GET_ORGANIZATION:
          serviceImpl.getOrganization((com.moneyops.grpc.OrgIdRequest) request,
              (io.grpc.stub.StreamObserver<com.moneyops.grpc.GetOrganizationResponse>) responseObserver);
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
          getGetOnboardingStatusMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.moneyops.grpc.UserIdRequest,
              com.moneyops.grpc.GetOnboardingStatusResponse>(
                service, METHODID_GET_ONBOARDING_STATUS)))
        .addMethod(
          getGetOrganizationMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.moneyops.grpc.OrgIdRequest,
              com.moneyops.grpc.GetOrganizationResponse>(
                service, METHODID_GET_ORGANIZATION)))
        .build();
  }

  private static abstract class OrganizationServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    OrganizationServiceBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return com.moneyops.grpc.Moneyops.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("OrganizationService");
    }
  }

  private static final class OrganizationServiceFileDescriptorSupplier
      extends OrganizationServiceBaseDescriptorSupplier {
    OrganizationServiceFileDescriptorSupplier() {}
  }

  private static final class OrganizationServiceMethodDescriptorSupplier
      extends OrganizationServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final java.lang.String methodName;

    OrganizationServiceMethodDescriptorSupplier(java.lang.String methodName) {
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
      synchronized (OrganizationServiceGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new OrganizationServiceFileDescriptorSupplier())
              .addMethod(getGetOnboardingStatusMethod())
              .addMethod(getGetOrganizationMethod())
              .build();
        }
      }
    }
    return result;
  }
}
