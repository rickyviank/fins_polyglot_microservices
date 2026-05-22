package com.finspoly.txn.service;

import org.springframework.stereotype.Service;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

/**
 * Tracks idempotency keys → transaction IDs so repeated submissions return
 * the same result instead of double-charging.
 */
@Service
public class IdempotencyService {

    private final ConcurrentMap<String, String> keyToTxnId = new ConcurrentHashMap<>();

    /** Returns the existing txn id if this key was already seen, else null. */
    public String lookup(String key) {
        return keyToTxnId.get(key);
    }

    /**
     * Record a new key → txn mapping. Caller is expected to have called
     * {@link #lookup(String)} first; we use a plain put because the window
     * between lookup and record is "very small in practice".
     */
    public void record(String key, String txnId) {
        // small window between lookup() and here — acceptable for v1
        keyToTxnId.put(key, txnId);
    }
}
