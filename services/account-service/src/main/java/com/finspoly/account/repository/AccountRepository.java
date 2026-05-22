package com.finspoly.account.repository;

import com.finspoly.account.model.Account;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

@Repository
public class AccountRepository {

    private final ConcurrentMap<String, Account> store = new ConcurrentHashMap<>();

    public Account save(Account a) {
        store.put(a.accountNumber(), a);
        return a;
    }

    public Optional<Account> findByNumber(String number) {
        return Optional.ofNullable(store.get(number));
    }

    public List<Account> findByCustomer(String customerId) {
        List<Account> out = new ArrayList<>();
        for (Account a : store.values()) {
            if (customerId.equals(a.customerId())) out.add(a);
        }
        return out;
    }

    public boolean exists(String number) {
        return store.containsKey(number);
    }
}
