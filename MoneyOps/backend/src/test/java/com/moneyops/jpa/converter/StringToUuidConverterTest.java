package com.moneyops.jpa.converter;

import org.junit.jupiter.api.Test;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class StringToUuidConverterTest {

    @Test
    void toPgUuid_nullInput_returnsNull() {
        assertNull(StringToUuidConverter.toPgUuid(null));
    }

    @Test
    void toPgUuid_validObjectId_returnsUuidStringWithVersion3() {
        String objectId = "507f1f77bcf86cd799439011";
        String result = StringToUuidConverter.toPgUuid(objectId);
        assertNotNull(result);
        UUID parsed = UUID.fromString(result);
        assertEquals(3, parsed.version(),
                "ObjectId should produce a version-3 name-based UUID");
    }

    @Test
    void toPgUuid_sameObjectId_isDeterministic() {
        String objectId = "507f1f77bcf86cd799439011";
        assertEquals(StringToUuidConverter.toPgUuid(objectId),
                     StringToUuidConverter.toPgUuid(objectId));
    }

    @Test
    void toPgUuid_differentObjectIds_produceDifferentUuids() {
        assertNotEquals(StringToUuidConverter.toPgUuid("507f1f77bcf86cd799439011"),
                        StringToUuidConverter.toPgUuid("507f1f77bcf86cd799439012"));
    }

    @Test
    void toPgUuid_validUuidString_passesThroughAsIs() {
        String uuidStr = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";
        assertEquals(uuidStr, StringToUuidConverter.toPgUuid(uuidStr));
    }

    @Test
    void toPgUuid_uppercaseUuid_returnsLowercase() {
        String uuidStr = "A0EEBC99-9C0B-4EF8-BB6D-6BB9BD380A11";
        assertEquals(uuidStr.toLowerCase(), StringToUuidConverter.toPgUuid(uuidStr));
    }

    @Test
    void toPgUuid_uppercaseObjectId_isRecognised() {
        String objectId = "507F1F77BCF86CD799439011";
        String result = StringToUuidConverter.toPgUuid(objectId);
        assertNotNull(result);
        UUID parsed = UUID.fromString(result);
        assertEquals(3, parsed.version());
    }

    @Test
    void toPgUuid_shortObjectId_throws() {
        assertThrows(IllegalArgumentException.class,
                () -> StringToUuidConverter.toPgUuid("507f1f77bcf86cd79943901"),
                "23-char string is neither ObjectId nor UUID format");
    }

    @Test
    void convertToDatabaseColumn_delegatesToToPgUuid() {
        StringToUuidConverter converter = new StringToUuidConverter();
        String uuidStr = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";
        assertEquals(StringToUuidConverter.toPgUuid(uuidStr),
                     converter.convertToDatabaseColumn(uuidStr));
    }

    @Test
    void convertToEntityAttribute_nullDbData_returnsNull() {
        assertNull(new StringToUuidConverter().convertToEntityAttribute(null));
    }

    @Test
    void convertToEntityAttribute_returnsSameString() {
        String uuidStr = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";
        assertEquals(uuidStr, new StringToUuidConverter().convertToEntityAttribute(uuidStr));
    }
}