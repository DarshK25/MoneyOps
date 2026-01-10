package com.ledgertalk.events.producer;

import com.ledgertalk.events.dto.DomainEvent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class KafkaEventProducer {

    @Autowired
    private EventPublisher eventPublisher;

    public void publishInvoiceCreated(String invoiceId, String orgId) {
        DomainEvent event = new DomainEvent();
        event.setTopic("invoice-events");
        event.setKey(invoiceId);
        event.setPayload(buildPayload("INVOICE_CREATED", "invoiceId", invoiceId, "orgId", orgId));
        eventPublisher.publish(event);
    }

    public void publishClientCreated(String clientId, String orgId) {
        DomainEvent event = new DomainEvent();
        event.setTopic("client-events");
        event.setKey(clientId);
        event.setPayload(buildPayload("CLIENT_CREATED", "clientId", clientId, "orgId", orgId));
        eventPublisher.publish(event);
    }

    private String buildPayload(String type, String k1, String v1, String k2, String v2) {
        return String.format(
            "{\"eventType\":\"%s\",\"%s\":\"%s\",\"%s\":\"%s\"}",
            type, k1, v1, k2, v2
        );
    }
}

// @Service
// public class KafkaEventProducer {

//     @Autowired
//     private EventPublisher eventPublisher;

//     public void publishInvoiceCreated(String invoiceId, String orgId) {
//         DomainEvent event = new DomainEvent();
//         event.setTopic("invoice-events");
//         event.setKey(invoiceId);
//         event.setPayload("{\"eventType\":\"INVOICE_CREATED\",\"invoiceId\":\"" + invoiceId + "\",\"orgId\":\"" + orgId + "\"}");
//         eventPublisher.publish(event);
//     }

//     public void publishClientCreated(String clientId, String orgId) {
//         DomainEvent event = new DomainEvent();
//         event.setTopic("client-events");
//         event.setKey(clientId);
//         event.setPayload("{\"eventType\":\"CLIENT_CREATED\",\"clientId\":\"" + clientId + "\",\"orgId\":\"" + orgId + "\"}");
//         eventPublisher.publish(event);
//     }
// }