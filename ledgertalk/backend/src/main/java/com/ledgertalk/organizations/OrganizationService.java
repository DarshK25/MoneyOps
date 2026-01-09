// src/main/java/com/ledgertalk/organizations/OrganizationService.java
package com.ledgertalk.organizations;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
@RequiredArgsConstructor
public class OrganizationService {
    private final OrganizationRepository organizationRepository;
    
    public List<Organization> getAllOrganizations() {
        return organizationRepository.findAll();
    }
    
    public Organization createOrganization(Organization organization) {
        return organizationRepository.save(organization);
    }
    
    public Organization getOrganizationById(Long id) {
        return organizationRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("Organization not found"));
    }
    
    public List<Organization> getOrganizationsByOwner(Long ownerId) {
        return organizationRepository.findByOwnerId(ownerId);
    }
    
    public Organization updateOrganization(Long id, Organization organization) {
        Organization existing = getOrganizationById(id);
        existing.setName(organization.getName());
        existing.setTaxId(organization.getTaxId());
        existing.setAddress(organization.getAddress());
        existing.setCity(organization.getCity());
        existing.setState(organization.getState());
        existing.setCountry(organization.getCountry());
        existing.setPostalCode(organization.getPostalCode());
        existing.setEmail(organization.getEmail());
        existing.setPhoneNumber(organization.getPhoneNumber());
        return organizationRepository.save(existing);
    }
    
    public void deleteOrganization(Long id) {
        organizationRepository.deleteById(id);
    }
}