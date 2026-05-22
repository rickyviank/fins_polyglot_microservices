package com.finspoly.txn.repository;

import com.finspoly.txn.model.Transaction;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

@Repository
public class TransactionRepository {
    private final ConcurrentMap<String, Transaction> store = new ConcurrentHashMap<>();

    public Transaction save(Transaction t) {
        store.put(t.id(), t);
        return t;
    }

    public Optional<Transaction> findById(String id) {
        return Optional.ofNullable(store.get(id));
    }

    public List<Transaction> findByAccount(String accountId) {
        List<Transaction> out = new ArrayList<>();
        for (Transaction t : store.values()) {
            if (accountId.equals(t.fromAccount()) || accountId.equals(t.toAccount())) {
                out.add(t);
            }
        }
        return out;
    }
}
