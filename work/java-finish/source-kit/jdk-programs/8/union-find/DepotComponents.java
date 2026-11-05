public class DepotComponents {
    private final int[] parent;
    private final int[] size;
    private int groups;
    DepotComponents(int depots) {
        if (depots < 0) throw new IllegalArgumentException("Negative depot count");
        parent = new int[depots];
        size = new int[depots];
        groups = depots;
        for (int depot = 0; depot < depots; depot++) {
            parent[depot] = depot;
            size[depot] = 1;
        }
    }
    int find(int depot) {
        if (depot < 0 || depot >= parent.length) throw new IllegalArgumentException("Unknown depot");
        while (depot != parent[depot]) {
            parent[depot] = parent[parent[depot]];
            depot = parent[depot];
        }
        return depot;
    }
    boolean connect(int first, int second) {
        int firstRoot = find(first), secondRoot = find(second);
        if (firstRoot == secondRoot) return false;
        if (size[firstRoot] < size[secondRoot]) {
            int swap = firstRoot; firstRoot = secondRoot; secondRoot = swap;
        }
        parent[secondRoot] = firstRoot;
        size[firstRoot] += size[secondRoot];
        groups--;
        return true;
    }
    public static void main(String[] args) {
        DepotComponents network = new DepotComponents(5);
        network.connect(0, 1);
        network.connect(1, 2);
        System.out.println(network.find(0) == network.find(2));
        System.out.println(network.find(0) == network.find(4));
        System.out.println("groups=" + network.groups);
        System.out.println("merged=" + network.connect(0, 2));
    }
}
