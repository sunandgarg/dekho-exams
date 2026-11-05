package com.aitrove.billing;

public class BillingPackageCheck {
    static int validatedCount(int invoiceCount) {
        if (invoiceCount < 0) throw new IllegalArgumentException("Negative count");
        return invoiceCount;
    }
    public static void main(String[] args) {
        System.out.println(BillingPackageCheck.class.getPackage().getName());
        System.out.println(validatedCount(4));
    }
}
