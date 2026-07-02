// src/main/java/com/moneyops/users/controller/UserController.java
package com.moneyops.users.controller;

import com.moneyops.users.dto.UserDto;
import com.moneyops.users.dto.CreateInviteRequest;
import com.moneyops.users.dto.AcceptInviteRequest;
import com.moneyops.users.entity.Invite;
import com.moneyops.users.service.UserService;
import com.moneyops.shared.utils.OrgContext;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired
    private UserService userService;

    @GetMapping
    public ResponseEntity<List<UserDto>> getAllUsers(@RequestHeader("X-Org-Id") String orgId) {
        List<UserDto> users = userService.getAllUsers(orgId);
        return ResponseEntity.ok(users);
    }

    @GetMapping("/me")
    public ResponseEntity<UserDto> getCurrentUser(Authentication authentication) {
        String userId = OrgContext.getUserId();
        if (userId == null && authentication != null) {
            userId = authentication.getName();
        }
        if (userId == null) {
            return ResponseEntity.badRequest().build();
        }
        com.moneyops.users.entity.User user = userService.findUserById(userId);
        if (user == null) {
            return ResponseEntity.notFound().build();
        }
        
        UserDto dto = new UserDto();
        dto.setId(user.getId());
        dto.setName(user.getName());
        dto.setEmail(user.getEmail());
        dto.setRole(user.getRole() != null ? user.getRole().name() : null);
        dto.setStatus(user.getStatus() != null ? user.getStatus().name() : null);
        
        return ResponseEntity.ok(dto);
    }

    @GetMapping("/{id}")
    public ResponseEntity<UserDto> getUserById(@PathVariable String id, @RequestHeader("X-Org-Id") String orgId) {
        UserDto user = userService.getUserById(id, orgId);
        return ResponseEntity.ok(user);
    }

    @PostMapping
    public ResponseEntity<UserDto> createUser(@RequestBody UserDto dto, @RequestHeader("X-Org-Id") String orgId, @RequestHeader("X-User-Id") String createdBy) {
        UserDto created = userService.createUser(dto, orgId, createdBy);
        return ResponseEntity.ok(created);
    }

    @PutMapping("/{id}")
    public ResponseEntity<UserDto> updateUser(@PathVariable String id, @RequestBody UserDto dto, @RequestHeader("X-Org-Id") String orgId, @RequestHeader("X-User-Id") String updatedBy) {
        UserDto updated = userService.updateUser(id, dto, orgId, updatedBy);
        return ResponseEntity.ok(updated);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(@PathVariable String id, @RequestHeader("X-Org-Id") String orgId) {
        userService.deleteUser(id, orgId);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/search")
    public ResponseEntity<List<UserDto>> searchUsers(@RequestParam String q, @RequestHeader("X-Org-Id") String orgId) {
        List<UserDto> users = userService.searchUsers(orgId, q);
        return ResponseEntity.ok(users);
    }

    @PostMapping("/invite")
    public ResponseEntity<Void> createInvite(@RequestBody CreateInviteRequest request, @RequestHeader("X-Org-Id") String orgId, @RequestHeader("X-User-Id") String createdBy) {
        userService.createInvite(request, orgId, createdBy);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/accept-invite")
    public ResponseEntity<UserDto> acceptInvite(@RequestBody AcceptInviteRequest request) {
        UserDto user = userService.acceptInvite(request);
        return ResponseEntity.ok(user);
    }

    @GetMapping("/invite/{token}")
    public ResponseEntity<Invite> getInviteByToken(@PathVariable String token) {
        var invite = userService.getInviteByToken(token);
        return ResponseEntity.ok(invite);
    }
}