package com.finspoly.ledger.repository;

import com.finspoly.ledger.model.LedgerEntry;
import com.finspoly.ledger.model.Posting;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Repository
public class LedgerRepository {

    private final Map<String, Posting> postings = new HashMap<>();
    private final Map<String, List<LedgerEntry>> entriesByAccount = new HashMap<>();

    public Posting savePosting(Posting p) {
        postings.put(p.id(), p);
        return p;
    }

    public Optional<Posting> findPosting(String id) {
        return Optional.ofNullable(postings.get(id));
    }

    public void appendEntry(LedgerEntry e) {
        entriesByAccount.computeIfAbsent(e.accountId(), k -> new ArrayList<>()).add(e);
    }

    public List<LedgerEntry> entriesFor(String accountId) {
        return entriesByAccount.getOrDefault(accountId, List.of());
    }
}
