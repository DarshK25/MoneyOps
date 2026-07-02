package com.moneyops.grpc;

import com.moneyops.onboarding.service.OnboardingService;
import com.moneyops.onboarding.dto.OnboardingStatusResponse;
import com.moneyops.organizations.service.OrganizationService;
import com.moneyops.organizations.dto.BusinessOrganizationDto;
import io.grpc.stub.StreamObserver;
import net.devh.boot.grpc.server.service.GrpcService;

@GrpcService
public class OrganizationGrpcService extends OrganizationServiceGrpc.OrganizationServiceImplBase {

    private final OnboardingService onboardingService;
    private final OrganizationService organizationService;

    public OrganizationGrpcService(OnboardingService onboardingService,
                                   OrganizationService organizationService) {
        this.onboardingService = onboardingService;
        this.organizationService = organizationService;
    }

    @Override
    public void getOnboardingStatus(UserIdRequest request,
                                    StreamObserver<GetOnboardingStatusResponse> responseObserver) {
        try {
            OnboardingStatusResponse status = onboardingService.getStatus(request.getUserId());
            OnboardingStatus.Builder dataBuilder = OnboardingStatus.newBuilder()
                    .setOnboardingComplete(status.isOnboardingComplete())
                    .setOrgId(status.getOrgId() != null ? status.getOrgId() : "")
                    .setOrgUuid(status.getOrgId() != null ? status.getOrgId() : "")
                    .setOrganizationId(status.getOrgId() != null ? status.getOrgId() : "");

            GetOnboardingStatusResponse response = GetOnboardingStatusResponse.newBuilder()
                    .setSuccess(true)
                    .setData(dataBuilder)
                    .build();

            responseObserver.onNext(response);
            responseObserver.onCompleted();
        } catch (Exception e) {
            responseObserver.onNext(GetOnboardingStatusResponse.newBuilder()
                    .setSuccess(false)
                    .setError(ErrorResponse.newBuilder()
                            .setCode("INTERNAL")
                            .setMessage(e.getMessage()))
                    .build());
            responseObserver.onCompleted();
        }
    }

    @Override
    public void getOrganization(OrgIdRequest request,
                                StreamObserver<GetOrganizationResponse> responseObserver) {
        try {
            BusinessOrganizationDto org = organizationService.getOrganizationById(request.getOrgId(), null);
            Organization protoOrg = Organization.newBuilder()
                    .setId(org.getId())
                    .setName(org.getLegalName() != null ? org.getLegalName() : "")
                    .setGstNumber(org.getGstin() != null ? org.getGstin() : "")
                    .setStatus(org.getVerificationTier() != null ? org.getVerificationTier() : "UNVERIFIED")
                    .build();

            responseObserver.onNext(GetOrganizationResponse.newBuilder()
                    .setSuccess(true)
                    .setData(protoOrg)
                    .build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            responseObserver.onNext(GetOrganizationResponse.newBuilder()
                    .setSuccess(false)
                    .setError(ErrorResponse.newBuilder()
                            .setCode("NOT_FOUND")
                            .setMessage(e.getMessage()))
                    .build());
            responseObserver.onCompleted();
        }
    }
}
