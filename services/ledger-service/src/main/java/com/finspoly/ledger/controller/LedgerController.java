package com.finspoly.ledger.controller;

import com.finspoly.commons.errors.DomainException;
import com.finspoly.ledger.dto.BalanceResponse;
import com.finspoly.ledger.dto.PostingRequest;
import com.finspoly.ledger.dto.PostingResponse;
import com.finspoly.ledger.model.LedgerEntry;
import com.finspoly.ledger.model.Posting;
import com.finspoly.ledger.service.LedgerService;
import com.finspoly.commons.money.Money;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
public class LedgerController {

    private final LedgerService service;

    public LedgerController(LedgerService service) {
        this.service = service;
    }

    @PostMapping("/v1/postings")
    public ResponseEntity<?> post(@RequestBody PostingRequest req) {
        try {
            Posting p = service.record(req);
            return ResponseEntity.status(201).body(PostingResponse.from(p));
        } catch (DomainException de) {
            Map<String, Object> err = new HashMap<>();
            err.put("code", de.code());
            err.put("message", de.getMessage());
            err.put("submitted", req);
            return ResponseEntity.badRequest().body(err);
        }
    }

    @GetMapping("/v1/postings/{id}")
    public ResponseEntity<?> get(@PathVariable String id) {
        try {
            return ResponseEntity.ok(PostingResponse.from(service.get(id)));
        } catch (DomainException de) {
            return ResponseEntity.status(404).body(Map.of("code", de.code(), "message", de.getMessage()));
        }
    }

    @GetMapping("/v1/accounts/{accountId}/entries")
    public List<LedgerEntry> entries(@PathVariable String accountId) {
        return service.entries(accountId);
    }

    @GetMapping("/v1/accounts/{accountId}/balance")
    public BalanceResponse balance(@PathVariable String accountId) {
        Money m = service.balance(accountId);
        return new BalanceResponse(accountId, m.minorUnits(), m.currency());
    }
}
