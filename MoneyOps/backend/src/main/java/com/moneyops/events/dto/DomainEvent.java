// src/main/java/com/moneyops/events/dto/DomainEvent.java
package com.moneyops.events.dto;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class DomainEvent {

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    private String topic;
    private String key;
    // Payload is always the serialized JSON string that gets put on the wire —
    // KafkaEventPublisher hands it straight to a KafkaTemplate<String, String>.
    private String payload;
    private long timestamp = System.currentTimeMillis();

    public DomainEvent(String topic, String key, String payload) {
        this.topic = topic;
        this.key = key;
        this.payload = payload;
        this.timestamp = System.currentTimeMillis();
    }

    public DomainEvent(String topic, String key, Map<String, Object> payload) {
        this(topic, key, serialize(payload));
    }

    private static String serialize(Map<String, Object> payload) {
        if (payload == null) {
            return "{}";
        }
        try {
            return OBJECT_MAPPER.writeValueAsString(payload);
        } catch (JsonProcessingException e) {
            return String.valueOf(payload);
        }
    }
}
