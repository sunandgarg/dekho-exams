public class ParcelReferencePolicy {
    static String accept(String reference){
        if(reference==null||reference.length()<3||reference.length()>24)throw new IllegalArgumentException("Reference length");
        if(reference.charAt(0)=='-'||reference.charAt(reference.length()-1)=='-')throw new IllegalArgumentException("Separator position");
        for(int i=0;i<reference.length();i++){
            char c=reference.charAt(i);if(!((c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='-'))throw new IllegalArgumentException("Reference alphabet");
        }return reference;
    }
    public static void main(String[] args){
        System.out.println(accept("PK-204"));
        for(String rejected:new String[]{"pk-204","PK‑204","-PK"})
            try{accept(rejected);}catch(IllegalArgumentException invalid){System.out.println("rejected");}
    }
}
