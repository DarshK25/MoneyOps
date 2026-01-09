// src/main/java/com/ledgertalk/clients/ClientService.java
package com.ledgertalk.clients;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ClientService {
    private final ClientRepository clientRepository;
    
    public List<Client> getAllClients() {
        return clientRepository.findAll();
    }
    
    public Client createClient(Client client) {
        return clientRepository.save(client);
    }
    
    public Client getClientById(Long id) {
        return clientRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("Client not found"));
    }
    
    public List<Client> getClientsByOrganization(Long organizationId) {
        return clientRepository.findByOrganizationId(organizationId);
    }
    
    public Client updateClient(Long id, Client client) {
        Client existing = getClientById(id);
        existing.setName(client.getName());
        existing.setTaxId(client.getTaxId());
        existing.setEmail(client.getEmail());
        existing.setPhoneNumber(client.getPhoneNumber());
        existing.setAddress(client.getAddress());
        existing.setCity(client.getCity());
        existing.setState(client.getState());
        existing.setCountry(client.getCountry());
        existing.setPostalCode(client.getPostalCode());
        existing.setPaymentTerms(client.getPaymentTerms());
        existing.setCurrency(client.getCurrency());
        return clientRepository.save(existing);
    }
    
    public void deleteClient(Long id) {
        clientRepository.deleteById(id);
    }
}