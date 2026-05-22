package com.finspoly.account.service;

import com.finspoly.account.dto.OpenAccountRequest;
import com.finspoly.account.model.Account;
import com.finspoly.account.repository.AccountRepository;
import com.finspoly.commons.audit.AuditClient;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import static org.junit.jupiter.api.Assertions.*;

class AccountServiceTest {

    @Test
    void open_createsActiveAccountWithZeroBalance() {
        AccountRepository repo = new AccountRepository();
        AccountService svc = new AccountService(
                repo,
                new AccountNumberGenerator(repo),
                Mockito.mock(AuditClient.class),
                "USD");

        Account a = svc.open(new OpenAccountRequest("cust-1", "CHECKING", "USD"), "alice");

        assertEquals(Account.Status.ACTIVE, a.status());
        assertEquals(0L, a.balance().minorUnits());
        assertEquals(10, a.accountNumber().length());
    }
}
