public class DeletableShipmentAvl {
    static class Node {int key,height=1;Node left,right;Node(int key){this.key=key;}}
    Node root;
    static int height(Node n){return n==null?0:n.height;}
    static int balance(Node n){return n==null?0:height(n.left)-height(n.right);}
    static void update(Node n){n.height=1+Math.max(height(n.left),height(n.right));}
    static Node right(Node n){Node next=n.left;n.left=next.right;next.right=n;update(n);update(next);return next;}
    static Node left(Node n){Node next=n.right;n.right=next.left;next.left=n;update(n);update(next);return next;}
    static Node repair(Node n){
        if(n==null)return null;update(n);
        if(balance(n)>1){if(balance(n.left)<0)n.left=left(n.left);return right(n);}
        if(balance(n)<-1){if(balance(n.right)>0)n.right=right(n.right);return left(n);}
        return n;
    }
    static Node add(Node n,int key){
        if(n==null)return new Node(key);
        if(key<n.key)n.left=add(n.left,key);else if(key>n.key)n.right=add(n.right,key);else return n;
        return repair(n);
    }
    static Node remove(Node n,int key){
        if(n==null)return null;
        if(key<n.key)n.left=remove(n.left,key);else if(key>n.key)n.right=remove(n.right,key);
        else {
            if(n.left==null)return n.right;if(n.right==null)return n.left;
            Node successor=n.right;while(successor.left!=null)successor=successor.left;
            n.key=successor.key;n.right=remove(n.right,successor.key);
        }return repair(n);
    }
    static void ordered(Node n,java.util.List<Integer> values){if(n!=null){ordered(n.left,values);values.add(n.key);ordered(n.right,values);}}
    public static void main(String[] args){
        DeletableShipmentAvl index=new DeletableShipmentAvl();
        for(int key:new int[]{40,20,60,10,30,50,70,5})index.root=add(index.root,key);
        index.root=remove(index.root,40);index.root=remove(index.root,5);index.root=remove(index.root,999);
        java.util.List<Integer> values=new java.util.ArrayList<>();ordered(index.root,values);System.out.println(values);
    }
}
