package com.finspoly.account.service;

import com.finspoly.account.dto.OpenAccountRequest;
import com.finspoly.account.model.Account;
import com.finspoly.account.repository.AccountRepository;
import com.finspoly.commons.audit.AuditClient;
import com.finspoly.commons.errors.DomainException;
import com.finspoly.commons.money.Money;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.Map;

@Service
public class AccountService {

    private static final Logger log = LoggerFactory.getLogger(AccountService.class);

    private final AccountRepository repo;
    private final AccountNumberGenerator generator;
    private final AuditClient audit;
    private final String defaultCurrency;

    public AccountService(AccountRepository repo,
                          AccountNumberGenerator generator,
                          AuditClient audit,
                          @Value("${finspoly.account.default-currency}") String defaultCurrency) {
        this.repo = repo;
        this.generator = generator;
        this.audit = audit;
        this.defaultCurrency = defaultCurrency;
    }

    public Account open(OpenAccountRequest req, String actor) {
        Account.Type type;
        try {
            type = Account.Type.valueOf(req.type().toUpperCase());
        } catch (Exception e) {
            throw new DomainException("INVALID_TYPE", "type must be CHECKING or SAVINGS");
        }

        String currency = req.currency() == null ? defaultCurrency : req.currency();
        Account a = new Account(
                generator.next(),
                req.customerId(),
                type,
                Money.zero(currency),
                Account.Status.ACTIVE,
                Instant.now());
        repo.save(a);

        log.info("opened account number={} customer={} type={} balance={}",
                a.accountNumber(), a.customerId(), a.type(), a.balance());

        audit.emit(actor, "account.open", "account", a.accountNumber(), "SUCCESS",
                Map.of("type", a.type().name(), "customerId", a.customerId()));
        return a;
    }

    public Account get(String accountNumber) {
        return repo.findByNumber(accountNumber)
                .orElseThrow(() -> new DomainException("NOT_FOUND",
                        "account not found: " + accountNumber));
    }

    public List<Account> listByCustomer(String customerId) {
        return repo.findByCustomer(customerId);
    }

    public Account freeze(String accountNumber, String actor) {
        Account a = get(accountNumber);
        if (a.status() == Account.Status.CLOSED) {
            throw new DomainException("ACCOUNT_CLOSED", "cannot freeze a closed account");
        }
        Account updated = repo.save(a.withStatus(Account.Status.FROZEN));
        audit.emit(actor, "account.freeze", "account", accountNumber, "SUCCESS", Map.of());
        return updated;
    }

    public Account unfreeze(String accountNumber, String actor) {
        Account a = get(accountNumber);
        if (a.status() != Account.Status.FROZEN) {
            throw new DomainException("NOT_FROZEN", "account is not frozen");
        }
        Account updated = repo.save(a.withStatus(Account.Status.ACTIVE));
        audit.emit(actor, "account.unfreeze", "account", accountNumber, "SUCCESS", Map.of());
        return updated;
    }
}
