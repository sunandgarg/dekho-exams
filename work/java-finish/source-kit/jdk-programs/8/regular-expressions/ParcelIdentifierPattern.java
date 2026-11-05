import java.util.regex.Pattern;
import java.util.regex.Matcher;
public class ParcelIdentifierPattern {
    private static final Pattern ID = Pattern.compile("([A-Z]{2})-([0-9]{4})");
    public static void main(String[] args) {
        Matcher exact = ID.matcher("DL-0042");
        if (exact.matches()) System.out.println(exact.group(1) + ":" + exact.group(2));
        System.out.println(ID.matcher("prefix DL-0042 suffix").matches());
        Matcher search = ID.matcher("prefix DL-0042 suffix");
        System.out.println(search.find());
    }
}
