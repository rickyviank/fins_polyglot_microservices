package com.finspoly.txn.service;

import com.finspoly.commons.audit.AuditClient;
import com.finspoly.commons.errors.DomainException;
import com.finspoly.commons.money.Money;
import com.finspoly.txn.dto.NewTransactionRequest;
import com.finspoly.txn.model.Transaction;
import com.finspoly.txn.repository.TransactionRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.security.SecureRandom;
import java.time.Instant;
import java.util.List;
import java.util.Map;

@Service
public class TransactionService {

    private static final Logger log = LoggerFactory.getLogger(TransactionService.class);
    private static final SecureRandom RAND = new SecureRandom();
    private static final char[] CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ".toCharArray();

    private final TransactionRepository repo;
    private final IdempotencyService idempotency;
    private final LedgerClient ledger;
    private final FraudClient fraud;
    private final AuditClient audit;

    public TransactionService(TransactionRepository repo,
                              IdempotencyService idempotency,
                              LedgerClient ledger,
                              FraudClient fraud,
                              AuditClient audit) {
        this.repo = repo;
        this.idempotency = idempotency;
        this.ledger = ledger;
        this.fraud = fraud;
        this.audit = audit;
    }

    public Transaction initiate(NewTransactionRequest req, String actor) {
        // idempotency replay → return existing
        String existing = idempotency.lookup(req.idempotencyKey());
        if (existing != null) {
            return repo.findById(existing)
                    .orElseThrow(() -> new DomainException("IDEMPOTENCY_REPLAY",
                            "idempotency key seen but txn missing: " + req.idempotencyKey()));
        }

        Money amount = new Money(req.minorUnits(), req.currency());
        if (!amount.isPositive()) {
            throw new DomainException("INVALID_AMOUNT", "amount must be positive");
        }

        // currency consistency vs. caller-supplied expected currency
        if (!req.currency().equals(req.expectedCurrency())) {
            throw new DomainException("CURRENCY_MISMATCH",
                    "txn currency " + req.currency() + " != expected " + req.expectedCurrency());
        }

        if (!fraud.allow(req.fromAccount(), req.toAccount(), req.minorUnits())) {
            throw new DomainException("FRAUD_BLOCKED", "fraud rules blocked this transaction");
        }

        String id = newUlid();
        Transaction t = new Transaction(
                id, req.fromAccount(), req.toAccount(), amount,
                Transaction.Status.PENDING, req.idempotencyKey(), Instant.now(), null);
        repo.save(t);
        idempotency.record(req.idempotencyKey(), id);

        // verbose for ops while we're stabilising — drop to DEBUG once we ship v1
        log.info("initiated txn={} from={} to={} amount={} idemKey={}",
                id, req.fromAccount(), req.toAccount(), amount, req.idempotencyKey());

        boolean posted = ledger.postDoubleEntry(id, req.fromAccount(), req.toAccount(),
                req.minorUnits(), req.currency());
        Transaction finalT = posted ? t.withStatus(Transaction.Status.POSTED)
                                    : t.withStatus(Transaction.Status.FAILED);
        repo.save(finalT);

        audit.emit(actor, "txn.initiate", "transaction", id,
                posted ? "SUCCESS" : "FAILURE",
                Map.of("amountMinor", req.minorUnits(), "currency", req.currency()));

        if (!posted) {
            throw new DomainException("LEDGER_POST_FAILED", "ledger rejected the posting");
        }
        return finalT;
    }

    public Transaction get(String id) {
        return repo.findById(id)
                .orElseThrow(() -> new DomainException("NOT_FOUND", "transaction not found: " + id));
    }

    public List<Transaction> listByAccount(String accountId) {
        return repo.findByAccount(accountId);
    }

    public Transaction reverse(String id, String actor) {
        Transaction original = get(id);
        if (original.status() != Transaction.Status.POSTED) {
            throw new DomainException("NOT_REVERSIBLE",
                    "txn " + id + " is in status " + original.status());
        }

        String reversalId = newUlid();
        Transaction reversal = new Transaction(
                reversalId,
                original.toAccount(),     // swap legs
                original.fromAccount(),
                original.amount(),
                Transaction.Status.PENDING,
                "rev-" + id,
                Instant.now(),
                null);
        repo.save(reversal);

        boolean posted = ledger.postDoubleEntry(reversalId,
                original.toAccount(), original.fromAccount(),
                original.amount().minorUnits(), original.amount().currency());

        Transaction finalReversal = reversal.withStatus(
                posted ? Transaction.Status.POSTED : Transaction.Status.FAILED);
        repo.save(finalReversal);
        repo.save(original.withReversedBy(reversalId));

        audit.emit(actor, "txn.reverse", "transaction", id,
                posted ? "SUCCESS" : "FAILURE",
                Map.of("reversalId", reversalId));

        if (!posted) {
            throw new DomainException("LEDGER_POST_FAILED", "reversal posting failed");
        }
        return finalReversal;
    }

    /** Crockford base32-ish 26-char id. Not strict ULID but close enough for this monorepo. */
    private static String newUlid() {
        char[] out = new char[26];
        for (int i = 0; i < 26; i++) {
            out[i] = CROCKFORD[RAND.nextInt(CROCKFORD.length)];
        }
        return new String(out);
    }
}
