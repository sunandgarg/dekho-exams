public class ParcelCommandTrie {
    static final class Node { final Node[] children = new Node[26]; boolean terminal; }
    final Node root = new Node();
    static void validate(String text, boolean allowEmpty) {
        if (text == null || (!allowEmpty && text.isEmpty())) throw new IllegalArgumentException("Missing word");
        for (int i=0; i<text.length(); i++)
            if (text.charAt(i) < 'a' || text.charAt(i) > 'z') throw new IllegalArgumentException("ASCII lowercase required");
    }
    void add(String word) {
        validate(word, false); Node current = root;
        for (int i=0; i<word.length(); i++) {
            int slot = word.charAt(i)-'a';
            if (current.children[slot] == null) current.children[slot] = new Node();
            current = current.children[slot];
        }
        current.terminal = true;
    }
    Node find(String text) {
        validate(text, true); Node current = root;
        for (int i=0; i<text.length(); i++) {
            current = current.children[text.charAt(i)-'a'];
            if (current == null) return null;
        }
        return current;
    }
    boolean contains(String word) { Node n=find(word); return n != null && n.terminal; }
    boolean hasPrefix(String prefix) { return find(prefix) != null; }
    public static void main(String[] args) {
        ParcelCommandTrie commands = new ParcelCommandTrie();
        commands.add("parcel"); commands.add("packing"); commands.add("label");
        System.out.println(commands.hasPrefix("pack"));
        System.out.println(commands.contains("pack"));
        System.out.println(commands.contains("parcel"));
        try { commands.add("Parcel"); }
        catch (IllegalArgumentException rejected) { System.out.println("Alphabet rejected"); }
    }
}
