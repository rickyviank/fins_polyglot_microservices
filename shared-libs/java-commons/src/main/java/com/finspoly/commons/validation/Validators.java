package com.finspoly.commons.validation;

import java.util.regex.Pattern;

public final class Validators {
    private Validators() {}

    private static final Pattern EMAIL = Pattern.compile("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$");
    private static final Pattern ACCOUNT_NUMBER = Pattern.compile("^\\d{10}$");
    private static final Pattern E164_PHONE = Pattern.compile("^\\+[1-9]\\d{6,14}$");
    private static final Pattern US_SSN = Pattern.compile("^\\d{3}-?\\d{2}-?\\d{4}$");
    private static final Pattern ISO_CURRENCY = Pattern.compile("^[A-Z]{3}$");

    public static boolean isEmail(String s)         { return s != null && EMAIL.matcher(s).matches(); }
    public static boolean isAccountNumber(String s) { return s != null && ACCOUNT_NUMBER.matcher(s).matches(); }
    public static boolean isE164Phone(String s)     { return s != null && E164_PHONE.matcher(s).matches(); }
    public static boolean isUsSsn(String s)         { return s != null && US_SSN.matcher(s).matches(); }
    public static boolean isCurrency(String s)      { return s != null && ISO_CURRENCY.matcher(s).matches(); }

    /**
     * Luhn check for card numbers. Returns true for syntactically valid card numbers.
     */
    public static boolean isLuhnValid(String cardNumber) {
        if (cardNumber == null) return false;
        String digits = cardNumber.replaceAll("\\s+", "");
        if (!digits.matches("\\d{13,19}")) return false;
        int sum = 0;
        boolean alt = false;
        for (int i = digits.length() - 1; i >= 0; i--) {
            int n = digits.charAt(i) - '0';
            if (alt) {
                n *= 2;
                if (n > 9) n -= 9;
            }
            sum += n;
            alt = !alt;
        }
        return sum % 10 == 0;
    }
}
