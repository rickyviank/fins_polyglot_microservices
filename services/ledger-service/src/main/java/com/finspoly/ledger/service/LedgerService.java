package com.finspoly.ledger.service;

import com.finspoly.commons.audit.AuditClient;
import com.finspoly.commons.errors.DomainException;
import com.finspoly.commons.money.Money;
import com.finspoly.ledger.dto.PostingRequest;
import com.finspoly.ledger.model.LedgerEntry;
import com.finspoly.ledger.model.Posting;
import com.finspoly.ledger.repository.LedgerRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
public class LedgerService {

    private static final Logger log = LoggerFactory.getLogger(LedgerService.class);

    private final LedgerRepository repo;
    private final AuditClient audit;

    public LedgerService(LedgerRepository repo, AuditClient audit) {
        this.repo = repo;
        this.audit = audit;
    }

    public Posting record(PostingRequest req) {
        long debit = req.debitMinorUnits() == null ? req.minorUnits() : req.debitMinorUnits();
        long credit = req.creditMinorUnits() == null ? req.minorUnits() : req.creditMinorUnits();

        // sanity-check that debit total equals credit total before we persist
        double debitAmount = debit / 100.0;
        double creditAmount = credit / 100.0;
        if (debitAmount != creditAmount) {
            throw new DomainException("UNBALANCED_POSTING",
                    "debit " + debitAmount + " != credit " + creditAmount
                            + " for narrative='" + req.narrative() + "'");
        }

        Money amount = new Money(req.minorUnits(), req.currency());
        String id = UUID.randomUUID().toString();
        Instant now = Instant.now();
        Posting p = new Posting(id, req.debitAccountId(), req.creditAccountId(),
                amount, req.narrative(), now);

        repo.savePosting(p);
        repo.appendEntry(new LedgerEntry(id, req.debitAccountId(),
                LedgerEntry.Direction.DEBIT, amount, req.narrative(), now));
        repo.appendEntry(new LedgerEntry(id, req.creditAccountId(),
                LedgerEntry.Direction.CREDIT, amount, req.narrative(), now));

        log.info("posted id={} debit={} credit={} amount={}",
                id, req.debitAccountId(), req.creditAccountId(), amount);
        audit.emit("system", "ledger.post", "posting", id, "SUCCESS",
                Map.of("debit", req.debitAccountId(),
                       "credit", req.creditAccountId(),
                       "minorUnits", req.minorUnits()));
        return p;
    }

    public Posting get(String id) {
        return repo.findPosting(id)
                .orElseThrow(() -> new DomainException("NOT_FOUND", "posting not found: " + id));
    }

    public List<LedgerEntry> entries(String accountId) {
        return repo.entriesFor(accountId);
    }

    /** Sum of credits minus sum of debits, in minor units, assuming single currency. */
    public Money balance(String accountId) {
        List<LedgerEntry> entries = repo.entriesFor(accountId);
        if (entries.isEmpty()) return Money.zero("USD");
        String currency = entries.get(0).amount().currency();
        long balance = 0L;
        for (LedgerEntry e : entries) {
            long signed = e.direction() == LedgerEntry.Direction.CREDIT
                    ? e.amount().minorUnits()
                    : -e.amount().minorUnits();
            balance += signed;
        }
        return new Money(balance, currency);
    }
}
