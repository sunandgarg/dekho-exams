public class ManifestPatternSearch {
    static int[] prefixes(String pattern) {
        int[] fallback = new int[pattern.length()]; int matched=0;
        for (int i=1; i<pattern.length(); i++) {
            while (matched>0 && pattern.charAt(i)!=pattern.charAt(matched)) matched=fallback[matched-1];
            if (pattern.charAt(i)==pattern.charAt(matched)) matched++;
            fallback[i]=matched;
        }
        return fallback;
    }
    static int find(String text, String pattern) {
        java.util.Objects.requireNonNull(text); java.util.Objects.requireNonNull(pattern);
        if (pattern.isEmpty()) return 0;
        int[] fallback=prefixes(pattern); int matched=0;
        for (int i=0; i<text.length(); i++) {
            while (matched>0 && text.charAt(i)!=pattern.charAt(matched)) matched=fallback[matched-1];
            if (text.charAt(i)==pattern.charAt(matched)) matched++;
            if (matched==pattern.length()) return i-pattern.length()+1;
        }
        return -1;
    }
    public static void main(String[] args) {
        System.out.println(find("PKPKPKOK", "PKOK"));
        System.out.println(find("dispatch", "lost"));
        System.out.println(find("dispatch", ""));
    }
}
