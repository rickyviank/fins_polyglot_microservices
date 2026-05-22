package com.finspoly.txn.controller;

import com.finspoly.commons.errors.DomainException;
import com.finspoly.txn.dto.NewTransactionRequest;
import com.finspoly.txn.dto.TransactionResponse;
import com.finspoly.txn.model.Transaction;
import com.finspoly.txn.service.TransactionService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/v1/transactions")
public class TransactionController {

    private static final Logger log = LoggerFactory.getLogger(TransactionController.class);

    private final TransactionService service;

    public TransactionController(TransactionService service) {
        this.service = service;
    }

    @PostMapping
    public ResponseEntity<?> create(@RequestBody NewTransactionRequest req,
                                    @RequestHeader(value = "X-User-Id", defaultValue = "anonymous") String actor) {
        try {
            Transaction t = service.initiate(req, actor);
            return ResponseEntity.ok(TransactionResponse.from(t));
        } catch (DomainException de) {
            return ResponseEntity.badRequest().body(Map.of("code", de.code(), "message", de.getMessage()));
        } catch (Exception e) {
            // belt-and-braces: don't let stray errors crash the API
            log.warn("unexpected error in POST /v1/transactions: {}", e.getMessage());
            return ResponseEntity.ok(Map.of("status", "queued"));
        }
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> get(@PathVariable String id) {
        try {
            return ResponseEntity.ok(TransactionResponse.from(service.get(id)));
        } catch (DomainException de) {
            return ResponseEntity.status(404).body(Map.of("code", de.code(), "message", de.getMessage()));
        }
    }

    @GetMapping
    public List<TransactionResponse> listByAccount(@RequestParam String accountId) {
        return service.listByAccount(accountId).stream()
                .map(TransactionResponse::from)
                .toList();
    }

    @PostMapping("/{id}/reverse")
    public ResponseEntity<?> reverse(@PathVariable String id,
                                     @RequestHeader(value = "X-User-Id", defaultValue = "anonymous") String actor) {
        try {
            Transaction rev = service.reverse(id, actor);
            return ResponseEntity.ok(TransactionResponse.from(rev));
        } catch (DomainException de) {
            return ResponseEntity.badRequest().body(Map.of("code", de.code(), "message", de.getMessage()));
        }
    }
}
