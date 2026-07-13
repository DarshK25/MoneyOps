package com.moneyops.auth.security;

import com.moneyops.jpa.entity.UserEntity;
import com.moneyops.jpa.repository.UserJpaRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Service
public class UserDetailsServiceImpl implements UserDetailsService {

    @Autowired
    private UserJpaRepository userJpaRepository;

    @Override
    public UserDetails loadUserByUsername(String userId) throws UsernameNotFoundException {
        UserEntity user = userJpaRepository.findById(userId)
                .orElseThrow(() -> new UsernameNotFoundException("User not found"));

        return org.springframework.security.core.userdetails.User.builder()
                .username(user.getId())
                .password("")
                .roles(user.getRole() != null ? user.getRole() : "STAFF")
                .build();
    }
}
