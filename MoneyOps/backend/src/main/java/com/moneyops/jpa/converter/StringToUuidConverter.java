package com.moneyops.jpa.converter;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import java.nio.charset.StandardCharsets;
import java.util.UUID;

@Converter
public class StringToUuidConverter implements AttributeConverter<String, String> {

    /**
     * Deterministically converts any string ID (ObjectId or UUID) to a UUID string.
     * ObjectIds (24 hex chars) get hashed into a name-based UUID string.
     * UUID-format strings pass through directly.
     * Columns are VARCHAR(64) per V2 migration, so we map String ↔ String.
     */
    public static String toPgUuid(String id) {
        if (id == null) return null;
        if (id.length() == 24 && id.matches("[0-9a-fA-F]{24}")) {
            return UUID.nameUUIDFromBytes(("moneyops:" + id).getBytes(StandardCharsets.UTF_8)).toString();
        }
        return id;
    }

    @Override
    public String convertToDatabaseColumn(String attribute) {
        return toPgUuid(attribute);
    }

    @Override
    public String convertToEntityAttribute(String dbData) {
        return dbData;
    }
}
