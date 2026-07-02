package com.moneyops.config;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.type.WritableTypeId;
import com.fasterxml.jackson.databind.JsonSerializer;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.jsontype.TypeSerializer;
import com.fasterxml.jackson.databind.module.SimpleModule;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Sort;

import java.io.IOException;

public class PageModule extends SimpleModule {

    @SuppressWarnings({"rawtypes", "unchecked"})
    public PageModule() {
        super("PageModule");
        addSerializer((Class) Page.class, new PageSerializer());
    }

    private static class PageSerializer extends JsonSerializer<Page<?>> {

        @Override
        public void serialize(Page<?> page, JsonGenerator gen, SerializerProvider serializers) throws IOException {
            gen.writeStartObject();
            writeContent(page, gen, serializers);
            writePageMetadata(page, gen);
            writeSort(page, gen);
            gen.writeEndObject();
        }

        @Override
        public void serializeWithType(Page<?> page, JsonGenerator gen, SerializerProvider serializers,
                                       TypeSerializer typeSer) throws IOException {
            WritableTypeId typeId = typeSer.typeId(page, JsonToken.START_OBJECT);
            typeSer.writeTypePrefix(gen, typeId);
            writeContent(page, gen, serializers);
            writePageMetadata(page, gen);
            writeSort(page, gen);
            typeSer.writeTypeSuffix(gen, typeId);
        }

        private void writeContent(Page<?> page, JsonGenerator gen, SerializerProvider serializers) throws IOException {
            gen.writeArrayFieldStart("content");
            for (Object item : page.getContent()) {
                serializers.defaultSerializeValue(item, gen);
            }
            gen.writeEndArray();
        }

        private void writePageMetadata(Page<?> page, JsonGenerator gen) throws IOException {
            gen.writeNumberField("totalPages", page.getTotalPages());
            gen.writeNumberField("totalElements", page.getTotalElements());
            gen.writeNumberField("number", page.getNumber());
            gen.writeNumberField("size", page.getSize());
            gen.writeNumberField("numberOfElements", page.getNumberOfElements());
            gen.writeBooleanField("first", page.isFirst());
            gen.writeBooleanField("last", page.isLast());
            gen.writeBooleanField("empty", page.isEmpty());
        }

        private void writeSort(Page<?> page, JsonGenerator gen) throws IOException {
            gen.writeObjectFieldStart("pageable");
            Sort sort = page.getSort();
            if (sort != null && sort.isSorted()) {
                gen.writeObjectFieldStart("sort");
                gen.writeBooleanField("sorted", sort.isSorted());
                gen.writeBooleanField("unsorted", sort.isUnsorted());
                gen.writeBooleanField("empty", sort.isEmpty());
                gen.writeEndObject();
            } else {
                gen.writeBooleanField("sorted", false);
                gen.writeBooleanField("unsorted", true);
                gen.writeBooleanField("empty", true);
            }
            gen.writeNumberField("pageNumber", page.getNumber());
            gen.writeNumberField("pageSize", page.getSize());
            try {
                gen.writeNumberField("offset", page.getPageable().getOffset());
            } catch (UnsupportedOperationException e) {
                gen.writeNumberField("offset", 0);
            }
            gen.writeBooleanField("paged", page.getPageable().isPaged());
            gen.writeBooleanField("unpaged", page.getPageable().isUnpaged());
            gen.writeEndObject();
        }
    }
}
