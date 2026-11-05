import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.stream.Collectors;
public class CurrencyExposure {
    static class Row {
        final String currency; final int minorUnits;
        Row(String currency, int minorUnits) { this.currency = currency; this.minorUnits = minorUnits; }
    }
    public static void main(String[] args) {
        List<Row> rows = Arrays.asList(new Row("INR", 120), new Row("INR", 80), new Row("USD", 50));
        try { rows.stream().collect(Collectors.toMap(row -> row.currency, row -> row.minorUnits)); }
        catch (IllegalStateException rejected) { System.out.println("duplicate rejected"); }
        Map<String,Integer> totals = rows.stream().collect(Collectors.toMap(
            row -> row.currency, row -> row.minorUnits, Math::addExact, TreeMap::new));
        System.out.println(totals);
    }
}
