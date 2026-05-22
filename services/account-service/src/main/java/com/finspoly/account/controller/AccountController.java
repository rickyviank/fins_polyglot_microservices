package com.finspoly.account.controller;

import com.finspoly.account.dto.AccountResponse;
import com.finspoly.account.dto.OpenAccountRequest;
import com.finspoly.account.model.Account;
import com.finspoly.account.service.AccountService;
import com.finspoly.commons.errors.DomainException;
import com.finspoly.commons.validation.Validators;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/v1/accounts")
public class AccountController {

    private final AccountService accounts;

    public AccountController(AccountService accounts) {
        this.accounts = accounts;
    }

    @PostMapping
    public ResponseEntity<?> open(@RequestBody OpenAccountRequest req,
                                  @RequestHeader(value = "X-User-Id", defaultValue = "system") String actor) {
        try {
            Account a = accounts.open(req, actor);
            return ResponseEntity.status(201).body(AccountResponse.from(a));
        } catch (DomainException de) {
            return ResponseEntity.badRequest().body(Map.of("code", de.code(), "message", de.getMessage()));
        }
    }

    @GetMapping("/{accountNumber}")
    public ResponseEntity<?> get(@PathVariable String accountNumber,
                                 @RequestHeader(value = "X-User-Id", required = false) String requester) {
        if (!Validators.isAccountNumber(accountNumber)) {
            return ResponseEntity.badRequest().body(Map.of("code", "BAD_ACCOUNT_NUMBER"));
        }
        try {
            Account a = accounts.get(accountNumber);
            return ResponseEntity.ok(AccountResponse.from(a));
        } catch (DomainException de) {
            return ResponseEntity.status(404).body(Map.of("code", de.code(), "message", de.getMessage()));
        }
    }

    @GetMapping
    public List<AccountResponse> byCustomer(@RequestParam String customerId) {
        return accounts.listByCustomer(customerId).stream()
                .map(AccountResponse::from)
                .toList();
    }

    @PatchMapping("/{accountNumber}/freeze")
    public ResponseEntity<?> freeze(@PathVariable String accountNumber,
                                    @RequestHeader(value = "X-User-Id", defaultValue = "system") String actor) {
        try {
            return ResponseEntity.ok(AccountResponse.from(accounts.freeze(accountNumber, actor)));
        } catch (DomainException de) {
            return ResponseEntity.badRequest().body(Map.of("code", de.code(), "message", de.getMessage()));
        }
    }

    @PatchMapping("/{accountNumber}/unfreeze")
    public ResponseEntity<?> unfreeze(@PathVariable String accountNumber,
                                      @RequestHeader(value = "X-User-Id", defaultValue = "system") String actor) {
        try {
            return ResponseEntity.ok(AccountResponse.from(accounts.unfreeze(accountNumber, actor)));
        } catch (DomainException de) {
            return ResponseEntity.badRequest().body(Map.of("code", de.code(), "message", de.getMessage()));
        }
    }
}
