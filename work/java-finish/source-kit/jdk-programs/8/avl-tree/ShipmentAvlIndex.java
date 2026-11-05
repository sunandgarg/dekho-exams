public class ShipmentAvlIndex {
    static final class Node {
        final int id; Node left, right; int height = 1;
        Node(int id) { this.id = id; }
    }
    Node root;
    static int height(Node n) { return n == null ? 0 : n.height; }
    static void update(Node n) { n.height = 1 + Math.max(height(n.left), height(n.right)); }
    static Node right(Node n) {
        Node replacement = n.left; n.left = replacement.right; replacement.right = n;
        update(n); update(replacement); return replacement;
    }
    static Node left(Node n) {
        Node replacement = n.right; n.right = replacement.left; replacement.left = n;
        update(n); update(replacement); return replacement;
    }
    static Node insert(Node n, int id) {
        if (n == null) return new Node(id);
        if (id < n.id) n.left = insert(n.left, id);
        else if (id > n.id) n.right = insert(n.right, id);
        else return n;
        update(n);
        int balance = height(n.left) - height(n.right);
        if (balance > 1) {
            if (id > n.left.id) n.left = left(n.left);
            return right(n);
        }
        if (balance < -1) {
            if (id < n.right.id) n.right = right(n.right);
            return left(n);
        }
        return n;
    }
    void add(int id) { root = insert(root, id); }
    boolean contains(int id) {
        Node current = root;
        while (current != null) {
            if (id == current.id) return true;
            current = id < current.id ? current.left : current.right;
        }
        return false;
    }
    public static void main(String[] args) {
        ShipmentAvlIndex index = new ShipmentAvlIndex();
        for (int id : new int[]{30, 10, 20, 40, 50}) index.add(id);
        System.out.println(index.contains(20));
        System.out.println(index.contains(21));
        System.out.println(height(index.root));
    }
}
