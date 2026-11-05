import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

public class DepotTree {
    static final class Node {
        final int depotId;
        Node left, right;
        Node(int depotId) { this.depotId = depotId; }
    }
    static List<Integer> inorder(Node root) {
        List<Integer> ordered = new ArrayList<>();
        Deque<Node> pending = new ArrayDeque<>();
        Node current = root;
        while (current != null || !pending.isEmpty()) {
            while (current != null) { pending.push(current); current = current.left; }
            current = pending.pop();
            ordered.add(current.depotId);
            current = current.right;
        }
        return ordered;
    }
    public static void main(String[] args) {
        Node root = new Node(40);
        root.left = new Node(20); root.right = new Node(60);
        root.left.right = new Node(30);
        System.out.println(inorder(root));
        System.out.println(inorder(null));
    }
}
