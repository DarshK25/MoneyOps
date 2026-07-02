package com.moneyops.grpc;

import com.moneyops.clients.service.ClientService;
import com.moneyops.clients.dto.ClientDto;
import io.grpc.stub.StreamObserver;
import net.devh.boot.grpc.server.service.GrpcService;
import java.util.List;
import java.util.stream.Collectors;

@GrpcService
public class ClientGrpcService extends ClientServiceGrpc.ClientServiceImplBase {

    private final ClientService clientService;

    public ClientGrpcService(ClientService clientService) {
        this.clientService = clientService;
    }

    @Override
    public void getClients(GetClientsRequest request,
                           StreamObserver<GetClientsResponse> responseObserver) {
        try {
            List<ClientDto> clients = clientService.getAllClients(request.getOrgId());
            int limit = request.getLimit() > 0 ? request.getLimit() : clients.size();

            List<Client> protoClients = clients.stream()
                    .limit(limit)
                    .map(c -> Client.newBuilder()
                            .setId(c.getId())
                            .setDisplayName(c.getName() != null ? c.getName() : "")
                            .setEmail(c.getEmail() != null ? c.getEmail() : "")
                            .setStatus(c.getStatus() != null ? c.getStatus() : "active")
                            .setOrgId(request.getOrgId())
                            .build())
                    .collect(Collectors.toList());

            responseObserver.onNext(GetClientsResponse.newBuilder()
                    .setSuccess(true)
                    .addAllClients(protoClients)
                    .build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            responseObserver.onNext(GetClientsResponse.newBuilder()
                    .setSuccess(false)
                    .setError(ErrorResponse.newBuilder()
                            .setCode("INTERNAL")
                            .setMessage(e.getMessage()))
                    .build());
            responseObserver.onCompleted();
        }
    }

    @Override
    public void createClient(CreateClientRequest request,
                             StreamObserver<CreateClientResponse> responseObserver) {
        try {
            ClientDto dto = new ClientDto();
            dto.setName(request.getName());
            dto.setEmail(request.getEmail());
            dto.setPhoneNumber(request.getPhone());
            dto.setGstin(request.getGstNumber());

            ClientDto created = clientService.createClient(dto, request.getOrgId(), "grpc");

            Client protoClient = Client.newBuilder()
                    .setId(created.getId())
                    .setDisplayName(created.getName())
                    .setEmail(created.getEmail() != null ? created.getEmail() : "")
                    .setStatus("active")
                    .setOrgId(request.getOrgId())
                    .build();

            responseObserver.onNext(CreateClientResponse.newBuilder()
                    .setSuccess(true)
                    .setClient(protoClient)
                    .build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            responseObserver.onNext(CreateClientResponse.newBuilder()
                    .setSuccess(false)
                    .setError(ErrorResponse.newBuilder()
                            .setCode("INTERNAL")
                            .setMessage(e.getMessage()))
                    .build());
            responseObserver.onCompleted();
        }
    }
}
