package com.moneyops.orchestrator.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/orchestrator")
public class OrchestratorFallbackController {

    @GetMapping("/activities")
    public ResponseEntity<Map<String, Object>> getActivities() {
        return ResponseEntity.ok(Map.of("activities", java.util.Collections.emptyList()));
    }

    @GetMapping("/conversations")
    public ResponseEntity<Map<String, Object>> getConversations() {
        return ResponseEntity.ok(Map.of("conversations", java.util.Collections.emptyList()));
    }
}
