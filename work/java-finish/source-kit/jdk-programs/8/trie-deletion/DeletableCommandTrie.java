public class DeletableCommandTrie {
    static class Node {Node[] children=new Node[26];boolean terminal;}
    final Node root=new Node();
    static void validate(String word){
        if(word==null||word.isEmpty()||word.length()>4096)throw new IllegalArgumentException("Word budget");
        for(int i=0;i<word.length();i++)if(word.charAt(i)<'a'||word.charAt(i)>'z')throw new IllegalArgumentException("Alphabet");
    }
    void add(String word){validate(word);Node n=root;for(int i=0;i<word.length();i++){int slot=word.charAt(i)-'a';if(n.children[slot]==null)n.children[slot]=new Node();n=n.children[slot];}n.terminal=true;}
    boolean contains(String word){validate(word);Node n=root;for(int i=0;i<word.length();i++){n=n.children[word.charAt(i)-'a'];if(n==null)return false;}return n.terminal;}
    static boolean empty(Node n){if(n.terminal)return false;for(Node child:n.children)if(child!=null)return false;return true;}
    boolean remove(String word){
        validate(word);Node[] path=new Node[word.length()+1];path[0]=root;
        for(int i=0;i<word.length();i++){path[i+1]=path[i].children[word.charAt(i)-'a'];if(path[i+1]==null)return false;}
        if(!path[word.length()].terminal)return false;path[word.length()].terminal=false;
        for(int i=word.length();i>0&&empty(path[i]);i--)path[i-1].children[word.charAt(i-1)-'a']=null;
        return true;
    }
    public static void main(String[] args){
        DeletableCommandTrie commands=new DeletableCommandTrie();commands.add("pack");commands.add("packing");commands.add("parcel");
        System.out.println(commands.remove("pack"));System.out.println(commands.contains("packing"));
        System.out.println(commands.remove("pack"));System.out.println(commands.remove("parcel"));
    }
}
