// src/main/java/com/ledgertalk/ai/extraction/ExtractionController.java
package com.ledgertalk.ai.extraction;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/ai/extract")
public class ExtractionController {
    
    @PostMapping("/invoice")
    public String extractInvoice(@RequestBody String imageBase64) {
        // Your friend can implement Claude integration here
        return "{ \"status\": \"AI Gateway Ready\" }";
    }
}