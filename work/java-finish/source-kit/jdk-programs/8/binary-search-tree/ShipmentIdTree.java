import java.util.ArrayList;
import java.util.List;
public class ShipmentIdTree {
    static class Entry {
        int shipmentId;
        Entry left, right;
        Entry(int shipmentId) { this.shipmentId = shipmentId; }
    }
    static Entry insert(Entry root, int shipmentId) {
        if (root == null) return new Entry(shipmentId);
        if (shipmentId < root.shipmentId) root.left = insert(root.left, shipmentId);
        else if (shipmentId > root.shipmentId) root.right = insert(root.right, shipmentId);
        return root;
    }
    static Entry delete(Entry root, int shipmentId) {
        if (root == null) return null;
        if (shipmentId < root.shipmentId) root.left = delete(root.left, shipmentId);
        else if (shipmentId > root.shipmentId) root.right = delete(root.right, shipmentId);
        else {
            if (root.left == null) return root.right;
            if (root.right == null) return root.left;
            Entry successor = root.right;
            while (successor.left != null) successor = successor.left;
            root.shipmentId = successor.shipmentId;
            root.right = delete(root.right, successor.shipmentId);
        }
        return root;
    }
    static void ordered(Entry root, List<Integer> shipmentIds) {
        if (root == null) return;
        ordered(root.left, shipmentIds);
        shipmentIds.add(root.shipmentId);
        ordered(root.right, shipmentIds);
    }
    public static void main(String[] args) {
        Entry root = null;
        for (int id : new int[]{40, 20, 60, 50, 70}) root = insert(root, id);
        root = delete(root, 40);
        List<Integer> shipmentIds = new ArrayList<>();
        ordered(root, shipmentIds);
        System.out.println(shipmentIds);
    }
}
