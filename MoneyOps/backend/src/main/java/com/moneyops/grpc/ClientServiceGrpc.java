package com.moneyops.grpc;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.62.2)",
    comments = "Source: moneyops.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class ClientServiceGrpc {

  private ClientServiceGrpc() {}

  public static final java.lang.String SERVICE_NAME = "moneyops.ClientService";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<com.moneyops.grpc.GetClientsRequest,
      com.moneyops.grpc.GetClientsResponse> getGetClientsMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetClients",
      requestType = com.moneyops.grpc.GetClientsRequest.class,
      responseType = com.moneyops.grpc.GetClientsResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.moneyops.grpc.GetClientsRequest,
      com.moneyops.grpc.GetClientsResponse> getGetClientsMethod() {
    io.grpc.MethodDescriptor<com.moneyops.grpc.GetClientsRequest, com.moneyops.grpc.GetClientsResponse> getGetClientsMethod;
    if ((getGetClientsMethod = ClientServiceGrpc.getGetClientsMethod) == null) {
      synchronized (ClientServiceGrpc.class) {
        if ((getGetClientsMethod = ClientServiceGrpc.getGetClientsMethod) == null) {
          ClientServiceGrpc.getGetClientsMethod = getGetClientsMethod =
              io.grpc.MethodDescriptor.<com.moneyops.grpc.GetClientsRequest, com.moneyops.grpc.GetClientsResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetClients"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.GetClientsRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.GetClientsResponse.getDefaultInstance()))
              .setSchemaDescriptor(new ClientServiceMethodDescriptorSupplier("GetClients"))
              .build();
        }
      }
    }
    return getGetClientsMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.moneyops.grpc.CreateClientRequest,
      com.moneyops.grpc.CreateClientResponse> getCreateClientMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "CreateClient",
      requestType = com.moneyops.grpc.CreateClientRequest.class,
      responseType = com.moneyops.grpc.CreateClientResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.moneyops.grpc.CreateClientRequest,
      com.moneyops.grpc.CreateClientResponse> getCreateClientMethod() {
    io.grpc.MethodDescriptor<com.moneyops.grpc.CreateClientRequest, com.moneyops.grpc.CreateClientResponse> getCreateClientMethod;
    if ((getCreateClientMethod = ClientServiceGrpc.getCreateClientMethod) == null) {
      synchronized (ClientServiceGrpc.class) {
        if ((getCreateClientMethod = ClientServiceGrpc.getCreateClientMethod) == null) {
          ClientServiceGrpc.getCreateClientMethod = getCreateClientMethod =
              io.grpc.MethodDescriptor.<com.moneyops.grpc.CreateClientRequest, com.moneyops.grpc.CreateClientResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "CreateClient"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.CreateClientRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.moneyops.grpc.CreateClientResponse.getDefaultInstance()))
              .setSchemaDescriptor(new ClientServiceMethodDescriptorSupplier("CreateClient"))
              .build();
        }
      }
    }
    return getCreateClientMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static ClientServiceStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<ClientServiceStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<ClientServiceStub>() {
        @java.lang.Override
        public ClientServiceStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new ClientServiceStub(channel, callOptions);
        }
      };
    return ClientServiceStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static ClientServiceBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<ClientServiceBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<ClientServiceBlockingStub>() {
        @java.lang.Override
        public ClientServiceBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new ClientServiceBlockingStub(channel, callOptions);
        }
      };
    return ClientServiceBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static ClientServiceFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<ClientServiceFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<ClientServiceFutureStub>() {
        @java.lang.Override
        public ClientServiceFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new ClientServiceFutureStub(channel, callOptions);
        }
      };
    return ClientServiceFutureStub.newStub(factory, channel);
  }

  /**
   */
  public interface AsyncService {

    /**
     */
    default void getClients(com.moneyops.grpc.GetClientsRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.GetClientsResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetClientsMethod(), responseObserver);
    }

    /**
     */
    default void createClient(com.moneyops.grpc.CreateClientRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.CreateClientResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getCreateClientMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service ClientService.
   */
  public static abstract class ClientServiceImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return ClientServiceGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service ClientService.
   */
  public static final class ClientServiceStub
      extends io.grpc.stub.AbstractAsyncStub<ClientServiceStub> {
    private ClientServiceStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected ClientServiceStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new ClientServiceStub(channel, callOptions);
    }

    /**
     */
    public void getClients(com.moneyops.grpc.GetClientsRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.GetClientsResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetClientsMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void createClient(com.moneyops.grpc.CreateClientRequest request,
        io.grpc.stub.StreamObserver<com.moneyops.grpc.CreateClientResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getCreateClientMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service ClientService.
   */
  public static final class ClientServiceBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<ClientServiceBlockingStub> {
    private ClientServiceBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected ClientServiceBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new ClientServiceBlockingStub(channel, callOptions);
    }

    /**
     */
    public com.moneyops.grpc.GetClientsResponse getClients(com.moneyops.grpc.GetClientsRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetClientsMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.moneyops.grpc.CreateClientResponse createClient(com.moneyops.grpc.CreateClientRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getCreateClientMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service ClientService.
   */
  public static final class ClientServiceFutureStub
      extends io.grpc.stub.AbstractFutureStub<ClientServiceFutureStub> {
    private ClientServiceFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected ClientServiceFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new ClientServiceFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.moneyops.grpc.GetClientsResponse> getClients(
        com.moneyops.grpc.GetClientsRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetClientsMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.moneyops.grpc.CreateClientResponse> createClient(
        com.moneyops.grpc.CreateClientRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getCreateClientMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_GET_CLIENTS = 0;
  private static final int METHODID_CREATE_CLIENT = 1;

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
        case METHODID_GET_CLIENTS:
          serviceImpl.getClients((com.moneyops.grpc.GetClientsRequest) request,
              (io.grpc.stub.StreamObserver<com.moneyops.grpc.GetClientsResponse>) responseObserver);
          break;
        case METHODID_CREATE_CLIENT:
          serviceImpl.createClient((com.moneyops.grpc.CreateClientRequest) request,
              (io.grpc.stub.StreamObserver<com.moneyops.grpc.CreateClientResponse>) responseObserver);
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
          getGetClientsMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.moneyops.grpc.GetClientsRequest,
              com.moneyops.grpc.GetClientsResponse>(
                service, METHODID_GET_CLIENTS)))
        .addMethod(
          getCreateClientMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.moneyops.grpc.CreateClientRequest,
              com.moneyops.grpc.CreateClientResponse>(
                service, METHODID_CREATE_CLIENT)))
        .build();
  }

  private static abstract class ClientServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    ClientServiceBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return com.moneyops.grpc.Moneyops.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("ClientService");
    }
  }

  private static final class ClientServiceFileDescriptorSupplier
      extends ClientServiceBaseDescriptorSupplier {
    ClientServiceFileDescriptorSupplier() {}
  }

  private static final class ClientServiceMethodDescriptorSupplier
      extends ClientServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final java.lang.String methodName;

    ClientServiceMethodDescriptorSupplier(java.lang.String methodName) {
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
      synchronized (ClientServiceGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new ClientServiceFileDescriptorSupplier())
              .addMethod(getGetClientsMethod())
              .addMethod(getCreateClientMethod())
              .build();
        }
      }
    }
    return result;
  }
}
