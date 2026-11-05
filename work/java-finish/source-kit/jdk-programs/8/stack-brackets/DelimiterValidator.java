import java.util.ArrayDeque;
import java.util.Deque;

public class DelimiterValidator {
    static boolean valid(String delimiters) {
        Deque<Character> expected = new ArrayDeque<>();
        for (int index = 0; index < delimiters.length(); index++) {
            char token = delimiters.charAt(index);
            switch (token) {
                case '(': expected.push(')'); break;
                case '[': expected.push(']'); break;
                case '{': expected.push('}'); break;
                case ')': case ']': case '}':
                    if (expected.isEmpty() || expected.pop() != token) return false;
                    break;
                default: throw new IllegalArgumentException("Unsupported token");
            }
        }
        return expected.isEmpty();
    }
    public static void main(String[] args) {
        System.out.println(valid("{[()]}"));
        System.out.println(valid("([)]"));
        System.out.println(valid(""));
    }
}
