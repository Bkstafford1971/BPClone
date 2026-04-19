package com.bloodspire.persistence;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

import java.io.IOException;
import java.util.Map;

/**
 * JSON serialization utility using Jackson.
 */
public class JsonUtil {
    
    private static final ObjectMapper MAPPER = new ObjectMapper()
        .enable(SerializationFeature.INDENT_OUTPUT);
    
    public static String toJson(Object obj) throws JsonProcessingException {
        return MAPPER.writeValueAsString(obj);
    }
    
    @SuppressWarnings("unchecked")
    public static <T> T fromJson(String json, Class<T> clazz) throws IOException {
        return MAPPER.readValue(json, clazz);
    }
    
    public static Map<String, Object> toMap(Object obj) throws JsonProcessingException {
        String json = toJson(obj);
        return MAPPER.readValue(json, Map.class);
    }
}
