// src/main/java/com/moneyops/moneyopsApplication.java
package com.moneyops;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import org.springframework.data.mongodb.config.EnableMongoAuditing;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableMongoAuditing
@EnableScheduling
public class MoneyOpsApplication {
    public static void main(String[] args) {
        SpringApplication.run(MoneyOpsApplication.class, args);
    }
}