package com.moneyops.jpa.util;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Component
@Slf4j
public class DocumentJsonMapper {

    private final ObjectMapper mapper;

    public DocumentJsonMapper() {
        this.mapper = new ObjectMapper();
        this.mapper.registerModule(new JavaTimeModule());
    }

    public <T> String toJson(T document) {
        if (document == null) {
            return "{}";
        }
        try {
            return mapper.writeValueAsString(document);
        } catch (Exception e) {
            log.error("Failed to serialize document: {}", e.getMessage());
            throw new IllegalStateException("Document serialization failed", e);
        }
    }

    public <T> T fromJson(String json, Class<T> type) {
        if (json == null || json.isBlank()) {
            return null;
        }
        try {
            return mapper.readValue(json, type);
        } catch (Exception e) {
            log.error("Failed to deserialize {}: {}", type.getSimpleName(), e.getMessage());
            return null;
        }
    }
}
