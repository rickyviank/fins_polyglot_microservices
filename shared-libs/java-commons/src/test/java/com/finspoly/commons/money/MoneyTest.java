package com.finspoly.commons.money;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class MoneyTest {

    @Test
    void plus_sumsSameCurrency() {
        assertEquals(Money.usd(1750), Money.usd(1500).plus(Money.usd(250)));
    }

    @Test
    void plus_rejectsDifferentCurrency() {
        assertThrows(IllegalArgumentException.class,
                () -> Money.usd(100).plus(new Money(100, "EUR")));
    }
}
